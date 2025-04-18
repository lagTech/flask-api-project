from rq import Queue, Connection, SimpleWorker
from api8inf349.redis_client import redis_client

if __name__ == "__main__":
    with Connection(redis_client):
        queue = Queue()
        worker = SimpleWorker([queue])
        worker.work()
