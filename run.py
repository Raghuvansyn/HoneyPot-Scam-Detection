# run.py
"""
Server Startup Script
Run this file to start the honeypot server.

Usage:
    python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("="*70)
    print("STARTING HONEYPOT API")
    print("="*70)
    print()
    print("API:  http://127.0.0.1:8002")
    print("Docs: http://127.0.0.1:8002/docs")
    print()
    print("Press Ctrl+C to stop")
    print("="*70)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=False
    )