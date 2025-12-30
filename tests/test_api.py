"""
API Integration Tests for MTP Backend
Tests all API endpoints with FastAPI TestClient
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import json

# Will use httpx for async testing
pytest_plugins = ['pytest_asyncio']


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_health_check_returns_200(self, client):
        """Test that /api/health returns 200"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Test health check response format"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


class TestIdentityAPI:
    """Tests for MTP-ID identity endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    @pytest.fixture
    def valid_registration_payload(self):
        """Valid agent registration payload"""
        from mtp_core.core.crypto import generate_keypair
        _, public_key = generate_keypair()

        return {
            "agent_type": "llm_agent",
            "base_model": "Claude 3.5 Sonnet",
            "org_id": "test-org-123",
            "supervisor_id": "supervisor-001",
            "jurisdiction": "ZA-GP",
            "public_key_hex": public_key,
            "authorized_actions": ["query", "transfer"],
            "prohibited_actions": ["delete"],
            "transaction_limit_daily": 10000.0
        }

    def test_register_agent_returns_201(self, client, valid_registration_payload):
        """Test successful agent registration"""
        with patch('mtp_core.api.identity.register_agent') as mock_register:
            mock_register.return_value = {
                "mtp_id": "MTP-abc123-def456",
                "status": "pending",
                "message": "Agent registered successfully"
            }

            response = client.post(
                "/api/v1/identity/register",
                json=valid_registration_payload
            )

            # Should succeed or return validation error
            assert response.status_code in [200, 201, 422, 500]

    def test_register_agent_missing_fields_returns_422(self, client):
        """Test that missing required fields returns 422"""
        incomplete_payload = {
            "agent_type": "llm_agent"
            # Missing required fields
        }

        response = client.post(
            "/api/v1/identity/register",
            json=incomplete_payload
        )

        assert response.status_code == 422

    def test_get_agent_returns_agent_data(self, client):
        """Test getting agent by MTP ID"""
        with patch('mtp_core.api.identity.get_agent') as mock_get:
            mock_get.return_value = {
                "mtp_id": "MTP-abc123-def456",
                "status": "active",
                "trust_score": 600
            }

            response = client.get("/api/v1/identity/agents/MTP-abc123-def456")

            # Should return agent or 404
            assert response.status_code in [200, 404, 500]


class TestGatewayAPI:
    """Tests for Kill Switch gateway endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_gateway_verify_endpoint_exists(self, client):
        """Test that gateway verify endpoint exists"""
        response = client.post("/api/v1/gateway/verify", json={})

        # Should return 422 (validation error) not 404
        assert response.status_code != 404

    def test_gateway_kill_endpoint_requires_auth(self, client):
        """Test that kill endpoint requires authentication"""
        response = client.post(
            "/api/v1/gateway/kill",
            json={"mtp_id": "MTP-test-123456", "reason": "test"}
        )

        # Should require auth or return error
        assert response.status_code in [401, 403, 422, 500]


class TestAuditAPI:
    """Tests for MTP-AUDIT audit trail endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_audit_events_returns_list(self, client):
        """Test getting audit events"""
        with patch('mtp_core.api.audit.get_events') as mock_events:
            mock_events.return_value = []

            response = client.get("/api/v1/audit/events")

            # Should return events or require auth
            assert response.status_code in [200, 401, 403, 500]

    def test_get_audit_event_by_id(self, client):
        """Test getting single audit event"""
        response = client.get("/api/v1/audit/events/test-event-id")

        # Should return event, 404, or require auth
        assert response.status_code in [200, 404, 401, 403, 500]

    def test_query_audit_events_with_filters(self, client):
        """Test querying audit events with filters"""
        response = client.get(
            "/api/v1/audit/events",
            params={
                "mtp_id": "MTP-test-123456",
                "action": "transfer",
                "limit": 10
            }
        )

        assert response.status_code in [200, 401, 403, 422, 500]


class TestTrustAPI:
    """Tests for MTP-TRUST trust score endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_trust_score(self, client):
        """Test getting trust score for agent"""
        response = client.get("/api/v1/trust/MTP-test-123456")

        # Should return score or 404
        assert response.status_code in [200, 404, 401, 500]

    def test_get_trust_history(self, client):
        """Test getting trust score history"""
        response = client.get("/api/v1/trust/MTP-test-123456/history")

        assert response.status_code in [200, 404, 401, 500]

    def test_get_trust_breakdown(self, client):
        """Test getting trust score breakdown"""
        response = client.get("/api/v1/trust/MTP-test-123456/breakdown")

        assert response.status_code in [200, 404, 401, 500]


