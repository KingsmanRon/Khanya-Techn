"""Mandate & Policy Data Models"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class Mandate(BaseModel):
    """
    Agent Mandate - The Rules of Engagement.
    
    This defines what an agent can and cannot do.
    The Gateway enforces these rules in real-time.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mtp_id: str
    
    # Transaction Limits
    max_transaction_value: float = Field(default=0.0)
    daily_transaction_limit: float = Field(default=0.0)
    monthly_transaction_limit: float = Field(default=0.0)
    
    # Action Authorization
    allowed_actions: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    
    # Time-Based Restrictions
    operating_hours: Optional[Dict[str, Any]] = None  # e.g., {"start": "08:00", "end": "18:00"}
    allowed_days: Optional[List[str]] = None  # e.g., ["MON", "TUE", "WED", "THU", "FRI"]
    
    # Trust Score Requirements
    min_trust_score_required: int = Field(default=0, ge=0, le=1000)
    
    # Approval Requirements
    requires_human_approval_above: Optional[float] = None  # Transaction value threshold
    escalation_contact: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class PolicyViolation(BaseModel):
    """Record of a mandate/policy violation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mtp_id: str
    event_id: str  # Reference to the audit event
    
    violation_type: str  # e.g., "EXCEEDED_TRANSACTION_LIMIT", "UNAUTHORIZED_ACTION"
    violation_description: str
    
    attempted_action: str
    attempted_value: Optional[float] = None
    
    # Enforcement Action
    action_taken: str  # e.g., "BLOCKED", "ESCALATED", "LOGGED"
    
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
