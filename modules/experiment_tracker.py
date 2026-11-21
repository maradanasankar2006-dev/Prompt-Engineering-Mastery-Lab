"""Append-only JSON experiment storage."""

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "experiments.json"
_FILE_LOCK = threading.Lock()


def load_experiments() -> list[dict[str, Any]]:
    """Load all saved experiments without hiding malformed-file errors."""
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as file:
        experiments = json.load(file)
    if not isinstance(experiments, list):
        raise ValueError("The experiment data file must contain a JSON list.")
    return experiments


def record_experiment(
    *,
    technique: str,
    input_text: str,
    prompt: str,
    raw_model_output: str = "",
    expected_output: Any = None,
    correctness: bool | None = None,
    validation_status: str = "not_applicable",
    model: str,
    error: str = "",
) -> dict[str, Any]:
    """Append one API attempt, preserving earlier experiment records."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "experiment_id": str(uuid.uuid4()),
        "technique": technique,
        "input": input_text,
        "prompt": prompt,
        "raw_model_output": raw_model_output,
        "expected_output": expected_output,
        "correctness": correctness,
        "validation_status": validation_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "error": error,
    }

    with _FILE_LOCK:
        experiments = load_experiments()
        experiments.append(record)
        with DATA_PATH.open("w", encoding="utf-8") as file:
            json.dump(experiments, file, ensure_ascii=False, indent=2)
            file.write("\n")

    return record
