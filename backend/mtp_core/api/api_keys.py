"""API Keys Management Endpoints

Endpoints for managing organization API keys.
These endpoints require admin authentication.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from mtp_core.services.api_auth import (
    api_key_service,
    APIKeyInfo,
    get_api_key,
    require_permission
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# Request/Response Models
class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key"""
    org_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Descriptive name for the key")
    permissions: List[str] = Field(
        ...,
        description="List of permissions for this key"
    )
    rate_limit_per_minute: int = Field(
        default=1000,
        description="Rate limit (requests per minute)",
        ge=10,
        le=10000
    )
    expires_in_days: Optional[int] = Field(
        None,
        description="Optional expiration in days",
        ge=1,
        le=365
    )

    class Config:
        json_schema_extra = {
            "example": {
                "org_id": "uuid-of-organization",
                "name": "Production API Key",
                "permissions": [
                    "agents:read",
                    "agents:write",
                    "audit:read",
                    "audit:write"
                ],
                "rate_limit_per_minute": 1000,
                "expires_in_days": 365
            }
        }


class APIKeyResponse(BaseModel):
    """API key response (without the actual key)"""
    id: str
    org_id: str
    name: str
    permissions: List[str]
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]


class APIKeyCreatedResponse(BaseModel):
    """Response when creating a new API key"""
    api_key: str = Field(..., description="The API key - SAVE THIS, shown only once!")
    key_info: APIKeyResponse


class APIKeyListResponse(BaseModel):
    """List of API keys"""
    keys: List[APIKeyResponse]
    total: int


# API Endpoints
@router.post("", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: APIKeyInfo = Depends(require_permission("admin:*"))
):
    """
    Create a new API key for an organization.

    IMPORTANT: The API key is only shown once in the response.
    Make sure to save it securely - it cannot be retrieved later.

    Requires: admin:* permission
    """
    try:
        plain_key, key_info = await api_key_service.create_api_key(
            org_id=request.org_id,
            name=request.name,
            permissions=request.permissions,
            rate_limit_per_minute=request.rate_limit_per_minute,
            expires_in_days=request.expires_in_days
        )

        logger.info(f"API key created: {request.name} for org {request.org_id}")

        return APIKeyCreatedResponse(
            api_key=plain_key,
            key_info=APIKeyResponse(
                id=key_info.id,
                org_id=key_info.org_id,
                name=key_info.name,
                permissions=key_info.permissions,
                rate_limit_per_minute=key_info.rate_limit_per_minute,
                is_active=key_info.is_active,
                created_at=key_info.created_at,
                expires_at=key_info.expires_at,
                last_used_at=key_info.last_used_at
            )
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    org_id: str = Query(..., description="Organization ID"),
    auth: APIKeyInfo = Depends(require_permission("admin:*"))
):
    """
    List all API keys for an organization.

    Requires: admin:* permission
    """
    keys = await api_key_service.list_api_keys(org_id)

    return APIKeyListResponse(
        keys=[
            APIKeyResponse(
                id=k.id,
                org_id=k.org_id,
                name=k.name,
                permissions=k.permissions,
                rate_limit_per_minute=k.rate_limit_per_minute,
                is_active=k.is_active,
                created_at=k.created_at,
                expires_at=k.expires_at,
                last_used_at=k.last_used_at
            )
            for k in keys
        ],
        total=len(keys)
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    auth: APIKeyInfo = Depends(require_permission("admin:*"))
):
    """
    Revoke an API key.

    The key will be immediately invalidated.

    Requires: admin:* permission
    """
    try:
        await api_key_service.revoke_api_key(key_id)
        logger.info(f"API key revoked: {key_id}")
        return {"status": "revoked", "key_id": key_id}

    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.post("/{key_id}/rotate", response_model=APIKeyCreatedResponse)
async def rotate_api_key(
    key_id: str,
    auth: APIKeyInfo = Depends(require_permission("admin:*"))
):
    """
    Rotate an API key.

    This creates a new key with the same permissions and revokes the old one.

    IMPORTANT: The new API key is only shown once in the response.

    Requires: admin:* permission
    """
    try:
        new_key, new_info = await api_key_service.rotate_api_key(key_id)

        logger.info(f"API key rotated: {key_id} -> {new_info.id}")

        return APIKeyCreatedResponse(
            api_key=new_key,
            key_info=APIKeyResponse(
                id=new_info.id,
                org_id=new_info.org_id,
                name=new_info.name,
                permissions=new_info.permissions,
                rate_limit_per_minute=new_info.rate_limit_per_minute,
                is_active=new_info.is_active,
                created_at=new_info.created_at,
                expires_at=new_info.expires_at,
                last_used_at=new_info.last_used_at
            )
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rotate API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to rotate API key")


@router.get("/permissions")
async def list_available_permissions():
    """
    List all available API key permissions.

    Returns the permission strings and their descriptions.
    """
    return {
        "permissions": api_key_service.PERMISSIONS,
        "categories": {
            "agents": "Agent management operations",
            "audit": "Audit event operations",
            "disputes": "Dispute resolution operations",
            "insurance": "Insurance and risk operations",
            "admin": "Administrative operations"
        }
    }


@router.get("/me", response_model=APIKeyResponse)
async def get_current_key_info(
    auth: APIKeyInfo = Depends(get_api_key)
):
    """
    Get information about the current API key.

    Returns the key metadata (not the key itself).
    """
    return APIKeyResponse(
        id=auth.id,
        org_id=auth.org_id,
        name=auth.name,
        permissions=auth.permissions,
        rate_limit_per_minute=auth.rate_limit_per_minute,
        is_active=auth.is_active,
        created_at=auth.created_at,
        expires_at=auth.expires_at,
        last_used_at=auth.last_used_at
    )
