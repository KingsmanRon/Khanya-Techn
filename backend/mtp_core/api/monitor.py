"""
MTP-MONITOR API Endpoints
Alerts, metrics, and monitoring status
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel

from mtp_core.services.monitor import mtp_monitor, AlertSeverity

router = APIRouter(prefix="/v1/monitor", tags=["Monitor"])


class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    type: str
    severity: str
    title: str
    message: str
    mtp_id: Optional[str]
    org_id: Optional[str]
    data: dict
    created_at: str
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[str]


class AcknowledgeRequest(BaseModel):
    """Acknowledge alert request"""
    acknowledged_by: str


class MetricsResponse(BaseModel):
    """Metrics response model"""
    timestamp: str
    websocket_clients: int
    batch_processor_running: bool
    pending_events: int
    active_alerts: int
    alert_counts: dict


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    mtp_id: Optional[str] = Query(None, description="Filter by agent MTP ID"),
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return")
):
    """
    Get alerts with optional filtering

    - **mtp_id**: Filter by agent MTP ID
    - **org_id**: Filter by organization ID
    - **severity**: Filter by severity (info, warning, critical, emergency)
    - **acknowledged**: Filter by acknowledged status
    - **limit**: Maximum number of alerts to return (default: 100)
    """
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity. Must be one of: {[s.value for s in AlertSeverity]}"
            )

    alerts = mtp_monitor.get_alerts(
        mtp_id=mtp_id,
        org_id=org_id,
        severity=severity_enum,
        acknowledged=acknowledged,
        limit=limit
    )

    return [
        AlertResponse(
            id=a.id,
            type=a.type.value,
            severity=a.severity.value,
            title=a.title,
            message=a.message,
            mtp_id=a.mtp_id,
            org_id=a.org_id,
            data=a.data,
            created_at=a.created_at.isoformat(),
            acknowledged=a.acknowledged,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None
        )
        for a in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """
    Get a specific alert by ID
    """
    alerts = mtp_monitor.get_alerts()
    alert = next((a for a in alerts if a.id == alert_id), None)

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        id=alert.id,
        type=alert.type.value,
        severity=alert.severity.value,
        title=alert.title,
        message=alert.message,
        mtp_id=alert.mtp_id,
        org_id=alert.org_id,
        data=alert.data,
        created_at=alert.created_at.isoformat(),
        acknowledged=alert.acknowledged,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
    )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AcknowledgeRequest):
    """
    Acknowledge an alert

    - **alert_id**: The alert ID to acknowledge
    - **acknowledged_by**: User ID acknowledging the alert
    """
    success = await mtp_monitor.acknowledge_alert(
        alert_id=alert_id,
        acknowledged_by=request.acknowledged_by
    )

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_by": request.acknowledged_by,
        "acknowledged_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current monitoring metrics

    Returns system health metrics including:
    - WebSocket connection count
    - Batch processor status
    - Pending events count
    - Alert counts by severity
    """
    metrics = mtp_monitor.get_metrics()

    return MetricsResponse(
        timestamp=metrics.get("timestamp", datetime.now(timezone.utc).isoformat()),
        websocket_clients=metrics.get("websocket_clients", 0),
        batch_processor_running=metrics.get("batch_processor_running", False),
        pending_events=metrics.get("pending_events", 0),
        active_alerts=metrics.get("active_alerts", 0),
        alert_counts=metrics.get("alert_counts", {})
    )


@router.get("/status")
async def get_monitor_status():
    """
    Get monitoring service status

    Returns the overall status of the monitoring service
    """
    metrics = mtp_monitor.get_metrics()

    return {
        "status": "operational",
        "monitoring_active": mtp_monitor._running,
        "rules_count": len(mtp_monitor._rules),
        "rules": [
            {
                "name": r.name,
                "description": r.description,
                "enabled": r.enabled,
                "severity": r.severity.value
            }
            for r in mtp_monitor._rules.values()
        ],
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def monitor_health():
    """
    Health check for the monitoring service

    Returns a simple health status for load balancers
    """
    return {
        "healthy": mtp_monitor._running,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