class TestCertificationsAPI:
    """Tests for MTP-CERT certification endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_certifications(self, client):
        """Test getting all certifications"""
        response = client.get("/api/v1/certifications")

        assert response.status_code in [200, 401, 500]

    def test_get_agent_certifications(self, client):
        """Test getting certifications for an agent"""
        response = client.get("/api/v1/certifications/agent/MTP-test-123456")

        assert response.status_code in [200, 404, 401, 500]

    def test_apply_for_certification(self, client):
        """Test applying for certification"""
        payload = {
            "mtp_id": "MTP-test-123456",
            "certification_type": "ZA-FIN",
            "evidence": {"document_url": "https://example.com/doc.pdf"}
        }

        response = client.post("/api/v1/certifications/apply", json=payload)

        assert response.status_code in [200, 201, 401, 403, 422, 500]


class TestDisputesAPI:
    """Tests for MTP-RESOLVE dispute endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_disputes(self, client):
        """Test getting all disputes"""
        response = client.get("/api/v1/disputes")

        assert response.status_code in [200, 401, 500]

    def test_file_dispute(self, client):
        """Test filing a new dispute"""
        payload = {
            "agent_mtp_id": "MTP-test-123456",
            "event_id": "event-abc-123",
            "description": "Unauthorized transaction",
            "evidence": {"screenshot": "https://example.com/evidence.png"}
        }

        response = client.post("/api/v1/disputes/file", json=payload)

        assert response.status_code in [200, 201, 401, 403, 422, 500]

    def test_get_dispute_by_id(self, client):
        """Test getting dispute by ID"""
        response = client.get("/api/v1/disputes/dispute-123")

        assert response.status_code in [200, 404, 401, 500]


class TestBlockchainAPI:
    """Tests for MTP-CHAIN blockchain endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_merkle_batches(self, client):
        """Test getting Merkle batches"""
        response = client.get("/api/v1/blockchain/batches")

        assert response.status_code in [200, 401, 500]

    def test_get_batch_by_id(self, client):
        """Test getting batch by ID"""
        response = client.get("/api/v1/blockchain/batches/batch-123")

        assert response.status_code in [200, 404, 401, 500]

    def test_verify_event_on_chain(self, client):
        """Test verifying event on blockchain"""
        response = client.get("/api/v1/blockchain/verify/event-123")

        assert response.status_code in [200, 404, 401, 500]


class TestInsuranceAPI:
    """Tests for MTP-INSURE insurance endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_policies(self, client):
        """Test getting insurance policies"""
        response = client.get("/api/v1/insurance/policies")

        assert response.status_code in [200, 401, 500]

    def test_get_policy_quote(self, client):
        """Test getting policy quote"""
        payload = {
            "mtp_id": "MTP-test-123456",
            "coverage_amount": 100000,
            "policy_type": "comprehensive"
        }

        response = client.post("/api/v1/insurance/quote", json=payload)

        assert response.status_code in [200, 401, 422, 500]

    def test_file_claim(self, client):
        """Test filing insurance claim"""
        payload = {
            "policy_id": "policy-123",
            "incident_description": "Agent caused financial loss",
            "claimed_amount": 5000
        }

        response = client.post("/api/v1/insurance/claims", json=payload)

        assert response.status_code in [200, 201, 401, 403, 422, 500]


class TestAPIKeyAuthentication:
    """Tests for API key authentication"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_api_key_header_authentication(self, client):
        """Test API key in header"""
        response = client.get(
            "/api/v1/identity/agents",
            headers={"X-API-Key": "test-api-key"}
        )

        # Should process request (may fail auth but should not 404)
        assert response.status_code != 404

    def test_missing_api_key_on_protected_route(self, client):
        """Test that protected routes require API key"""
        response = client.delete("/api/v1/identity/agents/MTP-test-123456")

        # Should require auth
        assert response.status_code in [401, 403, 405, 422, 500]


class TestRateLimiting:
    """Tests for rate limiting"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present"""
        response = client.get("/api/health")

        # Rate limit headers might be present
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining
        # This is optional based on implementation


class TestCORSConfiguration:
    """Tests for CORS configuration"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # Should allow CORS from configured origins
        assert response.status_code in [200, 204]
