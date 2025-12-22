"""Verification Service - Ed25519 Signature Verification + Mandate Enforcement"""
import json
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import logging

from mtp_core.core.crypto import verify_signature, hash_data
from mtp_core.core.config import settings
from mtp_core.models.identity import Agent, AgentVerification, AgentStatus
from mtp_core.models.mandate import Mandate, PolicyViolation
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class VerificationService:
    """
    The Enforcement Engine.
    
    This service is the Kill Switch. It verifies:
    1. Agent identity (Ed25519 signature)
    2. Agent status (is it active?)
    3. Mandate compliance (is this action allowed?)
    
    If ANY check fails, the request is BLOCKED (403 Forbidden).
    """
    
    async def verify_request(
        self,
        mtp_id: str,
        signature: str,
        timestamp: str,
        request_body: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Agent]]:
        """
        Verify an incoming request from an AI agent.
        
        Args:
            mtp_id: Agent's MTP ID
            signature: Base64-encoded Ed25519 signature
            timestamp: ISO timestamp of the request
            request_body: The request payload
        
        Returns:
            (is_valid, error_message, agent)
        """
        # 1. Retrieve agent from database
        agent = await self._get_agent(mtp_id)
        if not agent:
            return False, f"Agent {mtp_id} not found", None
        
        # 2. Check agent status
        if agent.status != AgentStatus.ACTIVE:
            return False, f"Agent {mtp_id} is {agent.status.value}, not ACTIVE", agent
        
        # 3. Verify timestamp freshness (prevent replay attacks)
        try:
            request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            time_diff = abs((current_time - request_time).total_seconds())
            
            if time_diff > settings.signature_validity_seconds:
                return False, "Request timestamp expired (>5 minutes old)", agent
        except Exception as e:
            return False, f"Invalid timestamp format: {e}", agent
        
        # 4. Verify Ed25519 signature
        message = self._construct_message(mtp_id, timestamp, request_body)
        is_signature_valid = verify_signature(
            public_key_hex=agent.public_key_hex,
            message=message,
            signature_b64=signature
        )
        
        if not is_signature_valid:
            logger.warning(f"Invalid signature for agent {mtp_id}")
            return False, "Invalid signature", agent
        
        # 5. All checks passed
        return True, None, agent
    
    async def check_mandate(
        self,
        agent: Agent,
        action: str,
        transaction_value: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an action violates the agent's mandate.
        
        Args:
            agent: The agent attempting the action
            action: The action name (e.g., "transfer_funds")
            transaction_value: Monetary value of the action
        
        Returns:
            (is_allowed, violation_reason)
        """
        # Check prohibited actions
        if action in agent.prohibited_actions:
            return False, f"Action '{action}' is prohibited"
        
        # Check authorized actions (if list is non-empty, action must be in it)
        if agent.authorized_actions and action not in agent.authorized_actions:
            return False, f"Action '{action}' is not authorized"
        
        # Check transaction limits
        if transaction_value is not None:
            if transaction_value > agent.transaction_limit_daily:
                return False, f"Transaction value {transaction_value} exceeds daily limit {agent.transaction_limit_daily}"
        
        # Check trust score (simple threshold for now)
        if agent.trust_score < 300:  # Minimum trust score
            return False, f"Trust score too low ({agent.trust_score}/1000)"
        
        # Fetch mandate from database for additional checks
        mandate = await self._get_mandate(agent.mtp_id)
        if mandate and mandate.is_active:
            # Check additional mandate constraints
            if transaction_value and mandate.max_transaction_value > 0:
                if transaction_value > mandate.max_transaction_value:
                    return False, f"Transaction exceeds mandate limit {mandate.max_transaction_value}"
            
            if mandate.min_trust_score_required > 0:
                if agent.trust_score < mandate.min_trust_score_required:
                    return False, f"Trust score {agent.trust_score} below required {mandate.min_trust_score_required}"
        
        return True, None
    
    async def get_agent_verification(self, mtp_id: str) -> Optional[AgentVerification]:
        """
        Get agent verification details for external queries.
        
        Args:
            mtp_id: Agent's MTP ID
        
        Returns:
            AgentVerification object or None
        """
        agent = await self._get_agent(mtp_id)
        if not agent:
            return None
        
        return AgentVerification(
            mtp_id=agent.mtp_id,
            is_active=(agent.status == AgentStatus.ACTIVE),
            trust_score=agent.trust_score,
            public_key_hex=agent.public_key_hex,
            transaction_limit_daily=agent.transaction_limit_daily,
            authorized_actions=agent.authorized_actions,
            prohibited_actions=agent.prohibited_actions,
            blockchain_verified=(agent.blockchain_tx_hash is not None)
        )
    
    # ---- Private Methods ----
    
    @staticmethod
    def _construct_message(mtp_id: str, timestamp: str, request_body: Dict[str, Any]) -> bytes:
        """
        Construct the canonical message for signature verification.
        
        Format: MTP_ID|TIMESTAMP|REQUEST_BODY_JSON
        """
        body_json = json.dumps(request_body, sort_keys=True)
        message_str = f"{mtp_id}|{timestamp}|{body_json}"
        return message_str.encode('utf-8')
    
    async def _get_agent(self, mtp_id: str) -> Optional[Agent]:
        """Retrieve agent from database"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agents WHERE mtp_id = $1",
                mtp_id
            )
            if not row:
                return None
            
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
    
    async def _get_mandate(self, mtp_id: str) -> Optional[Mandate]:
        """Retrieve active mandate for an agent"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mandates WHERE mtp_id = $1 AND is_active = TRUE ORDER BY created_at DESC LIMIT 1",
                mtp_id
            )
            if not row:
                return None
            
            return Mandate(
                id=str(row['id']),
                mtp_id=row['mtp_id'],
                max_transaction_value=float(row['max_transaction_value']),
                daily_transaction_limit=float(row['daily_transaction_limit']),
                monthly_transaction_limit=float(row['monthly_transaction_limit']),
                allowed_actions=row['allowed_actions'],
                forbidden_actions=row['forbidden_actions'],
                operating_hours=row['operating_hours'],
                allowed_days=row['allowed_days'],
                min_trust_score_required=row['min_trust_score_required'],
                requires_human_approval_above=float(row['requires_human_approval_above']) if row['requires_human_approval_above'] else None,
                escalation_contact=row['escalation_contact'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                is_active=row['is_active']
            )
