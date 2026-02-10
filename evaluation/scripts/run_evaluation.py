import asyncio
import aiohttp
import json
import time
import uuid
import os
from datetime import datetime
from statistics import mean
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8002/api/v1/honeypot"
API_KEY = os.getenv("API_KEY", "temp-key")  # Load from .env or default
DATASET_PATH = r"evaluation/dataset/expanded_scams.json"
REPORT_PATH = r"evaluation/reports/summary_report.md"
CONCURRENT_LIMIT = 50  # Number of concurrent requests

async def send_eval_request(session, item):
    """
    Sends a single scam prompt and returns the result metrics.
    """
    session_id = f"eval-{uuid.uuid4().hex[:8]}"
    prompt = item["text"]
    variation = item.get("variation", "unknown")
    category = item.get("category", "unknown")
    
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", 
            "text": prompt,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [], # First message
        "metadata": {"channel": "evaluation_script"}
    }
    
    headers = {"x-api-key": API_KEY}
    
    start_time = time.time()
    try:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            latency = (time.time() - start_time) * 1000  # ms
            status_code = response.status
            
            if status_code == 200:
                data = await response.json()
                reply = data.get("reply", "")
                meta = data.get("meta", {})
                notes = meta.get("agentNotes", "")
                
                # Check detection logic
                # Detection FAILURE = Polite exit message
                is_detected = "Have a great day" not in reply
                
                return {
                    "status": "success",
                    "latency_ms": latency,
                    "is_detected": is_detected,
                    "category": category,
                    "variation": variation,
                    "notes": notes,
                    "reply_snippet": reply[:50]
                }
            else:
                return {
                    "status": "error",
                    "latency_ms": latency,
                    "code": status_code,
                    "category": category,
                    "variation": variation
                }
    except Exception as e:
        return {
            "status": "exception",
            "latency_ms": 0,
            "error": str(e),
            "category": category,
            "variation": variation
        }

async def run_evaluation():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}. Run expand_prompts.py first.")
        return

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Starting evaluation of {len(dataset)} scenarios...")
    print(f"Target: {API_URL}")
    print(f"Concurrency: {CONCURRENT_LIMIT}")
    print("-" * 60)

    connector = aiohttp.TCPConnector(limit=CONCURRENT_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [send_eval_request(session, item) for item in dataset]
        results = await asyncio.gather(*tasks)

    # ============================================
    # ANALYZE RESULTS
    # ============================================
    
    total = len(results)
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] != "success"]
    
    detected = [r for r in successes if r["is_detected"]]
    missed = [r for r in successes if not r["is_detected"]]
    
    latencies = [r["latency_ms"] for r in successes]
    avg_latency = mean(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    detection_rate = (len(detected) / len(successes)) * 100 if successes else 0
    
    # Analyze by Category
    categories = set(r["category"] for r in successes)
    category_stats = {}
    for cat in categories:
        cat_results = [r for r in successes if r["category"] == cat]
        cat_detected = [r for r in cat_results if r["is_detected"]]
        category_stats[cat] = {
            "total": len(cat_results),
            "detected": len(cat_detected),
            "rate": (len(cat_detected)/len(cat_results))*100 if cat_results else 0
        }

    # ============================================
    # GENERATE REPORT
    # ============================================
    
    report = f"""# 🛡️ AI Honeypot Evaluation Report
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Dataset:** {len(dataset)} Scenarios (Reddit/Real-world)
**Variations:** Urgency, Typos, Hinglish, Emojis

## 📊 Executive Summary
| Metric | Value |
| :--- | :--- |
| **Total Scenarios** | {total} |
| **Success Rate (API)** | {len(successes)} ({len(successes)/total*100:.1f}%) |
| **Detection Rate** | **{detection_rate:.1f}%** (Core Metric) |
| **Missed Detections** | {len(missed)} (False Negatives) |
| **Avg Response Time** | {avg_latency:.0f} ms |
| **Max Response Time** | {max_latency:.0f} ms |
| **P95 Latency** | {p95_latency:.0f} ms |

## 🚨 Category Breakdown
| Category | Attempts | Detected | Detection Rate |
| :--- | :--- | :--- | :--- |
"""
    
    for cat, stats in category_stats.items():
        report += f"| {cat} | {stats['total']} | {stats['detected']} | {stats['rate']:.1f}% |\n"
        
    report += "\n## ❌ Missed Detections (False Negatives)\n"
    if missed:
        for m in missed[:10]:
            report += f"- **{m['category']}** ({m['variation']}): _output: {m['reply_snippet']}..._\n"
    else:
        report += "_None! Perfect Detection!_\n"

    report += "\n## ⚡ Performance\n"
    report += f"- Processed {len(successes)} requests in {(sum(latencies)/1000):.2f} total computing seconds (async).\n"
    
    # Save Report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
        
    print("\n" + "="*60)
    print(f"EVALUATION COMPLETE")
    print(f"Detection Rate: {detection_rate:.1f}%")
    print(f"Avg Latency:    {avg_latency:.0f} ms")
    print(f"Report saved to: {REPORT_PATH}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
