from rq import SimpleWorker, Queue
from api8inf349.redis_client import redis_client

if __name__ == "__main__":
    queue = Queue(connection=redis_client)
    worker = SimpleWorker([queue], connection=redis_client)
    print("🚀 SimpleWorker started (no fork, Windows-compatible)")
    worker.work()
