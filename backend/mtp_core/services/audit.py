"""Audit Service - Event Logging + Merkle Batching"""
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
import logging
import uuid

from mtp_core.models.audit import AuditEvent, AuditEventCreate, MerkleBatch
from mtp_core.core.merkle import MerkleTree
from mtp_core.core.config import settings
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class AuditService:
    """
    The Black Box.
    
    This service logs every AI agent action to TimescaleDB.
    Events are batched into Merkle trees and anchored to Base L2.
    
    This provides:
    1. Immutable audit trail
    2. Forensic query capability ("Show me everything Agent X did at 08:00")
    3. Blockchain proof (can verify any event in court)
    """
    
    def __init__(self):
        self._batch_queue: List[str] = []  # Event IDs waiting to be batched
        self._batching_task: Optional[asyncio.Task] = None
    
    async def log_event(self, event: AuditEventCreate) -> AuditEvent:
        """
        Log an audit event to TimescaleDB.
        
        Args:
            event: The audit event to log
        
        Returns:
            The logged AuditEvent with assigned event_id
        """
        event_id = str(uuid.uuid4())
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_events (
                    event_id, mtp_id, timestamp, event_type, event_category,
                    action_description, input_hash, output_hash, tool_calls,
                    triggering_entity, session_id, environment, status,
                    affected_parties, value_transferred, error_details
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """,
                event_id,
                event.mtp_id,
                datetime.now(timezone.utc),
                event.event_type.value,
                event.event_category.value,
                event.action_description,
                event.input_hash,
                event.output_hash,
                event.tool_calls,
                event.triggering_entity,
                event.session_id,
                event.environment,
                event.status.value,
                event.affected_parties,
                event.value_transferred,
                event.error_details
            )
        
        # Add to batch queue for Merkle anchoring
        self._batch_queue.append(event_id)
        
        # Check if we should trigger a batch
        if len(self._batch_queue) >= settings.merkle_batch_size:
            logger.info(f"Batch queue full ({len(self._batch_queue)} events), triggering batch")
            # Note: In production, this would trigger async batch processing
            # For now, we'll rely on periodic batching
        
        logger.info(f"Audit event {event_id} logged for agent {event.mtp_id}")
        
        return AuditEvent(
            event_id=event_id,
            mtp_id=event.mtp_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event.event_type,
            event_category=event.event_category,
            action_description=event.action_description,
            input_hash=event.input_hash,
            output_hash=event.output_hash,
            tool_calls=event.tool_calls,
            triggering_entity=event.triggering_entity,
            session_id=event.session_id,
            environment=event.environment,
            status=event.status,
            affected_parties=event.affected_parties,
            value_transferred=event.value_transferred,
            error_details=event.error_details
        )
    
    async def query_events(
        self,
        mtp_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Query audit events for an agent.
        
        This is the Forensic Query capability.
        "Show me everything Agent X did between 08:00 and 08:01."
        
        Args:
            mtp_id: Agent's MTP ID
            start_time: Start of time range
            end_time: End of time range
            event_type: Filter by event type
            limit: Max number of events to return
        
        Returns:
            List of AuditEvents
        """
        query = "SELECT * FROM audit_events WHERE mtp_id = $1"
        params = [mtp_id]
        param_idx = 2
        
        if start_time:
            query += f" AND timestamp >= ${param_idx}"
            params.append(start_time)
            param_idx += 1
        
        if end_time:
            query += f" AND timestamp <= ${param_idx}"
            params.append(end_time)
            param_idx += 1
        
        if event_type:
            query += f" AND event_type = ${param_idx}"
            params.append(event_type)
            param_idx += 1
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_idx}"
        params.append(limit)
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        events = []
        for row in rows:
            events.append(AuditEvent(
                event_id=str(row['event_id']),
                mtp_id=row['mtp_id'],
                timestamp=row['timestamp'],
                event_type=row['event_type'],
                event_category=row['event_category'],
                action_description=row['action_description'],
                input_hash=row['input_hash'],
                output_hash=row['output_hash'],
                tool_calls=row['tool_calls'],
                triggering_entity=row['triggering_entity'],
                session_id=row['session_id'],
                environment=row['environment'],
                status=row['status'],
                affected_parties=row['affected_parties'],
                value_transferred=float(row['value_transferred']) if row['value_transferred'] else None,
                error_details=row['error_details'],
                merkle_root=row['merkle_root'],
                block_reference=row['block_reference'],
                anchored_at=row['anchored_at']
            ))
        
        return events
    
    async def create_merkle_batch(self, event_ids: List[str]) -> Optional[MerkleTree]:
        """
        Create a Merkle tree from a batch of event IDs.
        
        Args:
            event_ids: List of event IDs to batch
        
        Returns:
            MerkleTree object or None if batch is empty
        """
        if not event_ids:
            return None
        
        # Create Merkle tree from event IDs (using event IDs as leaf hashes)
        merkle_tree = MerkleTree(event_ids)
        merkle_root = merkle_tree.get_root()
        
        logger.info(f"Created Merkle batch with {len(event_ids)} events, root: {merkle_root}")
        
        return merkle_tree
    
    async def anchor_batch(
        self,
        merkle_tree: MerkleTree,
        event_ids: List[str],
        blockchain_tx_hash: str,
        block_number: int
    ) -> MerkleBatch:
        """
        Record a Merkle batch that has been anchored to the blockchain.
        
        Args:
            merkle_tree: The Merkle tree
            event_ids: Event IDs in the batch
            blockchain_tx_hash: Transaction hash on Base L2
            block_number: Block number on Base L2
        
        Returns:
            MerkleBatch record
        """
        batch_id = str(uuid.uuid4())
        merkle_root = merkle_tree.get_root()
        anchored_at = datetime.now(timezone.utc)
        
        async with db_pool.acquire() as conn:
            # Insert batch record
            await conn.execute(
                """
                INSERT INTO merkle_batches (
                    batch_id, merkle_root, event_ids, event_count,
                    blockchain_tx_hash, block_number, anchored_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                batch_id,
                merkle_root,
                event_ids,
                len(event_ids),
                blockchain_tx_hash,
                block_number,
                anchored_at
            )
            
            # Update audit events with Merkle root and block reference
            await conn.execute(
                """
                UPDATE audit_events
                SET merkle_root = $1, block_reference = $2, anchored_at = $3
                WHERE event_id = ANY($4::uuid[])
                """,
                merkle_root,
                block_number,
                anchored_at,
                event_ids
            )
        
        logger.info(f"Anchored batch {batch_id} to blockchain at block {block_number}")
        
        return MerkleBatch(
            batch_id=batch_id,
            merkle_root=merkle_root,
            event_ids=event_ids,
            event_count=len(event_ids),
            blockchain_tx_hash=blockchain_tx_hash,
            block_number=block_number,
            anchored_at=anchored_at
        )
    
    def start_batch_processor(self):
        """Start background task for periodic Merkle batching"""
        if self._batching_task is None or self._batching_task.done():
            self._batching_task = asyncio.create_task(self._batch_processor_loop())
            logger.info("Batch processor started")
    
    async def _batch_processor_loop(self):
        """Background loop for processing Merkle batches"""
        while True:
            try:
                await asyncio.sleep(settings.merkle_batch_interval_seconds)
                
                if len(self._batch_queue) > 0:
                    logger.info(f"Processing batch of {len(self._batch_queue)} events")
                    # Note: Actual blockchain anchoring would happen here
                    # For now, we just clear the queue
                    self._batch_queue.clear()
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
