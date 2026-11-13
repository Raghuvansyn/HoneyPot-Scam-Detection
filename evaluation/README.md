# Evaluation and regression checks

## Reproduced offline checks

From the repository root after installing `requirements-dev.txt`:

```bash
python -m pytest -q
python -m examples.offline_demo
python -m evaluation.scripts.offline_detection
```

The pytest suite asserts application behavior without network access. The demonstration runs ten synthetic incoming messages through the real API, graph, extraction and SQLite state, using a clearly labelled persona fixture. It closes at 20 combined messages; the GUVI callback is a dry run. Neither command measures live model quality or deployed performance.

`dataset/offline_cases.json` contains 16 manually authored synthetic regression cases, 8 scam and 8 non-scam. The detection probe runs the real rule/TF-IDF/SVM cascade and abstains where a live LLM would be required. It checks there are no exact normalized-string duplicates of the 115 embedded training strings. This does not rule out template similarity or establish independence from development choices.

The local Python 3.13 run on 14 November 2026 produced:

| Outcome | Count |
|---|---:|
| True positives |8|
| True negatives |3|
| False positives |1|
| False negatives among decided cases |0|
| Abstentions requiring LLM |4|

All four abstentions were non-scam examples. The neutral `bank-discussion` example was wrongly classified as a scam by the bank keyword. Both outcomes remain in the probe. Do not report selective-case performance as overall accuracy, or infer generalization from this small set. Raw output includes each case ID, prediction and heuristic score; scores are not calibrated probabilities. No latency/cost metric is reported for this offline setup.

## Existing artifacts and unsupported claims

The model trains lazily on 115 source-embedded strings (65 scam, 50 legitimate), with no train/validation/test partition. There is no saved independently evaluated model artifact or reproducible held-out accuracy result. The same pipeline performs training and inference preprocessing via scikit-learn's `Pipeline`.

`dataset/reddit_scams.json` contains 18 historical scenarios with descriptive source labels. It lacks per-item source URLs, collection method, permission records and independent labels. Its provenance and reuse terms remain unresolved; it is not used in the new offline probe and should not be advertised as a verified real-world benchmark.

The historical `scripts/expand_prompts.py` generates variations; `scripts/run_evaluation.py` requires a running API and a generated dataset. Its detection metric infers detection from reply wording instead of the `scamDetected` field, and its source description overstates provenance. Its results should not support portfolio accuracy/throughput claims. These scripts remain for historical inspection and are not part of default CI. Do not run stress scripts against a service without authorization.

## Remaining live verification

Set a private API access key and your own provider key, keep `MODE=dev`, start the local server, and exercise representative scam/non-scam/malformed requests. Record provider/model/date, classification fields, human-labelled expected outcomes, provider failures, token usage and per-request elapsed time. Evaluate persona replies separately for safety, factuality, useful probing and failure behavior. A successful local provider request still does not verify a hosted deployment.

Before benchmark claims, create a separately labelled, permission-cleared dataset, deduplicate across all splits, freeze a test set, compare rule-only and ML baselines under the same protocol, and report false positives/negatives plus abstentions. Keep synthetic variations from the same source scenario in a single split.
