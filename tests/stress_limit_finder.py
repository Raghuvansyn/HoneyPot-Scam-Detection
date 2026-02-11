import asyncio
import aiohttp
import time
import json
import random

# CONFIGURATION
URL = "https://scambait-ai-production.up.railway.app/api/v1/honeypot"
API_KEY = "GUVI-Hackathon-2026-ScamBait-xK9mP2vL7qR3wT8"
TIMEOUT = 60  # Client timeout (seconds)

async def send_request(session, user_id):
    """Send a single scam request."""
    session_id = f"stress-finder-{user_id}-{random.randint(1000, 9999)}"
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": f"URGENT: Account {user_id} blocked. Verify OTP immediately.",
            "timestamp": "2026-02-11T12:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }
    
    start_time = time.time()
    try:
        async with session.post(URL, json=payload, headers={"x-api-key": API_KEY}) as resp:
            elapsed = time.time() - start_time
            if resp.status == 200:
                data = await resp.json()
                return {"status": "success", "time": elapsed, "reply": data.get("reply", "")[:30]}
            else:
                text = await resp.text()
                return {"status": "fail", "code": resp.status, "error": text[:100]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def run_batch(n_users):
    """Run a batch of N concurrent users."""
    print(f"\n[TESTING] Batch: {n_users} Concurrent Users...")
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        tasks = [send_request(session, i) for i in range(n_users)]
        results = await asyncio.gather(*tasks)
        
    failures = [r for r in results if r["status"] != "success"]
    successes = [r for r in results if r["status"] == "success"]
    
    avg_time = 0
    if successes:
        avg_time = sum(r["time"] for r in successes) / len(successes)
        
    print(f"   [RESULT] Success: {len(successes)} | Fail: {len(failures)} | Avg Latency: {avg_time:.2f}s")
    
    if failures:
        print(f"   [ERROR] First Failure Detail: {failures[0]}")
        return False  # Batch FAILED
    return True  # Batch PASSED

async def find_limit():
    print("=== STRESS LIMIT FINDER ===")
    print(f"Target: {URL}")
    
    # Ramping up from 10 to 60 users
    for n in range(10, 65, 5):
        success = await run_batch(n)
        if not success:
            print(f"\n[STOP] SYSTEM BREAKING POINT FOUND: {n} USERS")
            return
        
        # Cool down
        print("   [WAIT] Cooling down 2s...")
        await asyncio.sleep(2)
        
    print("\n[DONE] SYSTEM SURVIVED UP TO 60 USERS! (Excellent)")

if __name__ == "__main__":
    # Install dependency if missing (just in case)
    try:
        import aiohttp
    except ImportError:
        import os
        os.system("pip install aiohttp")
        import aiohttp
        
    asyncio.run(find_limit())
