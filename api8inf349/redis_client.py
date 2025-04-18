import os
import redis

# Utilise l'URL depuis la variable d'environnement
redis_url = os.getenv("REDIS_URL", "redis://localhost")
redis_client = redis.Redis.from_url(redis_url)
