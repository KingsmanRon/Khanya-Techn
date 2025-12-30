"""
MTP WebSocket Manager
Real-time updates for audit events, trust scores, and kill switch alerts
"""
import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """WebSocket event types"""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Audit events
    AUDIT_EVENT = "audit_event"
    AUDIT_BATCH_ANCHORED = "audit_batch_anchored"

    # Trust events
    TRUST_SCORE_UPDATE = "trust_score_update"
    TRUST_THRESHOLD_ALERT = "trust_threshold_alert"

    # Kill Switch events
    AGENT_SUSPENDED = "agent_suspended"
    AGENT_ACTIVATED = "agent_activated"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"

    # Certification events
    CERTIFICATION_GRANTED = "certification_granted"
    CERTIFICATION_REVOKED = "certification_revoked"

    # Dispute events
    DISPUTE_FILED = "dispute_filed"
    DISPUTE_RESOLVED = "dispute_resolved"

    # System events
    SYSTEM_ALERT = "system_alert"
    METRICS_UPDATE = "metrics_update"


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client"""
    websocket: WebSocket
    client_id: str
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events to connected clients.
    Supports:
    - Multiple concurrent connections
    - Subscription-based filtering (by MTP ID, org, event type)
    - Automatic reconnection handling
    - Broadcast to all or targeted clients
    """

    def __init__(self):
        # client_id -> WebSocketClient
        self._clients: Dict[str, WebSocketClient] = {}
        # mtp_id -> set of client_ids subscribed to this agent
        self._agent_subscriptions: Dict[str, Set[str]] = {}
        # org_id -> set of client_ids subscribed to this org
        self._org_subscriptions: Dict[str, Set[str]] = {}
        # event_type -> set of client_ids subscribed to this event type
        self._event_subscriptions: Dict[EventType, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> WebSocketClient:
        """
        Accept a new WebSocket connection

        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for this client
            user_id: Optional authenticated user ID
            org_id: Optional organization ID for filtering
        """
        await websocket.accept()

        async with self._lock:
            client = WebSocketClient(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
                org_id=org_id
            )
            self._clients[client_id] = client

            # Auto-subscribe to org events if org_id provided
            if org_id:
                if org_id not in self._org_subscriptions:
                    self._org_subscriptions[org_id] = set()
                self._org_subscriptions[org_id].add(client_id)

        logger.info(f"WebSocket client connected: {client_id} (user: {user_id}, org: {org_id})")

        # Send welcome message
        await self._send_to_client(client_id, {
            "type": EventType.CONNECTED,
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to MTP real-time updates"
        })

        return client

    async def disconnect(self, client_id: str):
        """
        Handle client disconnection

        Args:
            client_id: The client to disconnect
        """
        async with self._lock:
            if client_id not in self._clients:
                return

            client = self._clients[client_id]

            # Remove from all subscription sets
            for agent_id, subscribers in self._agent_subscriptions.items():
                subscribers.discard(client_id)

            if client.org_id:
                if client.org_id in self._org_subscriptions:
                    self._org_subscriptions[client.org_id].discard(client_id)

            for event_type, subscribers in self._event_subscriptions.items():
                subscribers.discard(client_id)

            del self._clients[client_id]

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe(
        self,
        client_id: str,
        mtp_id: Optional[str] = None,
        event_types: Optional[list] = None
    ):
        """
        Subscribe a client to specific agents or event types

        Args:
            client_id: The client subscribing
            mtp_id: Optional MTP ID to subscribe to
            event_types: Optional list of event types to subscribe to
        """
        async with self._lock:
            if client_id not in self._clients:
                return

            client = self._clients[client_id]

            if mtp_id:
                if mtp_id not in self._agent_subscriptions:
                    self._agent_subscriptions[mtp_id] = set()
                self._agent_subscriptions[mtp_id].add(client_id)
                client.subscriptions.add(f"agent:{mtp_id}")

            if event_types:
                for event_type in event_types:
                    try:
                        et = EventType(event_type)
                        if et not in self._event_subscriptions:
                            self._event_subscriptions[et] = set()
                        self._event_subscriptions[et].add(client_id)
                        client.subscriptions.add(f"event:{event_type}")
                    except ValueError:
                        logger.warning(f"Unknown event type: {event_type}")

        logger.debug(f"Client {client_id} subscribed to mtp_id={mtp_id}, events={event_types}")

    async def unsubscribe(
        self,
        client_id: str,
        mtp_id: Optional[str] = None,
        event_types: Optional[list] = None
    ):
        """
        Unsubscribe a client from specific agents or event types
        """
        async with self._lock:
            if client_id not in self._clients:
                return

            client = self._clients[client_id]

            if mtp_id and mtp_id in self._agent_subscriptions:
                self._agent_subscriptions[mtp_id].discard(client_id)
                client.subscriptions.discard(f"agent:{mtp_id}")

            if event_types:
                for event_type in event_types:
                    try:
                        et = EventType(event_type)
                        if et in self._event_subscriptions:
                            self._event_subscriptions[et].discard(client_id)
                        client.subscriptions.discard(f"event:{event_type}")
                    except ValueError:
                        pass

    async def broadcast(self, event: Dict[str, Any]):
        """
        Broadcast an event to all connected clients

        Args:
            event: The event data to broadcast
        """
        async with self._lock:
            client_ids = list(self._clients.keys())

        for client_id in client_ids:
            await self._send_to_client(client_id, event)

    async def broadcast_to_agent_subscribers(
        self,
        mtp_id: str,
        event: Dict[str, Any]
    ):
        """
        Broadcast an event to clients subscribed to a specific agent

        Args:
            mtp_id: The agent's MTP ID
            event: The event data
        """
        async with self._lock:
            subscribers = self._agent_subscriptions.get(mtp_id, set()).copy()

        for client_id in subscribers:
            await self._send_to_client(client_id, event)

    async def broadcast_to_org(
        self,
        org_id: str,
        event: Dict[str, Any]
    ):
        """
        Broadcast an event to all clients in an organization

        Args:
            org_id: The organization ID
            event: The event data
        """
        async with self._lock:
            subscribers = self._org_subscriptions.get(org_id, set()).copy()

        for client_id in subscribers:
            await self._send_to_client(client_id, event)

    async def broadcast_to_event_subscribers(
        self,
        event_type: EventType,
        event: Dict[str, Any]
    ):
        """
        Broadcast to clients subscribed to a specific event type

        Args:
            event_type: The type of event
            event: The event data
        """
        async with self._lock:
            subscribers = self._event_subscriptions.get(event_type, set()).copy()

        for client_id in subscribers:
            await self._send_to_client(client_id, event)

    async def _send_to_client(self, client_id: str, data: Dict[str, Any]):
        """
        Send data to a specific client

        Args:
            client_id: The client to send to
            data: The data to send
        """
        async with self._lock:
            client = self._clients.get(client_id)
            if not client:
                return

        try:
            await client.websocket.send_json(data)
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            await self.disconnect(client_id)

    def get_connected_count(self) -> int:
        """Get number of connected clients"""
        return len(self._clients)

    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Get information about a connected client"""
        client = self._clients.get(client_id)
        if not client:
            return None

        return {
            "client_id": client.client_id,
            "user_id": client.user_id,
            "org_id": client.org_id,
            "subscriptions": list(client.subscriptions),
            "connected_at": client.connected_at.isoformat()
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# Event broadcast helper functions
async def broadcast_audit_event(event_data: Dict[str, Any]):
    """Broadcast a new audit event"""
    mtp_id = event_data.get("mtp_id")
    org_id = event_data.get("org_id")

    event = {
        "type": EventType.AUDIT_EVENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": event_data
    }

    # Broadcast to all, agent subscribers, and org
    await ws_manager.broadcast_to_event_subscribers(EventType.AUDIT_EVENT, event)
    if mtp_id:
        await ws_manager.broadcast_to_agent_subscribers(mtp_id, event)
    if org_id:
        await ws_manager.broadcast_to_org(org_id, event)


async def broadcast_trust_update(mtp_id: str, old_score: int, new_score: int, org_id: Optional[str] = None):
    """Broadcast a trust score update"""
    event = {
        "type": EventType.TRUST_SCORE_UPDATE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "mtp_id": mtp_id,
            "old_score": old_score,
            "new_score": new_score,
            "change": new_score - old_score
        }
    }

    await ws_manager.broadcast_to_event_subscribers(EventType.TRUST_SCORE_UPDATE, event)
    await ws_manager.broadcast_to_agent_subscribers(mtp_id, event)
    if org_id:
        await ws_manager.broadcast_to_org(org_id, event)

    # Check for threshold alert
    if new_score < 300 and old_score >= 300:
        alert = {
            "type": EventType.TRUST_THRESHOLD_ALERT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "mtp_id": mtp_id,
                "score": new_score,
                "threshold": 300,
                "message": f"Agent {mtp_id} trust score dropped below critical threshold"
            }
        }
        await ws_manager.broadcast(alert)


async def broadcast_kill_switch(mtp_id: str, reason: str, triggered_by: str, org_id: Optional[str] = None):
    """Broadcast a kill switch activation"""
    event = {
        "type": EventType.KILL_SWITCH_TRIGGERED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "mtp_id": mtp_id,
            "reason": reason,
            "triggered_by": triggered_by
        }
    }

    # Kill switch is critical - broadcast to all
    await ws_manager.broadcast(event)


async def broadcast_batch_anchored(batch_id: str, merkle_root: str, tx_hash: str, event_count: int):
    """Broadcast when a batch is anchored to blockchain"""
    event = {
        "type": EventType.AUDIT_BATCH_ANCHORED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "batch_id": batch_id,
            "merkle_root": merkle_root,
            "tx_hash": tx_hash,
            "event_count": event_count
        }
    }

    await ws_manager.broadcast_to_event_subscribers(EventType.AUDIT_BATCH_ANCHORED, event)


async def broadcast_metrics_update(metrics: Dict[str, Any]):
    """Broadcast system metrics update"""
    event = {
        "type": EventType.METRICS_UPDATE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": metrics
    }

    await ws_manager.broadcast_to_event_subscribers(EventType.METRICS_UPDATE, event)
