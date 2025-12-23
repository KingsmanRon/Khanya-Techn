"""API Key Authentication Service

Handles organization-level API key authentication for MTP endpoints.
Each organization gets API keys with specific permissions and rate limits.
"""
import logging
import secrets
import hashlib
from typing import Optional, List, Tuple
from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)

# API Key header
API_KEY_HEADER = APIKeyHeader(name="X-MTP-API-Key", auto_error=False)


class APIKeyInfo(BaseModel):
    """API Key information"""
    id: str
    org_id: str
    name: str
    permissions: List[str]
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]


class APIKeyService:
    """
    API Key Management Service

    Features:
    - Generate secure API keys for organizations
    - Hash-based key storage (keys are never stored in plain text)
    - Permission-based access control
    - Rate limiting per key
    - Key rotation support
    """

    # Key prefix for identification
    KEY_PREFIX = "mtp_"

    # Available permissions
    PERMISSIONS = {
        # Agent operations
        "agents:read": "Read agent information",
        "agents:write": "Create and update agents",
        "agents:delete": "Deactivate agents",

        # Audit operations
        "audit:read": "Read audit events",
        "audit:write": "Log audit events",

        # Dispute operations
        "disputes:read": "Read disputes",
        "disputes:write": "File and respond to disputes",
        "disputes:resolve": "Resolve disputes (arbitrator)",

        # Insurance operations
        "insurance:read": "Read risk profiles and quotes",
        "insurance:write": "File claims",

        # Admin operations
        "admin:*": "Full administrative access"
    }

    def generate_api_key(self) -> Tuple[str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (plain_key, key_hash)
            The plain_key should be shown to the user once and never stored.
        """
        # Generate 32 bytes of random data
        random_bytes = secrets.token_bytes(32)

        # Create the key with prefix
        plain_key = f"{self.KEY_PREFIX}{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = self._hash_key(plain_key)

        return plain_key, key_hash

    def _hash_key(self, plain_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(plain_key.encode()).hexdigest()

    async def create_api_key(
        self,
        org_id: str,
        name: str,
        permissions: List[str],
        rate_limit_per_minute: int = 1000,
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, APIKeyInfo]:
        """
        Create a new API key for an organization.

        Args:
            org_id: Organization ID
            name: Descriptive name for the key
            permissions: List of permission strings
            rate_limit_per_minute: Rate limit for this key
            expires_in_days: Optional expiration in days

        Returns:
            Tuple of (plain_key, APIKeyInfo)
            IMPORTANT: The plain_key is only returned once!
        """
        # Validate permissions
        for perm in permissions:
            if perm not in self.PERMISSIONS and perm != "*":
                raise ValueError(f"Invalid permission: {perm}")

        # Generate key
        plain_key, key_hash = self.generate_api_key()

        key_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = created_at + timedelta(days=expires_in_days)

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO api_keys (
                    id, org_id, key_hash, name, permissions,
                    rate_limit_per_minute, is_active, created_at, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                uuid.UUID(key_id),
                uuid.UUID(org_id),
                key_hash,
                name,
                permissions,
                rate_limit_per_minute,
                True,
                created_at,
                expires_at
            )

        logger.info(f"Created API key '{name}' for organization {org_id}")

        return plain_key, APIKeyInfo(
            id=key_id,
            org_id=org_id,
            name=name,
            permissions=permissions,
            rate_limit_per_minute=rate_limit_per_minute,
            is_active=True,
            created_at=created_at,
            expires_at=expires_at,
            last_used_at=None
        )

    async def validate_api_key(self, api_key: str) -> Optional[APIKeyInfo]:
        """
        Validate an API key and return its info.

        Args:
            api_key: The plain API key to validate

        Returns:
            APIKeyInfo if valid, None if invalid
        """
        if not api_key or not api_key.startswith(self.KEY_PREFIX):
            return None

        key_hash = self._hash_key(api_key)

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, org_id, name, permissions, rate_limit_per_minute,
                       is_active, created_at, expires_at, last_used_at
                FROM api_keys
                WHERE key_hash = $1
                """,
                key_hash
            )

            if not row:
                return None

            # Check if active
            if not row['is_active']:
                logger.warning(f"Inactive API key used: {row['name']}")
                return None

            # Check expiration
            if row['expires_at'] and row['expires_at'] < datetime.now(timezone.utc):
                logger.warning(f"Expired API key used: {row['name']}")
                return None

            # Update last used
            await conn.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                row['id']
            )

            return APIKeyInfo(
                id=str(row['id']),
                org_id=str(row['org_id']),
                name=row['name'],
                permissions=row['permissions'],
                rate_limit_per_minute=row['rate_limit_per_minute'],
                is_active=row['is_active'],
                created_at=row['created_at'],
                expires_at=row['expires_at'],
                last_used_at=datetime.now(timezone.utc)
            )

    async def check_permission(
        self,
        api_key_info: APIKeyInfo,
        required_permission: str
    ) -> bool:
        """
        Check if an API key has a specific permission.

        Args:
            api_key_info: The validated API key info
            required_permission: The permission to check

        Returns:
            True if permitted, False otherwise
        """
        # Admin wildcard
        if "admin:*" in api_key_info.permissions:
            return True

        # Exact match
        if required_permission in api_key_info.permissions:
            return True

        # Category wildcard (e.g., "agents:*" matches "agents:read")
        category = required_permission.split(":")[0]
        if f"{category}:*" in api_key_info.permissions:
            return True

        return False

    async def revoke_api_key(self, key_id: str):
        """Revoke an API key"""
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE api_keys SET is_active = FALSE WHERE id = $1",
                uuid.UUID(key_id)
            )
        logger.info(f"API key {key_id} revoked")

    async def list_api_keys(self, org_id: str) -> List[APIKeyInfo]:
        """List all API keys for an organization"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, org_id, name, permissions, rate_limit_per_minute,
                       is_active, created_at, expires_at, last_used_at
                FROM api_keys
                WHERE org_id = $1
                ORDER BY created_at DESC
                """,
                uuid.UUID(org_id)
            )

            return [
                APIKeyInfo(
                    id=str(row['id']),
                    org_id=str(row['org_id']),
                    name=row['name'],
                    permissions=row['permissions'],
                    rate_limit_per_minute=row['rate_limit_per_minute'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    last_used_at=row['last_used_at']
                )
                for row in rows
            ]

    async def rotate_api_key(
        self,
        old_key_id: str
    ) -> Tuple[str, APIKeyInfo]:
        """
        Rotate an API key - create new one and revoke old.

        Args:
            old_key_id: ID of the key to rotate

        Returns:
            Tuple of (new_plain_key, new_APIKeyInfo)
        """
        async with db_pool.acquire() as conn:
            # Get old key info
            row = await conn.fetchrow(
                """
                SELECT org_id, name, permissions, rate_limit_per_minute
                FROM api_keys WHERE id = $1
                """,
                uuid.UUID(old_key_id)
            )

            if not row:
                raise ValueError("API key not found")

            # Create new key with same settings
            new_key, new_info = await self.create_api_key(
                org_id=str(row['org_id']),
                name=f"{row['name']} (rotated)",
                permissions=row['permissions'],
                rate_limit_per_minute=row['rate_limit_per_minute']
            )

            # Revoke old key
            await self.revoke_api_key(old_key_id)

            logger.info(f"API key {old_key_id} rotated to {new_info.id}")

            return new_key, new_info


# Global service instance
api_key_service = APIKeyService()


# FastAPI dependency for authentication
async def get_api_key(
    api_key: str = Security(API_KEY_HEADER)
) -> APIKeyInfo:
    """
    FastAPI dependency to validate API key from header.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(api_key: APIKeyInfo = Depends(get_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-MTP-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    key_info = await api_key_service.validate_api_key(api_key)

    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return key_info


def require_permission(permission: str):
    """
    Decorator/dependency to require specific permission.

    Usage:
        @router.get("/agents")
        async def list_agents(
            api_key: APIKeyInfo = Depends(require_permission("agents:read"))
        ):
            ...
    """
    async def check_permission(
        api_key: APIKeyInfo = Depends(get_api_key)
    ) -> APIKeyInfo:
        has_permission = await api_key_service.check_permission(
            api_key,
            permission
        )

        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {permission}"
            )

        return api_key

    return check_permission


# Optional API key - doesn't fail if missing
async def get_optional_api_key(
    api_key: str = Security(API_KEY_HEADER)
) -> Optional[APIKeyInfo]:
    """
    FastAPI dependency for optional API key validation.
    Returns None if no key provided, validates if provided.
    """
    if not api_key:
        return None

    return await api_key_service.validate_api_key(api_key)
