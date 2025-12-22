"""Identity API - Agent Registration & Management"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone

from mtp_core.models.identity import (
    Agent,
    AgentRegistration,
    AgentVerification,
    AgentStatus,
    Organization,
    Supervisor
)
from mtp_core.core.crypto import generate_mtp_id
from mtp_core.services.verification import VerificationService
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/identity", tags=["Identity"])
verification_service = VerificationService()


@router.post("/agents/register", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(registration: AgentRegistration):
    """
    Register a new AI agent.
    
    This is the entry point into MTP.
    The agent provides its Ed25519 public key.
    We generate the MTP ID and register it.
    
    CRITICAL: We never hold the private key. The agent holds it.
    We only verify signatures. This is zero-liability key management.
    """
    # Generate MTP ID
    mtp_id = generate_mtp_id(registration.org_id, registration.agent_type)
    agent_id = str(uuid.uuid4())
    
    # Verify organization exists
    async with db_pool.acquire() as conn:
        org_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM organizations WHERE id = $1)",
            uuid.UUID(registration.org_id)
        )
        if not org_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization {registration.org_id} not found"
            )
        
        # Verify supervisor exists
        supervisor_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM supervisors WHERE id = $1)",
            uuid.UUID(registration.supervisor_id)
        )
        if not supervisor_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supervisor {registration.supervisor_id} not found"
            )
        
        # Insert agent
        await conn.execute(
            """
            INSERT INTO agents (
                id, mtp_id, agent_type, base_model, model_version_hash,
                org_id, department, supervisor_id, jurisdiction,
                public_key_hex, authorized_actions, prohibited_actions,
                transaction_limit_daily, status, trust_score, registered_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            uuid.UUID(agent_id),
            mtp_id,
            registration.agent_type,
            registration.base_model,
            registration.model_version_hash,
            uuid.UUID(registration.org_id),
            registration.department,
            uuid.UUID(registration.supervisor_id),
            registration.jurisdiction,
            registration.public_key_hex,
            registration.authorized_actions,
            registration.prohibited_actions,
            registration.transaction_limit_daily,
            AgentStatus.PENDING.value,
            500,  # Default trust score
            datetime.now(timezone.utc)
        )
    
    logger.info(f"Agent registered: {mtp_id} ({registration.agent_type})")
    
    return Agent(
        id=agent_id,
        mtp_id=mtp_id,
        agent_type=registration.agent_type,
        base_model=registration.base_model,
        model_version_hash=registration.model_version_hash,
        org_id=registration.org_id,
        department=registration.department,
        supervisor_id=registration.supervisor_id,
        jurisdiction=registration.jurisdiction,
        public_key_hex=registration.public_key_hex,
        authorized_actions=registration.authorized_actions,
        prohibited_actions=registration.prohibited_actions,
        transaction_limit_daily=registration.transaction_limit_daily,
        status=AgentStatus.PENDING,
        trust_score=500,
        registered_at=datetime.now(timezone.utc)
    )


@router.get("/agents/{mtp_id}", response_model=Agent)
async def get_agent(mtp_id: str):
    """Get agent details by MTP ID"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM agents WHERE mtp_id = $1",
            mtp_id
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {mtp_id} not found"
            )
        
        return Agent(
            id=str(row['id']),
            mtp_id=row['mtp_id'],
            agent_type=row['agent_type'],
            base_model=row['base_model'],
            model_version_hash=row['model_version_hash'],
            org_id=str(row['org_id']),
            department=row['department'],
            supervisor_id=str(row['supervisor_id']),
            jurisdiction=row['jurisdiction'],
            public_key_hex=row['public_key_hex'],
            authorized_actions=row['authorized_actions'],
            prohibited_actions=row['prohibited_actions'],
            transaction_limit_daily=float(row['transaction_limit_daily']),
            status=AgentStatus(row['status']),
            trust_score=row['trust_score'],
            registered_at=row['registered_at'],
            last_verified_at=row['last_verified_at'],
            activated_at=row['activated_at'],
            blockchain_tx_hash=row['blockchain_tx_hash']
        )


@router.put("/agents/{mtp_id}/status")
async def update_agent_status(mtp_id: str, new_status: AgentStatus):
    """
    Update agent status (ACTIVATE, PAUSE, SUSPEND, etc.)
    
    This is the control lever. If an agent goes rogue:
    1. Set status to SUSPENDED
    2. All future requests are blocked by the Gateway
    3. Agent is instantly neutralized
    """
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE agents SET status = $1 WHERE mtp_id = $2",
            new_status.value,
            mtp_id
        )
        
        if result == "UPDATE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {mtp_id} not found"
            )
    
    logger.info(f"Agent {mtp_id} status updated to {new_status.value}")
    
    return {
        "mtp_id": mtp_id,
        "status": new_status.value,
        "message": f"Agent status updated to {new_status.value}"
    }


@router.get("/agents/{mtp_id}/verification", response_model=AgentVerification)
async def verify_agent(mtp_id: str):
    """
    Check agent verification status.
    
    This is what external systems call to verify:
    - Is this agent active?
    - What's its trust score?
    - What can it do?
    """
    verification = await verification_service.get_agent_verification(mtp_id)
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {mtp_id} not found"
        )
    
    return verification


# ---- Organization Management ----

@router.post("/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(org: Organization):
    """Create a new organization"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO organizations (
                id, legal_name, registration_number, jurisdiction,
                kyb_status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            uuid.UUID(org.id),
            org.legal_name,
            org.registration_number,
            org.jurisdiction,
            org.kyb_status.value,
            org.created_at
        )
    
    logger.info(f"Organization created: {org.legal_name} ({org.id})")
    return org


@router.post("/supervisors", response_model=Supervisor, status_code=status.HTTP_201_CREATED)
async def create_supervisor(supervisor: Supervisor):
    """Create a new supervisor"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO supervisors (
                id, org_id, full_name, email, role_title,
                authority_scope, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            uuid.UUID(supervisor.id),
            uuid.UUID(supervisor.org_id),
            supervisor.full_name,
            supervisor.email,
            supervisor.role_title,
            supervisor.authority_scope,
            supervisor.created_at
        )
    
    logger.info(f"Supervisor created: {supervisor.full_name} ({supervisor.id})")
    return supervisor
