"""PostgreSQL Database Connection and Schema"""
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import logging

from mtp_core.core.config import settings

logger = logging.getLogger(__name__)


class DatabasePool:
    """PostgreSQL connection pool manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize the connection pool"""
        if self.pool is None:
            try:
                # Parse asyncpg URL (remove +asyncpg suffix)
                db_url = settings.postgres_url.replace("postgresql+asyncpg://", "postgresql://")
                
                self.pool = await asyncpg.create_pool(
                    db_url,
                    min_size=5,
                    max_size=settings.postgres_pool_size,
                    command_timeout=60
                )
                logger.info("PostgreSQL connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise
    
    async def disconnect(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            yield connection


# Global database pool instance
db_pool = DatabasePool()


async def init_db():
    """Initialize database schema"""
    await db_pool.connect()
    
    async with db_pool.acquire() as conn:
        # Create TimescaleDB extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        
        # Organizations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY,
                legal_name VARCHAR(256) NOT NULL,
                registration_number VARCHAR(64) NOT NULL UNIQUE,
                jurisdiction VARCHAR(8) NOT NULL,
                kyb_status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
                kyb_verified_at TIMESTAMP,
                insurance_policy_ref VARCHAR(128),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        
        # Supervisors table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS supervisors (
                id UUID PRIMARY KEY,
                org_id UUID NOT NULL REFERENCES organizations(id),
                full_name VARCHAR(256) NOT NULL,
                email VARCHAR(256) NOT NULL,
                role_title VARCHAR(128) NOT NULL,
                authority_scope JSONB DEFAULT '{}',
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        
        # Agents table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY,
                mtp_id VARCHAR(64) NOT NULL UNIQUE,
                agent_type VARCHAR(32) NOT NULL,
                base_model VARCHAR(128) NOT NULL,
                model_version_hash VARCHAR(64),
                org_id UUID NOT NULL REFERENCES organizations(id),
                department VARCHAR(128),
                supervisor_id UUID NOT NULL REFERENCES supervisors(id),
                jurisdiction VARCHAR(8) NOT NULL,
                public_key_hex TEXT NOT NULL,
                authorized_actions JSONB DEFAULT '[]',
                prohibited_actions JSONB DEFAULT '[]',
                transaction_limit_daily DECIMAL(18, 2) DEFAULT 0.0,
                status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
                trust_score INTEGER DEFAULT 500 CHECK (trust_score >= 0 AND trust_score <= 1000),
                registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
                last_verified_at TIMESTAMP,
                activated_at TIMESTAMP,
                blockchain_tx_hash VARCHAR(128),
                UNIQUE(public_key_hex)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_mtp_id ON agents(mtp_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_org_id ON agents(org_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);")
        
        # Audit Events table (TimescaleDB hypertable)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id UUID PRIMARY KEY,
                mtp_id VARCHAR(64) NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                event_type VARCHAR(32) NOT NULL,
                event_category VARCHAR(32) NOT NULL,
                action_description TEXT NOT NULL,
                input_hash VARCHAR(64) NOT NULL,
                output_hash VARCHAR(64) NOT NULL,
                tool_calls JSONB DEFAULT '[]',
                triggering_entity VARCHAR(256),
                session_id VARCHAR(64),
                environment VARCHAR(16) DEFAULT 'production',
                status VARCHAR(16) NOT NULL,
                affected_parties JSONB DEFAULT '[]',
                value_transferred DECIMAL(18, 2),
                error_details JSONB,
                merkle_root VARCHAR(64),
                block_reference BIGINT,
                anchored_at TIMESTAMPTZ
            )
        """)
        
        # Convert to TimescaleDB hypertable
        try:
            await conn.execute("""
                SELECT create_hypertable('audit_events', 'timestamp',
                    if_not_exists => TRUE,
                    migrate_data => TRUE
                )
            """)
            logger.info("TimescaleDB hypertable created for audit_events")
        except Exception as e:
            logger.warning(f"Hypertable creation skipped (may already exist): {e}")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_mtp_id ON audit_events(mtp_id, timestamp DESC);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_merkle_root ON audit_events(merkle_root);")
        
        # Mandates table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mandates (
                id UUID PRIMARY KEY,
                mtp_id VARCHAR(64) NOT NULL REFERENCES agents(mtp_id),
                max_transaction_value DECIMAL(18, 2) DEFAULT 0.0,
                daily_transaction_limit DECIMAL(18, 2) DEFAULT 0.0,
                monthly_transaction_limit DECIMAL(18, 2) DEFAULT 0.0,
                allowed_actions JSONB DEFAULT '[]',
                forbidden_actions JSONB DEFAULT '[]',
                operating_hours JSONB,
                allowed_days JSONB,
                min_trust_score_required INTEGER DEFAULT 0,
                requires_human_approval_above DECIMAL(18, 2),
                escalation_contact VARCHAR(256),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Merkle Batches table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS merkle_batches (
                batch_id UUID PRIMARY KEY,
                merkle_root VARCHAR(64) NOT NULL UNIQUE,
                event_ids JSONB NOT NULL,
                event_count INTEGER NOT NULL,
                blockchain_tx_hash VARCHAR(128) NOT NULL,
                block_number BIGINT NOT NULL,
                anchored_at TIMESTAMP NOT NULL DEFAULT NOW(),
                ipfs_uri TEXT
            )
        """)
        
        # Disputes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS disputes (
                id UUID PRIMARY KEY,
                dispute_number VARCHAR(64) NOT NULL UNIQUE,
                complainant_type VARCHAR(32) NOT NULL,
                complainant_identifier VARCHAR(256) NOT NULL,
                respondent_mtp_id VARCHAR(64) NOT NULL,
                respondent_org_id UUID NOT NULL REFERENCES organizations(id),
                incident_timestamp TIMESTAMPTZ NOT NULL,
                incident_description TEXT NOT NULL,
                incident_category VARCHAR(64) NOT NULL,
                claimed_damages DECIMAL(18, 2) DEFAULT 0.0,
                currency VARCHAR(8) DEFAULT 'ZAR',
                related_event_ids JSONB DEFAULT '[]',
                complainant_evidence JSONB DEFAULT '{}',
                respondent_evidence JSONB DEFAULT '{}',
                status VARCHAR(32) NOT NULL DEFAULT 'FILED',
                finding VARCHAR(32),
                finding_details TEXT,
                remedy_ordered JSONB,
                trust_score_impact INTEGER DEFAULT 0,
                filed_at TIMESTAMP NOT NULL DEFAULT NOW(),
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                insurance_claim_ref VARCHAR(128),
                insurance_payout DECIMAL(18, 2)
            )
        """)
        
        logger.info("Database schema initialized successfully")
