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
    print("API:  http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print("="*70)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )