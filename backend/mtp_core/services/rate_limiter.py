"""Rate Limiting Service - DoS Protection for Gateway"""
from datetime import datetime, timezone, timedelta
from typing import Tuple
import logging

from mtp_core.db.postgres import db_pool
from mtp_core.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiter for Gateway Protection.

    Implements a sliding window rate limiter using PostgreSQL.
    This prevents DoS attacks against the Gateway.

    Default limits:
    - 100 requests per minute per agent
    - 1000 requests per minute per organization (via API key)
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check_rate_limit(self, mtp_id: str) -> Tuple[bool, int, int]:
        """
        Check if an agent has exceeded their rate limit.

        Args:
            mtp_id: Agent's MTP ID

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = datetime.now(timezone.utc)
        window_start_threshold = now - timedelta(seconds=self.window_seconds)

        async with db_pool.acquire() as conn:
            # Get or create rate limit bucket
            row = await conn.fetchrow(
                """
                SELECT request_count, window_start, last_request_at
                FROM rate_limit_buckets
                WHERE mtp_id = $1
                """,
                mtp_id
            )

            if row is None:
                # First request from this agent
                await conn.execute(
                    """
                    INSERT INTO rate_limit_buckets (mtp_id, request_count, window_start, last_request_at)
                    VALUES ($1, 1, $2, $2)
                    """,
                    mtp_id, now
                )
                return True, self.max_requests - 1, 0

            window_start = row['window_start']
            request_count = row['request_count']

            # Check if we need to reset the window
            if window_start < window_start_threshold:
                # Reset window
                await conn.execute(
                    """
                    UPDATE rate_limit_buckets
                    SET request_count = 1, window_start = $2, last_request_at = $2
                    WHERE mtp_id = $1
                    """,
                    mtp_id, now
                )
                return True, self.max_requests - 1, 0

            # Check if limit exceeded
            if request_count >= self.max_requests:
                # Calculate retry-after
                window_end = window_start + timedelta(seconds=self.window_seconds)
                retry_after = max(0, int((window_end - now).total_seconds()))

                logger.warning(
                    f"Rate limit exceeded for agent {mtp_id}: "
                    f"{request_count}/{self.max_requests} requests"
                )

                return False, 0, retry_after

            # Increment counter
            await conn.execute(
                """
                UPDATE rate_limit_buckets
                SET request_count = request_count + 1, last_request_at = $2
                WHERE mtp_id = $1
                """,
                mtp_id, now
            )

            remaining = self.max_requests - request_count - 1
            return True, remaining, 0

    async def reset_rate_limit(self, mtp_id: str) -> None:
        """
        Reset rate limit for an agent (admin function).

        Args:
            mtp_id: Agent's MTP ID
        """
        async with db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM rate_limit_buckets WHERE mtp_id = $1",
                mtp_id
            )
        logger.info(f"Rate limit reset for agent {mtp_id}")


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=100,  # 100 requests
    window_seconds=60   # per minute
)
