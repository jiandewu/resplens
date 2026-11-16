"""LoRA training for B2 (plan: docs/finetune-eval.md, "Training" and the 2026-11-13 implementation details).

Runs in its own environment (torch, transformers, peft), not the project's:

    T=~/.local/share/resplens/train/bin/python
    PYTHONPATH=src $T -m resplens.finetune.train stats                  # token lengths and loss tokens
    PYTHONPATH=src ~/.local/share/resplens/vllm/bin/python -m resplens.finetune.train roundtrip   # vLLM's parser
    PYTHONPATH=src $T -m resplens.finetune.train fit --rank 16 --lr 2e-4 # 3 epochs, a merged model per epoch

Each conversation is rendered with the student's own chat template, the same one vLLM uses when serving. The
template renders every prefix of a conversation as a prefix of the whole, so the text each message adds is known.
Loss is on what the model writes: the text an assistant message adds, without the `<|turn>model` header (the server
adds it). That text ends with a stop token: `<|tool_response>` after tool calls, `<turn|>` after the answer.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "eval" / "finetune" / "train.jsonl"
RUNS = ROOT / "eval" / "finetune" / "training"
BASE = "google/gemma-4-E4B-it"
REVISION = "4ecc2ba63bcac23ba4a767fc87025b1450f84c9c"
HEADER = "<|turn>model\n"
TOOL_RESPONSE = "<|tool_response>"  # ends a tool-call turn; one of the model's stop tokens
END = "<turn|>"
# Attention and MLP projections of the language model; not the vision or audio towers, not the per-layer
# embedding projections. Gemma 4 E4B: 42 layers, k/v only in the first 24 (KV sharing): 258 modules.
TARGET = r"model\.language_model\.layers\.\d+\.(self_attn\.(q|k|v|o)_proj|mlp\.(gate|up|down)_proj)"


def examples(path: Path = DATA) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def render(tokenizer, example: dict) -> tuple[str, list[tuple[int, int]]]:
    """The full text and the character spans that get loss."""
    messages, tools = example["messages"], example["tools"]
    full = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False)
    spans, previous = [], tokenizer.apply_chat_template(messages[:1], tools=tools, tokenize=False)
    for k in range(2, len(messages) + 1):
        text = tokenizer.apply_chat_template(messages[:k], tools=tools, tokenize=False)
        if not full.startswith(text) or not text.startswith(previous):
            raise ValueError(f"{example['id']}: the template is not prefix-stable at message {k}")
        start, end = len(previous), len(text)
        role = messages[k - 1]["role"]
        if role == "assistant":
            if full.startswith(HEADER, start):
                start += len(HEADER)
            if full[start:end].endswith(END + "\n"):
                end -= 1
            if not full[start:end].endswith((TOOL_RESPONSE, END)):
                raise ValueError(f"{example['id']}: assistant message {k} does not end with a stop token")
            spans.append((start, end))
        previous = text
    return full, spans


def tokenize(tokenizer, example: dict) -> dict:
    """input_ids and labels (-100 outside the loss spans). A token gets loss if it lies inside a span."""
    full, spans = render(tokenizer, example)
    encoded = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
    labels = []
    for token, (start, end) in zip(encoded["input_ids"], encoded["offset_mapping"]):
        inside = any(a <= start and end <= b for a, b in spans) and end > start
        labels.append(token if inside else -100)
    return {"id": example["id"], "input_ids": encoded["input_ids"], "labels": labels}


def _tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(BASE, revision=REVISION)


def stats() -> dict:
    tokenizer = _tokenizer()
    rows = [tokenize(tokenizer, example) for example in examples()]
    lengths = sorted(len(row["input_ids"]) for row in rows)
    loss = [sum(label != -100 for label in row["labels"]) for row in rows]

    def q(p):
        return lengths[min(int(p * len(lengths)), len(lengths) - 1)]

    result = {"conversations": len(rows), "tokens_total": sum(lengths), "loss_tokens_total": sum(loss),
              "length": {"min": lengths[0], "median": q(0.5), "p90": q(0.9), "p99": q(0.99), "max": lengths[-1]},
              "loss_tokens_median": statistics.median(loss), "no_loss_tokens": sum(n == 0 for n in loss)}
    return result


def _plain(value):
    """The converter returns numbers and Booleans as text; the server's adapter types them from the tool schema
    (base Gemma's validation calls came back as integers), so the round trip compares them, and null, as text."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "null"
    return value if isinstance(value, str) else str(value)


def roundtrip() -> dict:
    """Every tool call, rendered by the template and parsed back by the converter vLLM's gemma4 parser uses, must
    give the same name and arguments. Needs the vLLM environment."""
    from vllm.parser.gemma4 import _gemma4_arg_converter
    tokenizer = _tokenizer()
    pattern = re.compile(r"<\|tool_call\>call:(\w+)\{(.*?)\}<tool_call\|>", re.DOTALL)
    calls = mismatches = 0
    examples_seen = []
    for example in examples():
        full, spans = render(tokenizer, example)
        rendered = [m for a, b in spans for m in pattern.finditer(full[a:b])]
        expected = [call["function"] for message in example["messages"] if message["role"] == "assistant"
                    for call in message.get("tool_calls", [])]
        if len(rendered) != len(expected):
            mismatches += 1
            examples_seen.append({"id": example["id"], "problem": f"{len(rendered)} rendered, {len(expected)} sent"})
            continue
        for match, call in zip(rendered, expected):
            calls += 1
            name = match.group(1)
            arguments = json.loads(_gemma4_arg_converter(match.group(2), False)) \
                if match.group(2).strip() else {}
            want = call["arguments"]
            if name != call["name"] or _plain(arguments) != _plain(want):
                mismatches += 1
                if len(examples_seen) < 10:
                    examples_seen.append({"id": example["id"], "sent": [call["name"], want],
                                          "parsed": [name, arguments]})
    return {"tool_calls": calls, "mismatches": mismatches, "examples": examples_seen}


PROCESSOR_FILES = ("chat_template.jinja", "processor_config.json", "tokenizer_config.json", "tokenizer.json")
MERGED = Path.home() / ".local" / "share" / "resplens" / "b2-models"  # merged models for vLLM (large, outside git)
# sdpa for the language model (the audio tower has no sdpa); the default left the text attention to a path whose
# recomputation under gradient checkpointing gave different shapes.
ATTENTION = {"text_config": "sdpa", "vision_config": "sdpa", "audio_config": "eager"}
EPOCHS, BATCH, ACCUMULATION, WARMUP, DROPOUT, SEED = 3, 1, 16, 0.03, 0.05, 0


def run_name(rank: int, lr: float) -> str:
    return f"r{rank}-lr{lr:g}"


def _commit() -> str:
    import subprocess
    git = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = git("git", "status", "--porcelain", "--", "src", "eval/finetune/train.jsonl")
    return git("git", "rev-parse", "--short", "HEAD") + ("-dirty" if dirty else "")


def _collate(rows: list[dict], pad_id: int) -> dict:
    import torch
    width = max(len(row["input_ids"]) for row in rows)
    ids = [row["input_ids"] + [pad_id] * (width - len(row["input_ids"])) for row in rows]
    labels = [row["labels"] + [-100] * (width - len(row["labels"])) for row in rows]
    mask = [[1] * len(row["input_ids"]) + [0] * (width - len(row["input_ids"])) for row in rows]
    return {"input_ids": torch.tensor(ids), "labels": torch.tensor(labels), "attention_mask": torch.tensor(mask)}


def fit(rank: int, lr: float, limit: int | None = None, max_steps: int = -1) -> Path:
    """Train one configuration for 3 epochs with an adapter saved after each epoch."""
    import peft
    import torch
    import transformers
    from transformers import AutoModelForImageTextToText, Trainer, TrainingArguments

    out = RUNS / run_name(rank, lr) if limit is None else RUNS / f"smoke-{run_name(rank, lr)}"
    out.mkdir(parents=True, exist_ok=True)
    tokenizer = _tokenizer()
    rows = [tokenize(tokenizer, example) for example in examples()[:limit]]
    model = AutoModelForImageTextToText.from_pretrained(BASE, revision=REVISION, dtype=torch.bfloat16,
                                                        attn_implementation=ATTENTION).to("cuda")
    model.config.use_cache = False
    config = peft.LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=DROPOUT, target_modules=TARGET,
                             bias="none", task_type="CAUSAL_LM")
    model = peft.get_peft_model(model, config)
    adapted = [name for name, module in model.named_modules() if isinstance(module, peft.tuners.lora.LoraLayer)]
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    args = TrainingArguments(output_dir=str(out), num_train_epochs=EPOCHS, max_steps=max_steps,
                             per_device_train_batch_size=BATCH, gradient_accumulation_steps=ACCUMULATION,
                             learning_rate=lr, lr_scheduler_type="cosine", warmup_steps=WARMUP, bf16=True,
                             gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
                             logging_steps=5, save_strategy="epoch", save_only_model=True, seed=SEED,
                             data_seed=SEED, report_to=[], remove_unused_columns=False, dataloader_num_workers=1)
    (out / "config.json").write_text(json.dumps({
        "base": BASE, "revision": REVISION, "rank": rank, "alpha": 2 * rank, "dropout": DROPOUT, "lr": lr,
        "epochs": EPOCHS, "batch": BATCH, "accumulation": ACCUMULATION, "schedule": "cosine", "warmup": WARMUP,
        "seed": SEED, "conversations": len(rows), "max_length": max(len(r["input_ids"]) for r in rows),
        "target": TARGET, "adapted_modules": len(adapted), "trainable_parameters": trainable,
        "attention": ATTENTION, "sdpa_backend": "efficient", "git_commit": _commit(),
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__,
                     "peft": peft.__version__}}, indent=1))
    trainer = Trainer(model=model, args=args, train_dataset=rows,
                      data_collator=lambda batch: _collate(batch, tokenizer.pad_token_id))
    from torch.nn.attention import SDPBackend, sdpa_kernel
    with sdpa_kernel(SDPBackend.EFFICIENT_ATTENTION):  # the same kernel in the forward pass and its recomputation
        trainer.train()
    (out / "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))
    return out


def merge(adapter: Path, target: Path) -> Path:
    """W' = W + (alpha / r) B A for every adapted module; saves a full model, with the base's own tokenizer, chat
    template and processor files copied unchanged (vLLM serves it exactly like the base)."""
    import shutil

    import peft
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForImageTextToText

    model = AutoModelForImageTextToText.from_pretrained(BASE, revision=REVISION, dtype=torch.bfloat16)
    model = peft.PeftModel.from_pretrained(model, str(adapter)).merge_and_unload()
    target.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(target)
    base = Path(snapshot_download(BASE, revision=REVISION))
    for name in PROCESSOR_FILES:
        shutil.copy(base / name, target / name)
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats")
    commands.add_parser("roundtrip")
    train = commands.add_parser("fit")
    train.add_argument("--rank", type=int, required=True)
    train.add_argument("--lr", type=float, required=True)
    train.add_argument("--limit", type=int, help="first N conversations only (smoke test)")
    train.add_argument("--max-steps", type=int, default=-1)
    combine = commands.add_parser("merge")
    combine.add_argument("adapter", type=Path)
    combine.add_argument("target", type=Path)
    args = parser.parse_args(argv)
    if args.command == "fit":
        print(fit(args.rank, args.lr, args.limit, args.max_steps))
    elif args.command == "merge":
        print(merge(args.adapter, args.target))
    else:
        print(json.dumps(stats() if args.command == "stats" else roundtrip(), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
