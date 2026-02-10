# 🧪 AI Honeypot Evaluation Suite

This module provides tools for stress-testing and evaluating the accuracy of the AI Honeypot against realistic scam scenarios.

## 📂 Structure

- **dataset/**: Contains `reddit_scams.json` (base prompts) and `expanded_scams.json` (generated variations).
- **scripts/**:
  - `expand_prompts.py`: Generates 6 variations for each base prompt (Urgency, Typos, Hinglish, etc.).
  - `run_evaluation.py`: Runs the test suite against the local API and generates a report.
- **reports/**: Stores the generated Markdown reports.

## 🚀 How to Use

### 1. Generate/Update Dataset
If you modify `reddit_scams.json`, regenerate the full dataset:
```bash
python evaluation/scripts/expand_prompts.py
```

### 2. Run Evaluation
Ensure the **Honeypot Server** is running (`python run.py`), then run:
```bash
python evaluation/scripts/run_evaluation.py
```
This will:
- Send ~50 concurrent requests.
- Measure latency and detection rates.
- Save a report to `evaluation/reports/summary_report.md`.

## 📊 Metrics
- **Success Rate**: API returned 200 OK.
- **Detection Rate**: API engaged with the scammer (did NOT return "Have a great day").
- **Latency**: End-to-end response time.
