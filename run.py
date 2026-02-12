# run.py
"""
Server Startup Script - OPTIMIZED FOR CONCURRENCY
Run this file to start the honeypot server.

Usage:
    python run.py
"""

import uvicorn
import multiprocessing

if __name__ == "__main__":

    # FOR DEMO PURPOSES: Use 1 worker to prevent messy logs on Windows
    # In production, use (cpu_count * 2) + 1
    cpu_count = multiprocessing.cpu_count()
    workers = 1

    print("=" * 70)
    print("STARTING SCAMBAIT AI - HONEYPOT API")
    print("=" * 70)
    print()
    print(f"API:         http://127.0.0.1:8002")
    print(f"Docs:        http://127.0.0.1:8002/docs")
    print(f"Health:      http://127.0.0.1:8002/health")
    print()
    print(f"CPU Cores:   {cpu_count}")
    print(f"Workers:     {workers} (handles {workers * 30} concurrent requests)")
    print(f"Concurrency: 50+ simultaneous requests supported")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",           # Accept from any IP (needed for hackathon)
        port=8002,
        reload=False,
        workers=workers,           # Multiple worker processes
        loop="asyncio",            # Async event loop
        http="httptools",          # Faster HTTP parser
        limit_concurrency=200,     # Max concurrent connections
        limit_max_requests=10000,  # Restart worker after 10k requests (memory)
        timeout_keep_alive=30,     # Keep connections alive 30s
        access_log=True,           # Log all requests
    )
