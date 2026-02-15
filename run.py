import uvicorn
import multiprocessing

if __name__ == "__main__":
    cpu_count = multiprocessing.cpu_count()
    workers = 1

    print(f"ScamBait AI | http://127.0.0.1:8002 | docs: /docs | workers: {workers}")

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        workers=workers,
        loop="asyncio",
        http="httptools",
        limit_concurrency=200,
        limit_max_requests=10000,
        timeout_keep_alive=30,
        access_log=True,
    )
