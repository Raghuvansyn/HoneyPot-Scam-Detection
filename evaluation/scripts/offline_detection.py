"""Synthetic regression probe of real rules/ML; LLM-required cases abstain."""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.agents import detection

DATASET = Path(__file__).resolve().parents[1] / "dataset" / "offline_cases.json"


async def evaluate():
    cases = json.loads(DATASET.read_text())
    training = detection.SCAM_TRAINING_DATA + detection.LEGIT_TRAINING_DATA
    overlap = {c["text"].strip().lower() for c in cases} & {t.strip().lower() for t in training}
    if overlap:
        raise ValueError("Regression cases must not exactly duplicate embedded training strings")
    confusion = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "abstained": 0}
    results = []
    fallback = AsyncMock(side_effect=RuntimeError("Offline probe: LLM not evaluated"))
    with patch.object(detection, "llm_fallback_check", fallback):
        for case in cases:
            try:
                prediction, score, _, _ = await detection.detect_scam(case["text"])
                key = ("tp" if case["label"] else "fp") if prediction else ("fn" if case["label"] else "tn")
                confusion[key] += 1
                results.append({"id": case["id"], "label": case["label"], "prediction": prediction,
                                "heuristic_score": float(score)})
            except RuntimeError:
                confusion["abstained"] += 1
                results.append({"id": case["id"], "label": case["label"], "prediction": None})
    return {"method": "rules + embedded TF-IDF/SVM cascade; no live LLM; ambiguous cases abstain",
            "samples": len(cases), "positive": sum(c["label"] for c in cases),
            "negative": sum(not c["label"] for c in cases), "training_samples": len(training),
            "exact_training_overlap": len(overlap), "confusion": confusion, "cases": results,
            "limitations": "Handwritten regression cases, not a representative or independent benchmark. Scores are not calibrated probabilities."}


if __name__ == "__main__":
    print(json.dumps(asyncio.run(evaluate()), indent=2))
