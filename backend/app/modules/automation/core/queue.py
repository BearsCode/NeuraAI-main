from redis.asyncio import Redis

class QueueManager:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def enqueue(self, queue_name: str, payload: str) -> None:
        await self.redis.lpush(queue_name, payload)

    async def dequeue(self, queue_name: str) -> str | None:
        item = await self.redis.rpop(queue_name)
        if item is None:
            return None
        return item.decode("utf-8") if isinstance(item, bytes) else item

    async def save_state(self, key: str, state: str, expire: int = 3600) -> None:
        await self.redis.set(key, state, ex=expire)

    async def get_state(self, key: str) -> str | None:
        val = await self.redis.get(key)
        if val is None:
            return None
        return val.decode("utf-8") if isinstance(val, bytes) else val
