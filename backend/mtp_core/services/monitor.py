"""
MTP-MONITOR: Real-time Monitoring and Alerting Service
Monitors agent behavior, trust scores, and system health
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from mtp_core.services.websocket import (
    ws_manager,
    EventType,
    broadcast_trust_update,
    broadcast_metrics_update
)

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(str, Enum):
    """Types of alerts"""
    TRUST_SCORE_DROP = "trust_score_drop"
    TRUST_BELOW_THRESHOLD = "trust_below_threshold"
    HIGH_ERROR_RATE = "high_error_rate"
    UNUSUAL_ACTIVITY = "unusual_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"
    BATCH_ANCHOR_FAILED = "batch_anchor_failed"
    SYSTEM_HEALTH_DEGRADED = "system_health_degraded"
    AGENT_SUSPENDED = "agent_suspended"
    CERTIFICATION_EXPIRING = "certification_expiring"
    DISPUTE_FILED = "dispute_filed"


@dataclass
class Alert:
    """Represents an alert"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    mtp_id: Optional[str] = None
    org_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class MonitoringRule:
    """Defines a monitoring rule"""
    name: str
    description: str
    enabled: bool = True
    check_interval: int = 60  # seconds
    condition: Callable = None  # Function that returns (should_alert, alert_data)
    severity: AlertSeverity = AlertSeverity.WARNING
    cooldown: int = 300  # Minimum seconds between alerts


