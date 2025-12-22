"""Audit API - Query Audit Events"""
from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional
from datetime import datetime
import logging

from mtp_core.models.audit import AuditEvent, AuditEventCreate
from mtp_core.services.audit import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])
audit_service = AuditService()


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def log_event(event: AuditEventCreate):
    """
    Log an audit event.
    
    This endpoint is primarily used by MTP adapters.
    Every AI action flows through here.
    
    Returns 202 Accepted (event queued for processing).
    """
    logged_event = await audit_service.log_event(event)
    
    return {
        "status": "accepted",
        "event_id": logged_event.event_id,
        "message": "Event logged successfully"
    }


@router.get("/events/query", response_model=List[AuditEvent])
async def query_events(
    mtp_id: str = Query(..., description="Agent MTP ID"),
    start_time: Optional[str] = Query(None, description="ISO timestamp start"),
    end_time: Optional[str] = Query(None, description="ISO timestamp end"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    limit: int = Query(100, ge=1, le=1000, description="Max results")
):
    """
    Query audit events for an agent.
    
    The Forensic Query:
    "Show me everything Agent X did between 08:00 and 08:01."
    
    This is what regulators, auditors, and lawyers will use.
    TimescaleDB makes these queries fast, even with millions of events.
    """
    # Parse timestamps
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_time format. Use ISO 8601."
            )
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_time format. Use ISO 8601."
            )
    
    events = await audit_service.query_events(
        mtp_id=mtp_id,
        start_time=start_dt,
        end_time=end_dt,
        event_type=event_type,
        limit=limit
    )
    
    return events


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_event(event_id: str):
    """Get a specific audit event by ID"""
    from mtp_core.db.postgres import db_pool
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM audit_events WHERE event_id = $1",
            event_id
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        return AuditEvent(
            event_id=str(row['event_id']),
            mtp_id=row['mtp_id'],
            timestamp=row['timestamp'],
            event_type=row['event_type'],
            event_category=row['event_category'],
            action_description=row['action_description'],
            input_hash=row['input_hash'],
            output_hash=row['output_hash'],
            tool_calls=row['tool_calls'],
            triggering_entity=row['triggering_entity'],
            session_id=row['session_id'],
            environment=row['environment'],
            status=row['status'],
            affected_parties=row['affected_parties'],
            value_transferred=float(row['value_transferred']) if row['value_transferred'] else None,
            error_details=row['error_details'],
            merkle_root=row['merkle_root'],
            block_reference=row['block_reference'],
            anchored_at=row['anchored_at']
        )
