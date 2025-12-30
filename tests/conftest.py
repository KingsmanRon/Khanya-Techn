"""
Pytest Configuration and Fixtures for MTP Tests
"""
import pytest
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_agent_data():
    """Sample agent data for tests"""
    from mtp_core.core.crypto import generate_keypair
    private_key, public_key = generate_keypair()

    return {
        "private_key": private_key,
        "public_key": public_key,
        "agent_type": "llm_agent",
        "base_model": "Claude 3.5 Sonnet",
        "org_id": "test-org-123",
        "supervisor_id": "supervisor-001",
        "jurisdiction": "ZA-GP",
        "authorized_actions": ["query", "transfer"],
        "prohibited_actions": ["delete"],
        "transaction_limit_daily": 10000.0
    }


@pytest.fixture
def sample_audit_event():
    """Sample audit event for tests"""
    from datetime import datetime, timezone

    return {
        "mtp_id": "MTP-abc123-def456",
        "action": "transfer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": "a" * 64,
        "output_hash": "b" * 64,
        "decision": "ALLOW",
        "latency_ms": 45
    }


@pytest.fixture
def sample_merkle_leaves():
    """Sample Merkle tree leaves for tests"""
    from mtp_core.core.crypto import hash_data

    return [hash_data(f"event_{i}".encode()) for i in range(100)]


@pytest.fixture
def mock_db():
    """Mock database connection"""
    from unittest.mock import AsyncMock

    db = AsyncMock()
    db.execute = AsyncMock(return_value=None)
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])

    return db


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    from unittest.mock import AsyncMock

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)

    return redis


@pytest.fixture
def mock_blockchain():
    """Mock blockchain service"""
    from unittest.mock import AsyncMock

    blockchain = AsyncMock()
    blockchain.anchor_merkle_root = AsyncMock(return_value="0x" + "a" * 64)
    blockchain.verify_on_chain = AsyncMock(return_value=True)

    return blockchain
