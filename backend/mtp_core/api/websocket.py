"""
MTP WebSocket API Endpoints
Real-time updates via WebSocket connections
"""
import uuid
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from datetime import datetime, timezone

from mtp_core.services.websocket import ws_manager, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None)
):
    """
    WebSocket connection endpoint for real-time updates

    Query Parameters:
        client_id: Optional client identifier (auto-generated if not provided)
        user_id: Optional authenticated user ID
        org_id: Optional organization ID for org-wide events

    Message Protocol:
        Client -> Server:
            {"action": "subscribe", "mtp_id": "MTP-xxx", "event_types": ["audit_event"]}
            {"action": "unsubscribe", "mtp_id": "MTP-xxx"}
            {"action": "ping"}

        Server -> Client:
            {"type": "connected", "client_id": "xxx", "timestamp": "..."}
            {"type": "audit_event", "data": {...}, "timestamp": "..."}
            {"type": "trust_score_update", "data": {...}, "timestamp": "..."}
            {"type": "pong", "timestamp": "..."}
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"ws-{uuid.uuid4().hex[:12]}"

    # Connect the client
    client = await ws_manager.connect(
        websocket=websocket,
        client_id=client_id,
        user_id=user_id,
        org_id=org_id
    )

    try:
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                await handle_client_message(client_id, data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": EventType.ERROR,
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        await ws_manager.disconnect(client_id)


async def handle_client_message(client_id: str, data: dict):
    """
    Handle incoming message from WebSocket client

    Supported actions:
        - subscribe: Subscribe to agent or event type updates
        - unsubscribe: Unsubscribe from updates
        - ping: Keep-alive ping
    """
    action = data.get("action")

    if action == "subscribe":
        mtp_id = data.get("mtp_id")
        event_types = data.get("event_types", [])

        await ws_manager.subscribe(
            client_id=client_id,
            mtp_id=mtp_id,
            event_types=event_types
        )

        # Send confirmation
        client = ws_manager._clients.get(client_id)
        if client:
            await client.websocket.send_json({
                "type": "subscribed",
                "mtp_id": mtp_id,
                "event_types": event_types,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    elif action == "unsubscribe":
        mtp_id = data.get("mtp_id")
        event_types = data.get("event_types", [])

        await ws_manager.unsubscribe(
            client_id=client_id,
            mtp_id=mtp_id,
            event_types=event_types
        )

        # Send confirmation
        client = ws_manager._clients.get(client_id)
        if client:
            await client.websocket.send_json({
                "type": "unsubscribed",
                "mtp_id": mtp_id,
                "event_types": event_types,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    elif action == "ping":
        # Respond with pong for keep-alive
        client = ws_manager._clients.get(client_id)
        if client:
            await client.websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    else:
        # Unknown action
        client = ws_manager._clients.get(client_id)
        if client:
            await client.websocket.send_json({
                "type": EventType.ERROR,
                "message": f"Unknown action: {action}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })


@router.get("/status")
async def websocket_status():
    """
    Get WebSocket connection status

    Returns:
        Connected client count and other stats
    """
    return {
        "connected_clients": ws_manager.get_connected_count(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
