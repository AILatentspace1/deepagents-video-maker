"""Training data flywheel for the script Generator + Evaluator loop.

Phase 1 (inference-time): accumulate (script, score, suggestions) triplets
that were produced by the GAN Evaluator during normal video production runs.
Each entry is appended to a newline-delimited JSON file so the corpus can
grow incrementally without loading the entire dataset into memory.

Phase 2/3 (fine-tuning): a separate offline process reads the collected
samples and uses high-scoring scripts for SFT and (good, bad) pairs for DPO.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import EvalSample

# File written inside each session's output dir so samples stay co-located
# with the ratify artifacts that produced them.
_SAMPLES_FILENAME = "eval-samples.jsonl"
_TRAINING_DIR = "training"


def eval_samples_path(output_dir: str | Path) -> Path:
    """Return the path to the session-local training data file."""
    return Path(output_dir) / _TRAINING_DIR / _SAMPLES_FILENAME


def append_eval_sample(output_dir: str | Path, sample: EvalSample) -> Path:
    """Append one EvalSample to the session's JSONL training file.

    Creates the directory and file if they do not yet exist.
    Returns the path of the file written to.
    """
    path = eval_samples_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(sample), ensure_ascii=False) + "\n")
    return path


def load_eval_samples(output_dir: str | Path) -> list[EvalSample]:
    """Load all EvalSamples from the session's JSONL training file.

    Returns an empty list if the file does not exist.
    """
    path = eval_samples_path(output_dir)
    if not path.exists():
        return []
    samples: list[EvalSample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        samples.append(EvalSample(**data))
    return samples
