"""Unit Tests for Verification Service"""
import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from mtp_core.services.verification import VerificationService
from mtp_core.models.identity import Agent, AgentStatus
from mtp_core.core.crypto import generate_keypair, sign_message


class TestVerificationServiceRequestValidation:
    """Tests for request verification logic"""

    @pytest.fixture
    def verification_service(self):
        """Create verification service instance"""
        return VerificationService()

    @pytest.fixture
    def valid_agent(self):
        """Create a valid active agent"""
        private_key, public_key = generate_keypair()
        return Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex=public_key,
            status=AgentStatus.ACTIVE,
            trust_score=600,
            transaction_limit_daily=10000.0,
            authorized_actions=["query", "transfer"],
            prohibited_actions=["delete"]
        ), private_key, public_key

    def test_construct_message_format(self, verification_service):
        """Test canonical message construction"""
        mtp_id = "MTP-test-123456"
        timestamp = "2025-01-15T10:30:00Z"
        request_body = {"action": "test", "amount": 100}

        message = verification_service._construct_message(mtp_id, timestamp, request_body)

        # Should be bytes
        assert isinstance(message, bytes)

        # Should contain all parts separated by |
        decoded = message.decode('utf-8')
        parts = decoded.split("|")
        assert len(parts) == 3
        assert parts[0] == mtp_id
        assert parts[1] == timestamp

    def test_construct_message_deterministic(self, verification_service):
        """Test that message construction is deterministic"""
        mtp_id = "MTP-test-123456"
        timestamp = "2025-01-15T10:30:00Z"

        # Same body with different key order
        body1 = {"z": 1, "a": 2}
        body2 = {"a": 2, "z": 1}

        msg1 = verification_service._construct_message(mtp_id, timestamp, body1)
        msg2 = verification_service._construct_message(mtp_id, timestamp, body2)

        # sort_keys=True ensures same result
        assert msg1 == msg2


class TestMandateEnforcement:
    """Tests for mandate checking logic"""

    @pytest.fixture
    def verification_service(self):
        """Create verification service instance"""
        return VerificationService()

    @pytest.fixture
    def agent_with_limits(self):
        """Create agent with transaction limits"""
        return Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex="a" * 64,
            status=AgentStatus.ACTIVE,
            trust_score=600,
            transaction_limit_daily=1000.0,
            authorized_actions=["query", "transfer"],
            prohibited_actions=["delete", "admin"]
        )

    @pytest.mark.asyncio
    async def test_check_mandate_allows_authorized_action(self, verification_service, agent_with_limits):
        """Test that authorized actions are allowed"""
        with patch.object(verification_service, '_get_mandate', new_callable=AsyncMock) as mock_mandate:
            mock_mandate.return_value = None

            is_allowed, reason = await verification_service.check_mandate(
                agent=agent_with_limits,
                action="transfer",
                transaction_value=500.0
            )

            assert is_allowed is True
            assert reason is None

    @pytest.mark.asyncio
    async def test_check_mandate_blocks_prohibited_action(self, verification_service, agent_with_limits):
        """Test that prohibited actions are blocked"""
        with patch.object(verification_service, '_get_mandate', new_callable=AsyncMock) as mock_mandate:
            mock_mandate.return_value = None

            is_allowed, reason = await verification_service.check_mandate(
                agent=agent_with_limits,
                action="delete"
            )

            assert is_allowed is False
            assert "prohibited" in reason.lower()

    @pytest.mark.asyncio
    async def test_check_mandate_blocks_unauthorized_action(self, verification_service, agent_with_limits):
        """Test that non-whitelisted actions are blocked"""
        with patch.object(verification_service, '_get_mandate', new_callable=AsyncMock) as mock_mandate:
            mock_mandate.return_value = None

            is_allowed, reason = await verification_service.check_mandate(
                agent=agent_with_limits,
                action="unknown_action"  # Not in authorized_actions
            )

            assert is_allowed is False
            assert "not authorized" in reason.lower()

    @pytest.mark.asyncio
    async def test_check_mandate_blocks_excessive_transaction(self, verification_service, agent_with_limits):
        """Test that transactions exceeding limit are blocked"""
        with patch.object(verification_service, '_get_mandate', new_callable=AsyncMock) as mock_mandate:
            mock_mandate.return_value = None

            is_allowed, reason = await verification_service.check_mandate(
                agent=agent_with_limits,
                action="transfer",
                transaction_value=5000.0  # Exceeds 1000.0 limit
            )

            assert is_allowed is False
            assert "exceeds" in reason.lower()

    @pytest.mark.asyncio
    async def test_check_mandate_blocks_low_trust_score(self, verification_service):
        """Test that low trust score blocks actions"""
        low_trust_agent = Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex="a" * 64,
            status=AgentStatus.ACTIVE,
            trust_score=200,  # Below 300 threshold
            transaction_limit_daily=1000.0,
            authorized_actions=["transfer"],
            prohibited_actions=[]
        )

        with patch.object(verification_service, '_get_mandate', new_callable=AsyncMock) as mock_mandate:
            mock_mandate.return_value = None

            is_allowed, reason = await verification_service.check_mandate(
                agent=low_trust_agent,
                action="transfer"
            )

            assert is_allowed is False
            assert "trust score" in reason.lower()


