# app/utils/rate_limiting.py

import logging
import time
from functools import lru_cache

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis, RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    A class to handle rate limiting for API requests.
    Built using Sliding Window Counter algorithm with Redis as the Storage.
    """

    def __init__(self, max_requests: int, window_size: int, redis_client: Redis):
        """
        Initializes the RateLimiter with a maximum number of requests and a time window.

        Args:
            max_requests (int): Maximum number of requests allowed in the time window.
            window_size (int): Time window size in seconds.
        """
        self._max_requests = max(max_requests, 1)
        self._window_size = max(window_size, 1)
        self._redis_client = redis_client

    async def __call__(self, request: Request):
        """
        Middleware function to check if the incoming request exceeds the rate limit.

        Args:
            request (Request): The incoming FastAPI request.
        Raises:
            HTTPException: If the request exceeds the rate limit.
        """
        identifier = request.client.host if request.client else "unknown"

        now = time.time()
        current_window = int(now // self._window_size)
        prev_window = current_window - 1

        elapsed_ratio = (now % self._window_size) / self._window_size
        prev_weight = 1.0 - elapsed_ratio

        curr_window_key = f"rate_limit:{identifier}:{current_window}"
        prev_window_key = f"rate_limit:{identifier}:{prev_window}"

        try:
            async with self._redis_client.pipeline(transaction=True) as pipe:
                pipe.get(prev_window_key)
                pipe.incr(curr_window_key)

                pipe.expire(curr_window_key, self._window_size * 2)
                prev_count, curr_count, _ = await pipe.execute()

            prev_count = int(prev_count) if prev_count else 0
            curr_count = int(curr_count) if curr_count else 0

            weighted_count = prev_count * prev_weight + curr_count

            if weighted_count > self._max_requests:
                await self._redis_client.decr(curr_window_key)
                retry_after = max(1, self._window_size - (now % self._window_size))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(int(retry_after))},
                )
        except RedisError as e:
            logger.error(f"Redis error during rate limiting: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during rate limiting.",
            )


@lru_cache(maxsize=1)
def _get_redis_client() -> Redis:
    """
    Returns a cached Redis client instance.

    Returns:
        Redis: An instance of the Redis client.
    """
    return Redis.from_url(get_settings().REDIS_URL)


@lru_cache
def rl_is_allowed(max_requests: int, window_size: int) -> RateLimiter:
    """
    Returns a cached instance of the RateLimiter.

    Args:
        max_requests (int): Maximum number of requests allowed in the time window.
        window_size (int): Time window size in seconds.
        redis_url (str): Redis connection URL.

    Returns:
        RateLimiter: An instance of the RateLimiter class.
    """
    return RateLimiter(max_requests, window_size, _get_redis_client())
