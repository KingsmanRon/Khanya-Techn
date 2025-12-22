"""Audit Event Data Models - TimescaleDB Schema"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Type of audit event"""
    TRANSACTION = "TRANSACTION"
    DECISION = "DECISION"
    COMMUNICATION = "COMMUNICATION"
    ERROR = "ERROR"
    ESCALATION = "ESCALATION"
    TOOL_CALL = "TOOL_CALL"
    POLICY_VIOLATION = "POLICY_VIOLATION"


class EventCategory(str, Enum):
    """Category of audit event"""
    FINANCIAL = "FINANCIAL"
    CUSTOMER = "CUSTOMER"
    OPERATIONAL = "OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"
    SECURITY = "SECURITY"


class EventStatus(str, Enum):
    """Outcome status of the event"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"


class AuditEvent(BaseModel):
    """
    Audit Event - The Black Box Record.
    
    Every action by an AI agent is logged here.
    This is stored in TimescaleDB for time-series queries.
    Events are batched into Merkle trees and anchored to Base L2.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mtp_id: str = Field(..., description="Agent MTP ID")
    
    # Temporal Data
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Event Classification
    event_type: EventType
    event_category: EventCategory
    action_description: str = Field(..., description="Human-readable action description")
    
    # Input/Output Tracking
    input_hash: str = Field(..., description="SHA-256 hash of inputs")
    output_hash: str = Field(..., description="SHA-256 hash of outputs")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Context
    triggering_entity: Optional[str] = None  # user_id, system, etc.
    session_id: Optional[str] = None
    environment: str = Field(default="production")  # production, staging, test
    
    # Outcome
    status: EventStatus = EventStatus.SUCCESS
    affected_parties: List[str] = Field(default_factory=list)
    value_transferred: Optional[float] = None  # Monetary value
    error_details: Optional[Dict[str, Any]] = None
    
    # Blockchain Anchoring
    merkle_root: Optional[str] = None  # Populated when batched
    block_reference: Optional[int] = None  # Blockchain block number
    anchored_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "mtp_id": "MTP-a3f5b2-7k9m2p",
                "event_type": "TRANSACTION",
                "event_category": "FINANCIAL",
                "action_description": "Transfer R500 from Account A to Account B",
                "input_hash": "8a3f5b2c1d...",
                "output_hash": "2d1c5b3f8a...",
                "tool_calls": [
                    {"tool": "transfer_funds", "params": {"amount": 500}}
                ],
                "status": "SUCCESS",
                "value_transferred": 500.0
            }
        }


class AuditEventCreate(BaseModel):
    """Request payload for logging an audit event"""
    mtp_id: str
    event_type: EventType
    event_category: EventCategory
    action_description: str
    input_hash: str
    output_hash: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    triggering_entity: Optional[str] = None
    session_id: Optional[str] = None
    environment: str = "production"
    status: EventStatus = EventStatus.SUCCESS
    affected_parties: List[str] = Field(default_factory=list)
    value_transferred: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None


class MerkleBatch(BaseModel):
    """Batch of audit events anchored to blockchain"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    merkle_root: str
    event_ids: List[str]
    event_count: int
    
    # Blockchain Anchoring
    blockchain_tx_hash: str
    block_number: int
    anchored_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Storage
    ipfs_uri: Optional[str] = None  # IPFS/Arweave URI for full event data
