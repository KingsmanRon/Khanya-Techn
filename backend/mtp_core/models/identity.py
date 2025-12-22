"""Identity Data Models - Agent, Organization, Supervisor"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class AgentStatus(str, Enum):
    """Agent operational status"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    DECOMMISSIONED = "DECOMMISSIONED"


class KYBStatus(str, Enum):
    """KYB verification status"""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class Organization(BaseModel):
    """Organization deploying AI agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    legal_name: str = Field(..., max_length=256)
    registration_number: str = Field(..., max_length=64)
    jurisdiction: str = Field(..., max_length=8)  # e.g., ZA-GP, EU-DE
    kyb_status: KYBStatus = KYBStatus.PENDING
    kyb_verified_at: Optional[datetime] = None
    insurance_policy_ref: Optional[str] = Field(None, max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "legal_name": "First National Bank of South Africa",
                "registration_number": "1929/001225/06",
                "jurisdiction": "ZA-GP",
                "kyb_status": "VERIFIED"
            }
        }


class Supervisor(BaseModel):
    """Human supervisor responsible for AI agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str
    full_name: str = Field(..., max_length=256)
    email: str = Field(..., max_length=256)
    role_title: str = Field(..., max_length=128)
    authority_scope: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Dr. Sarah Mthembu",
                "email": "s.mthembu@fnb.co.za",
                "role_title": "Head of AI Risk & Compliance",
                "authority_scope": {
                    "departments": ["Customer Service", "Fraud Detection"],
                    "max_agents": 100
                }
            }
        }


class Agent(BaseModel):
    """AI Agent Identity Record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mtp_id: str  # Globally unique MTP identifier (MTP-{org_hash}-{random})
    agent_type: str = Field(..., max_length=32)  # e.g., LLM, trading_bot
    base_model: str = Field(..., max_length=128)  # e.g., Claude 3.5, GPT-4
    model_version_hash: Optional[str] = Field(None, max_length=64)
    
    # Ownership & Accountability
    org_id: str
    department: Optional[str] = Field(None, max_length=128)
    supervisor_id: str
    jurisdiction: str = Field(..., max_length=8)
    
    # Cryptographic Identity (Ed25519)
    public_key_hex: str = Field(..., description="Ed25519 public key (hex-encoded)")
    
    # Mandate & Authorization
    authorized_actions: List[str] = Field(default_factory=list)
    prohibited_actions: List[str] = Field(default_factory=list)
    transaction_limit_daily: float = Field(default=0.0)
    
    # Status & Metrics
    status: AgentStatus = AgentStatus.PENDING
    trust_score: int = Field(default=500, ge=0, le=1000)  # 0-1000
    
    # Timestamps
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    # Blockchain Anchoring
    blockchain_tx_hash: Optional[str] = None  # Base L2 registration tx
    
    class Config:
        json_schema_extra = {
            "example": {
                "mtp_id": "MTP-a3f5b2-7k9m2p",
                "agent_type": "customer_service_llm",
                "base_model": "Claude 3.5 Sonnet",
                "org_id": "uuid-of-org",
                "supervisor_id": "uuid-of-supervisor",
                "jurisdiction": "ZA-GP",
                "public_key_hex": "a4b2c1d3...",
                "authorized_actions": [
                    "query_account_balance",
                    "transfer_funds",
                    "send_notification"
                ],
                "transaction_limit_daily": 10000.0
            }
        }


class AgentRegistration(BaseModel):
    """Request payload for agent registration"""
    agent_type: str = Field(..., max_length=32)
    base_model: str = Field(..., max_length=128)
    model_version_hash: Optional[str] = None
    
    org_id: str
    department: Optional[str] = None
    supervisor_id: str
    jurisdiction: str = Field(..., max_length=8)
    
    public_key_hex: str = Field(..., description="Ed25519 public key")
    
    authorized_actions: List[str] = Field(default_factory=list)
    prohibited_actions: List[str] = Field(default_factory=list)
    transaction_limit_daily: float = Field(default=0.0)


class AgentVerification(BaseModel):
    """Agent verification response"""
    mtp_id: str
    is_active: bool
    trust_score: int
    public_key_hex: str
    transaction_limit_daily: float
    authorized_actions: List[str]
    prohibited_actions: List[str]
    blockchain_verified: bool