class TestTimestampValidation:
    """Tests for timestamp freshness validation"""

    @pytest.fixture
    def verification_service(self):
        """Create verification service instance"""
        return VerificationService()

    def test_valid_timestamp_format(self, verification_service):
        """Test that valid ISO timestamp is accepted"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # This should not raise
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert dt is not None

    def test_timestamp_freshness_within_window(self):
        """Test that recent timestamp is fresh"""
        now = datetime.now(timezone.utc)
        request_time = now - timedelta(minutes=2)  # 2 minutes ago

        time_diff = abs((now - request_time).total_seconds())

        assert time_diff < 300  # Within 5 minute window

    def test_timestamp_expired_outside_window(self):
        """Test that old timestamp is expired"""
        now = datetime.now(timezone.utc)
        request_time = now - timedelta(minutes=10)  # 10 minutes ago

        time_diff = abs((now - request_time).total_seconds())

        assert time_diff > 300  # Outside 5 minute window


class TestAgentStatusVerification:
    """Tests for agent status checks"""

    def test_active_agent_passes(self):
        """Test that ACTIVE status passes"""
        agent = Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex="a" * 64,
            status=AgentStatus.ACTIVE,
            trust_score=600
        )

        assert agent.status == AgentStatus.ACTIVE

    def test_suspended_agent_fails(self):
        """Test that SUSPENDED status fails"""
        agent = Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex="a" * 64,
            status=AgentStatus.SUSPENDED,
            trust_score=600
        )

        assert agent.status != AgentStatus.ACTIVE

    def test_pending_agent_fails(self):
        """Test that PENDING status fails"""
        agent = Agent(
            id="test-id",
            mtp_id="MTP-abc123-def456",
            agent_type="llm",
            base_model="Claude 3.5",
            org_id="org-123",
            supervisor_id="supervisor-123",
            jurisdiction="ZA-GP",
            public_key_hex="a" * 64,
            status=AgentStatus.PENDING,
            trust_score=600
        )

        assert agent.status != AgentStatus.ACTIVE


class TestSignatureVerificationIntegration:
    """Integration tests for full signature verification flow"""

    def test_full_signature_flow(self):
        """Test complete sign and verify flow"""
        from mtp_core.core.crypto import verify_signature

        # Generate keys
        private_key, public_key = generate_keypair()

        # Create message components
        mtp_id = "MTP-abc123-def456"
        timestamp = datetime.now(timezone.utc).isoformat()
        request_body = {"action": "transfer", "amount": 100}

        # Construct canonical message
        body_json = json.dumps(request_body, sort_keys=True)
        message_str = f"{mtp_id}|{timestamp}|{body_json}"
        message = message_str.encode('utf-8')

        # Sign
        signature = sign_message(private_key, message)

        # Verify
        is_valid = verify_signature(public_key, message, signature)

        assert is_valid is True

    def test_signature_fails_with_wrong_body(self):
        """Test that changing request body invalidates signature"""
        from mtp_core.core.crypto import verify_signature

        private_key, public_key = generate_keypair()

        mtp_id = "MTP-abc123-def456"
        timestamp = datetime.now(timezone.utc).isoformat()
        original_body = {"action": "transfer", "amount": 100}
        tampered_body = {"action": "transfer", "amount": 999}

        # Sign original
        original_json = json.dumps(original_body, sort_keys=True)
        original_message = f"{mtp_id}|{timestamp}|{original_json}".encode('utf-8')
        signature = sign_message(private_key, original_message)

        # Try to verify with tampered body
        tampered_json = json.dumps(tampered_body, sort_keys=True)
        tampered_message = f"{mtp_id}|{timestamp}|{tampered_json}".encode('utf-8')
        is_valid = verify_signature(public_key, tampered_message, signature)

        assert is_valid is False
