"""Gateway API - The Kill Switch"""
from fastapi import APIRouter, Request, HTTPException, Header, Response, status
from typing import Optional, Dict, Any
import json
import logging
import uuid
from datetime import datetime

from mtp_core.services.verification import VerificationService
from mtp_core.services.audit import AuditService
from mtp_core.services.rate_limiter import rate_limiter
from mtp_core.models.audit import AuditEventCreate, EventType, EventCategory, EventStatus
from mtp_core.core.crypto import hash_data
from mtp_core.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateway", tags=["Gateway"])
verification_service = VerificationService()
audit_service = AuditService()


def generate_request_id() -> str:
    """Generate unique request correlation ID for tracing"""
    return f"MTP-REQ-{uuid.uuid4().hex[:16].upper()}"


@router.post("/proxy")
async def proxy_request(
    request: Request,
    response: Response,
    mtp_id: str = Header(..., alias="X-MTP-ID"),
    signature: str = Header(..., alias="X-MTP-Signature"),
    timestamp: str = Header(..., alias="X-MTP-Timestamp"),
    action: Optional[str] = Header(None, alias="X-MTP-Action"),
    transaction_value: Optional[float] = Header(None, alias="X-MTP-Transaction-Value")
):
    """
    The Kill Switch.

    This endpoint intercepts ALL AI agent requests.

    Flow:
    0. Rate limit check (prevent DoS)
    1. Verify Ed25519 signature (Is this agent real?)
    2. Check agent status (Is it active?)
    3. Check mandate (Is this action allowed?)
    4. If ANY check fails → 403 Forbidden (REQUEST BLOCKED)
    5. If all checks pass → Log to audit trail → Allow request

    Headers:
        X-MTP-ID: Agent's MTP ID
        X-MTP-Signature: Ed25519 signature (base64)
        X-MTP-Timestamp: ISO timestamp
        X-MTP-Action: Action being performed (optional)
        X-MTP-Transaction-Value: Monetary value (optional)

    Response Headers:
        X-MTP-Request-ID: Unique correlation ID for tracing
        X-RateLimit-Remaining: Remaining requests in current window
        X-RateLimit-Reset: Seconds until rate limit resets

    The Pitch:
    "Mr. Banker, I can stop a rogue agent in 100 milliseconds."
    """
    # Generate request correlation ID
    request_id = generate_request_id()
    response.headers["X-MTP-Request-ID"] = request_id

    # ---- STEP 0: Rate Limit Check ----
    is_allowed, remaining, retry_after = await rate_limiter.check_rate_limit(mtp_id)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(retry_after)

    if not is_allowed:
        logger.warning(f"[{request_id}] Rate limit exceeded for {mtp_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    try:
        # Parse request body
        request_body = await request.json()
    except Exception:
        request_body = {}
    
    # ---- STEP 1: Verify Signature & Agent Status ----
    is_valid, error_msg, agent = await verification_service.verify_request(
        mtp_id=mtp_id,
        signature=signature,
        timestamp=timestamp,
        request_body=request_body
    )
    
    if not is_valid:
        logger.warning(f"[{request_id}] Request BLOCKED for {mtp_id}: {error_msg}")

        # Log blocked attempt
        await audit_service.log_event(AuditEventCreate(
            mtp_id=mtp_id,
            event_type=EventType.POLICY_VIOLATION,
            event_category=EventCategory.SECURITY,
            action_description=f"Request blocked: {error_msg}",
            input_hash=hash_data(json.dumps(request_body).encode()),
            output_hash=hash_data(b"BLOCKED"),
            status=EventStatus.BLOCKED,
            session_id=request_id,
            error_details={"reason": error_msg, "request_id": request_id}
        ))

        # Use 401 for identity failures, 403 for authorization failures
        status_code = status.HTTP_401_UNAUTHORIZED if "not found" in error_msg or "Invalid signature" in error_msg else status.HTTP_403_FORBIDDEN

        raise HTTPException(
            status_code=status_code,
            detail=f"Request blocked: {error_msg}"
        )
    
    # ---- STEP 2: Check Mandate ----
    if action:
        is_allowed, violation_reason = await verification_service.check_mandate(
            agent=agent,
            action=action,
            transaction_value=transaction_value
        )
        
        if not is_allowed:
            logger.warning(f"[{request_id}] Mandate violation for {mtp_id}: {violation_reason}")

            # Log mandate violation
            await audit_service.log_event(AuditEventCreate(
                mtp_id=mtp_id,
                event_type=EventType.POLICY_VIOLATION,
                event_category=EventCategory.COMPLIANCE,
                action_description=f"Mandate violation: {violation_reason}",
                input_hash=hash_data(json.dumps(request_body).encode()),
                output_hash=hash_data(b"BLOCKED"),
                status=EventStatus.BLOCKED,
                session_id=request_id,
                value_transferred=transaction_value,
                error_details={
                    "reason": violation_reason,
                    "action": action,
                    "request_id": request_id
                }
            ))

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Mandate violation: {violation_reason}"
            )
    
    # ---- STEP 3: Log Successful Request ----
    await audit_service.log_event(AuditEventCreate(
        mtp_id=mtp_id,
        event_type=EventType.DECISION,
        event_category=EventCategory.OPERATIONAL,
        action_description=action or "Request processed",
        input_hash=hash_data(json.dumps(request_body).encode()),
        output_hash=hash_data(b"SUCCESS"),
        status=EventStatus.SUCCESS,
        session_id=request_id,
        value_transferred=transaction_value
    ))

    # ---- STEP 4: Allow Request ----
    logger.info(f"[{request_id}] Request ALLOWED for {mtp_id}: {action}")

    return {
        "status": "allowed",
        "request_id": request_id,
        "mtp_id": mtp_id,
        "action": action,
        "message": "Request verified and allowed",
        "agent_trust_score": agent.trust_score
    }


@router.get("/health")
async def gateway_health():
    """Gateway health check"""
    return {
        "status": "operational",
        "service": "MTP Gateway",
        "description": "The Kill Switch is active"
    }