class MTPMonitor:
    """
    MTP Monitoring Service
    Continuously monitors system health and agent behavior
    """

    # Alert thresholds
    TRUST_CRITICAL_THRESHOLD = 300
    TRUST_WARNING_THRESHOLD = 500
    TRUST_DROP_ALERT_PERCENT = 10  # Alert if trust drops by this %
    ERROR_RATE_THRESHOLD = 0.1  # 10% error rate
    HIGH_LATENCY_MS = 500  # Alert if avg latency > 500ms

    def __init__(self):
        self._running = False
        self._task = None
        self._rules: Dict[str, MonitoringRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._last_alert_times: Dict[str, datetime] = {}
        self._metrics: Dict[str, Any] = {}
        self._alert_handlers: List[Callable] = []

        # Register default rules
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default monitoring rules"""
        # Trust score monitoring
        self.add_rule(MonitoringRule(
            name="trust_below_critical",
            description="Alert when agent trust score drops below critical threshold",
            check_interval=30,
            severity=AlertSeverity.CRITICAL,
            cooldown=600
        ))

        self.add_rule(MonitoringRule(
            name="trust_below_warning",
            description="Alert when agent trust score drops below warning threshold",
            check_interval=60,
            severity=AlertSeverity.WARNING,
            cooldown=900
        ))

        # System health monitoring
        self.add_rule(MonitoringRule(
            name="high_error_rate",
            description="Alert when error rate exceeds threshold",
            check_interval=60,
            severity=AlertSeverity.WARNING,
            cooldown=300
        ))

        self.add_rule(MonitoringRule(
            name="batch_anchor_health",
            description="Alert when batch anchoring fails",
            check_interval=120,
            severity=AlertSeverity.CRITICAL,
            cooldown=600
        ))

    def add_rule(self, rule: MonitoringRule):
        """Add a monitoring rule"""
        self._rules[rule.name] = rule
        logger.info(f"Added monitoring rule: {rule.name}")

    def remove_rule(self, name: str):
        """Remove a monitoring rule"""
        if name in self._rules:
            del self._rules[name]
            logger.info(f"Removed monitoring rule: {name}")

    def add_alert_handler(self, handler: Callable):
        """Add a handler to be called when alerts are generated"""
        self._alert_handlers.append(handler)

    async def start(self):
        """Start the monitoring service"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("MTP-MONITOR service started")

    async def stop(self):
        """Stop the monitoring service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MTP-MONITOR service stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Collect metrics
                await self._collect_metrics()

                # Check all rules
                for rule_name, rule in self._rules.items():
                    if rule.enabled:
                        await self._check_rule(rule)

                # Broadcast metrics update periodically
                await broadcast_metrics_update(self._metrics)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(10)  # Base loop interval

    async def _collect_metrics(self):
        """Collect system metrics"""
        from mtp_core.services.batch_processor import batch_processor

        self._metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "websocket_clients": ws_manager.get_connected_count(),
            "batch_processor_running": batch_processor._running,
            "pending_events": await batch_processor.get_pending_count(),
            "active_alerts": len([a for a in self._alerts.values() if not a.acknowledged])
        }

    async def _check_rule(self, rule: MonitoringRule):
        """Check a monitoring rule and generate alert if needed"""
        # Check cooldown
        last_alert = self._last_alert_times.get(rule.name)
        if last_alert:
            elapsed = (datetime.now(timezone.utc) - last_alert).total_seconds()
            if elapsed < rule.cooldown:
                return

        # For now, rules are checked via explicit calls to check_* methods

    async def check_trust_score(
        self,
        mtp_id: str,
        old_score: int,
        new_score: int,
        org_id: Optional[str] = None
    ):
        """
        Check trust score changes and generate alerts if needed

        Args:
            mtp_id: Agent MTP ID
            old_score: Previous trust score
            new_score: New trust score
            org_id: Optional organization ID
        """
        # Check for critical threshold
        if new_score < self.TRUST_CRITICAL_THRESHOLD and old_score >= self.TRUST_CRITICAL_THRESHOLD:
            await self._create_alert(
                type=AlertType.TRUST_BELOW_THRESHOLD,
                severity=AlertSeverity.CRITICAL,
                title="Agent Trust Below Critical Threshold",
                message=f"Agent {mtp_id} trust score dropped to {new_score}, below critical threshold of {self.TRUST_CRITICAL_THRESHOLD}",
                mtp_id=mtp_id,
                org_id=org_id,
                data={
                    "old_score": old_score,
                    "new_score": new_score,
                    "threshold": self.TRUST_CRITICAL_THRESHOLD
                }
            )

        # Check for warning threshold
        elif new_score < self.TRUST_WARNING_THRESHOLD and old_score >= self.TRUST_WARNING_THRESHOLD:
            await self._create_alert(
                type=AlertType.TRUST_BELOW_THRESHOLD,
                severity=AlertSeverity.WARNING,
                title="Agent Trust Below Warning Threshold",
                message=f"Agent {mtp_id} trust score dropped to {new_score}, below warning threshold of {self.TRUST_WARNING_THRESHOLD}",
                mtp_id=mtp_id,
                org_id=org_id,
                data={
                    "old_score": old_score,
                    "new_score": new_score,
                    "threshold": self.TRUST_WARNING_THRESHOLD
                }
            )

        # Check for significant drop
        if old_score > 0:
            drop_percent = ((old_score - new_score) / old_score) * 100
            if drop_percent >= self.TRUST_DROP_ALERT_PERCENT:
                await self._create_alert(
                    type=AlertType.TRUST_SCORE_DROP,
                    severity=AlertSeverity.WARNING,
                    title="Significant Trust Score Drop",
                    message=f"Agent {mtp_id} trust score dropped by {drop_percent:.1f}% (from {old_score} to {new_score})",
                    mtp_id=mtp_id,
                    org_id=org_id,
                    data={
                        "old_score": old_score,
                        "new_score": new_score,
                        "drop_percent": drop_percent
                    }
                )

        # Broadcast trust update via WebSocket
        await broadcast_trust_update(mtp_id, old_score, new_score, org_id)

    async def check_error_rate(
        self,
        mtp_id: str,
        success_count: int,
        error_count: int,
        time_window: int = 3600
    ):
        """
        Check agent error rate and alert if too high

        Args:
            mtp_id: Agent MTP ID
            success_count: Number of successful operations
            error_count: Number of failed operations
            time_window: Time window in seconds
        """
        total = success_count + error_count
        if total == 0:
            return

        error_rate = error_count / total

        if error_rate >= self.ERROR_RATE_THRESHOLD:
            await self._create_alert(
                type=AlertType.HIGH_ERROR_RATE,
                severity=AlertSeverity.WARNING if error_rate < 0.25 else AlertSeverity.CRITICAL,
                title="High Error Rate Detected",
                message=f"Agent {mtp_id} has {error_rate*100:.1f}% error rate in the last {time_window//60} minutes",
                mtp_id=mtp_id,
                data={
                    "error_rate": error_rate,
                    "success_count": success_count,
                    "error_count": error_count,
                    "time_window_seconds": time_window
                }
            )

    async def check_kill_switch(
        self,
        mtp_id: str,
        reason: str,
        triggered_by: str,
        org_id: Optional[str] = None
    ):
        """
        Record and alert on kill switch activation

        Args:
            mtp_id: Agent MTP ID
            reason: Reason for kill switch
            triggered_by: Who triggered the kill switch
            org_id: Optional organization ID
        """
        await self._create_alert(
            type=AlertType.KILL_SWITCH_TRIGGERED,
            severity=AlertSeverity.EMERGENCY,
            title="Kill Switch Activated",
            message=f"Kill switch triggered for agent {mtp_id}: {reason}",
            mtp_id=mtp_id,
            org_id=org_id,
            data={
                "reason": reason,
                "triggered_by": triggered_by
            }
        )

    async def check_batch_anchor_failure(self, batch_id: str, error: str):
        """Alert on batch anchoring failure"""
        await self._create_alert(
            type=AlertType.BATCH_ANCHOR_FAILED,
            severity=AlertSeverity.CRITICAL,
            title="Batch Anchoring Failed",
            message=f"Failed to anchor batch {batch_id} to blockchain: {error}",
            data={
                "batch_id": batch_id,
                "error": error
            }
        )

    async def _create_alert(
        self,
        type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        mtp_id: Optional[str] = None,
        org_id: Optional[str] = None,
        data: Dict[str, Any] = None
    ):
        """
        Create and store an alert

        Args:
            type: Alert type
            severity: Alert severity
            title: Alert title
            message: Alert message
            mtp_id: Optional agent MTP ID
            org_id: Optional organization ID
            data: Additional alert data
        """
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            type=type,
            severity=severity,
            title=title,
            message=message,
            mtp_id=mtp_id,
            org_id=org_id,
            data=data or {}
        )

        # Store alert
        self._alerts[alert.id] = alert
        self._last_alert_times[type.value] = datetime.now(timezone.utc)

        logger.warning(f"ALERT [{severity.value.upper()}] {type.value}: {message}")

        # Broadcast alert via WebSocket
        await ws_manager.broadcast({
            "type": EventType.SYSTEM_ALERT,
            "timestamp": alert.created_at.isoformat(),
            "data": {
                "id": alert.id,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "mtp_id": alert.mtp_id,
                "org_id": alert.org_id,
                "data": alert.data
            }
        })

        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                await handler(alert) if asyncio.iscoroutinefunction(handler) else handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged

        Returns:
            True if acknowledged, False if not found
        """
        if alert_id not in self._alerts:
            return False

        alert = self._alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now(timezone.utc)

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    def get_alerts(
        self,
        mtp_id: Optional[str] = None,
        org_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alerts with optional filtering

        Args:
            mtp_id: Filter by agent MTP ID
            org_id: Filter by organization ID
            severity: Filter by severity
            acknowledged: Filter by acknowledged status
            limit: Maximum number of alerts to return

        Returns:
            List of matching alerts
        """
        alerts = list(self._alerts.values())

        # Apply filters
        if mtp_id:
            alerts = [a for a in alerts if a.mtp_id == mtp_id]
        if org_id:
            alerts = [a for a in alerts if a.org_id == org_id]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        # Sort by created_at descending
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics"""
        return {
            **self._metrics,
            "alert_counts": {
                "total": len(self._alerts),
                "unacknowledged": len([a for a in self._alerts.values() if not a.acknowledged]),
                "by_severity": {
                    s.value: len([a for a in self._alerts.values() if a.severity == s])
                    for s in AlertSeverity
                }
            }
        }


# Global monitor instance
mtp_monitor = MTPMonitor()
