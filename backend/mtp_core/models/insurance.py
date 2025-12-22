"""Insurance & Dispute Data Models"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class RiskTier(str, Enum):
    """Risk classification tiers"""
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    VERY_HIGH_RISK = "VERY_HIGH_RISK"


class DisputeStatus(str, Enum):
    """Dispute lifecycle status"""
    FILED = "FILED"
    INVESTIGATING = "INVESTIGATING"
    PENDING_RESPONSE = "PENDING_RESPONSE"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    APPEALED = "APPEALED"
    CLOSED = "CLOSED"


class RiskProfile(BaseModel):
    """
    Agent Risk Profile - The Insurance Trap.
    
    This data is sold to insurance companies for underwriting.
    It allows insurers to price AI agent liability policies accurately.
    """
    mtp_id: str
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Agent Characteristics
    agent_type: str
    base_model: str
    jurisdiction: str
    
    # Activity Metrics
    total_events: int = 0
    total_transactions: int = 0
    total_value_transferred: float = 0.0
    
    # Performance Metrics
    success_rate: float = 0.0  # 0.0 - 1.0
    error_rate: float = 0.0
    average_transaction_value: float = 0.0
    
    # Trust & Compliance
    current_trust_score: int
    trust_score_history: List[int] = Field(default_factory=list)
    policy_violations: int = 0
    disputes_filed: int = 0
    disputes_resolved_favorably: int = 0
    
    # Risk Assessment
    risk_tier: RiskTier = RiskTier.MEDIUM_RISK
    risk_score: float = 0.5  # 0.0 (lowest) to 1.0 (highest)
    risk_factors: Dict[str, Any] = Field(default_factory=dict)
    
    # Financial Exposure
    max_potential_loss: float = 0.0
    recommended_coverage: float = 0.0


class Dispute(BaseModel):
    """
    Dispute Record - When Things Go Wrong.
    
    This is the paper trail for liability claims.
    Immutable audit events + blockchain anchoring = courtroom evidence.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dispute_number: str  # e.g., DISP-2025-001234
    
    # Parties
    complainant_type: str  # e.g., "customer", "regulator", "internal"
    complainant_identifier: str
    respondent_mtp_id: str  # The agent being disputed
    respondent_org_id: str
    
    # Incident Details
    incident_timestamp: datetime
    incident_description: str
    incident_category: str  # e.g., "unauthorized_transaction", "incorrect_information"
    
    # Financial Impact
    claimed_damages: float = 0.0
    currency: str = "ZAR"
    
    # Evidence
    related_event_ids: List[str] = Field(default_factory=list)
    complainant_evidence: Dict[str, Any] = Field(default_factory=dict)
    respondent_evidence: Dict[str, Any] = Field(default_factory=dict)
    
    # Resolution
    status: DisputeStatus = DisputeStatus.FILED
    finding: Optional[str] = None  # "UPHELD", "DISMISSED", "PARTIAL"
    finding_details: Optional[str] = None
    remedy_ordered: Optional[Dict[str, Any]] = None
    trust_score_impact: int = 0  # Penalty to trust score
    
    # Timestamps
    filed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Insurance
    insurance_claim_ref: Optional[str] = None
    insurance_payout: Optional[float] = None
