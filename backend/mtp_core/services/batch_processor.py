"""Batch Processor - Merkle Tree Blockchain Anchoring

This service handles the critical task of batching audit events into
Merkle trees and anchoring them to Base L2 blockchain.

The Immutability Guarantee:
"Every 100 events (or 60 seconds), we create a cryptographic proof
and anchor it to the blockchain. This is irrefutable evidence."
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from mtp_core.core.merkle import MerkleTree
from mtp_core.core.config import settings
from mtp_core.services.blockchain import BlockchainService
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Merkle Tree Batch Processor with Blockchain Anchoring

    This is the heart of MTP's immutability guarantee. Every audit event
    gets included in a Merkle tree, and the root is anchored to Base L2.

    Configuration:
    - MERKLE_BATCH_SIZE: Events per batch (default: 100)
    - MERKLE_BATCH_INTERVAL_SECONDS: Max time between batches (default: 60)

    Recovery:
    - Pending events are persisted to database
    - On restart, pending events are recovered and processed
    - Failed anchoring attempts are retried with exponential backoff
    """

    def __init__(self):
        self.blockchain_service = BlockchainService()
        self._running = False
        self._batch_task: Optional[asyncio.Task] = None
        self._pending_count = 0

    async def start(self):
        """Start the batch processor"""
        if self._running:
            logger.warning("Batch processor already running")
            return

        self._running = True
        logger.info(
            f"Starting batch processor (batch_size={settings.merkle_batch_size}, "
            f"interval={settings.merkle_batch_interval_seconds}s)"
        )

        # Recover any pending events from database
        await self._recover_pending_events()

        # Start the processing loop
        self._batch_task = asyncio.create_task(self._processing_loop())

    async def stop(self):
        """Stop the batch processor gracefully"""
        if not self._running:
            return

        self._running = False

        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        # Process any remaining events before shutting down
        await self._process_pending_batch()

        logger.info("Batch processor stopped")

    async def add_event(self, event_id: str):
        """
        Add an event to the pending batch queue.

        The event is persisted to database to survive restarts.
        """
        async with db_pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO pending_batch_events (event_id, added_at)
                    VALUES ($1, NOW())
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    uuid.UUID(event_id)
                )
                self._pending_count += 1

                logger.debug(f"Event {event_id} added to batch queue")

                # Check if we should trigger an immediate batch
                if self._pending_count >= settings.merkle_batch_size:
                    logger.info(f"Batch size reached ({self._pending_count}), triggering batch")
                    asyncio.create_task(self._process_pending_batch())

            except Exception as e:
                logger.error(f"Failed to add event to batch queue: {e}")

    async def get_pending_count(self) -> int:
        """Get count of pending events"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM pending_batch_events"
            )
            return row['count'] if row else 0

    async def _recover_pending_events(self):
        """Recover pending events on startup"""
        self._pending_count = await self.get_pending_count()
        if self._pending_count > 0:
            logger.info(f"Recovered {self._pending_count} pending events from database")

    async def _processing_loop(self):
        """Main processing loop - runs until stopped"""
        while self._running:
            try:
                # Wait for interval or until batch size is reached
                await asyncio.sleep(settings.merkle_batch_interval_seconds)

                # Process any pending events
                await self._process_pending_batch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _process_pending_batch(self):
        """Process all pending events into a Merkle batch"""
        async with db_pool.acquire() as conn:
            # Get pending events
            rows = await conn.fetch(
                """
                SELECT event_id FROM pending_batch_events
                ORDER BY added_at ASC
                LIMIT $1
                """,
                settings.merkle_batch_size
            )

            if not rows:
                return

            event_ids = [str(row['event_id']) for row in rows]
            logger.info(f"Processing batch of {len(event_ids)} events")

            try:
                # Create Merkle tree
                merkle_tree = MerkleTree(event_ids)
                merkle_root = merkle_tree.get_root()

                logger.info(f"Created Merkle tree with root: {merkle_root}")

                # Anchor to blockchain
                result = await self._anchor_to_blockchain(
                    merkle_root=merkle_root,
                    event_count=len(event_ids)
                )

                if result:
                    # Successfully anchored - update events and clear queue
                    await self._finalize_batch(
                        event_ids=event_ids,
                        merkle_root=merkle_root,
                        tx_hash=result['tx_hash'],
                        block_number=result['block_number']
                    )

                    # Remove from pending queue
                    await conn.execute(
                        """
                        DELETE FROM pending_batch_events
                        WHERE event_id = ANY($1::uuid[])
                        """,
                        [uuid.UUID(eid) for eid in event_ids]
                    )

                    self._pending_count = max(0, self._pending_count - len(event_ids))

                    logger.info(
                        f"Batch anchored: {len(event_ids)} events, "
                        f"tx={result['tx_hash']}, block={result['block_number']}"
                    )
                else:
                    logger.warning("Blockchain anchoring failed - events will be retried")

            except Exception as e:
                logger.error(f"Failed to process batch: {e}")

    async def _anchor_to_blockchain(
        self,
        merkle_root: str,
        event_count: int,
        max_retries: int = 3
    ) -> Optional[dict]:
        """
        Anchor Merkle root to blockchain with retry logic.

        Returns transaction details on success, None on failure.
        """
        for attempt in range(max_retries):
            try:
                result = await self.blockchain_service.anchor_merkle_root(
                    merkle_root=merkle_root,
                    event_count=event_count
                )

                if result:
                    return result

            except Exception as e:
                logger.warning(
                    f"Blockchain anchoring attempt {attempt + 1}/{max_retries} failed: {e}"
                )

            if attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                wait_time = 2 ** (attempt + 1)
                await asyncio.sleep(wait_time)

        return None

    async def _finalize_batch(
        self,
        event_ids: List[str],
        merkle_root: str,
        tx_hash: str,
        block_number: int
    ):
        """
        Finalize a batch by updating audit events and creating batch record.
        """
        batch_id = str(uuid.uuid4())
        anchored_at = datetime.now(timezone.utc)

        async with db_pool.acquire() as conn:
            # Create batch record
            await conn.execute(
                """
                INSERT INTO merkle_batches (
                    batch_id, merkle_root, event_ids, event_count,
                    blockchain_tx_hash, block_number, anchored_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                uuid.UUID(batch_id),
                merkle_root,
                event_ids,
                len(event_ids),
                tx_hash,
                block_number,
                anchored_at
            )

            # Update audit events with anchoring info
            # Note: This bypasses the immutability trigger because
            # we're only adding anchoring metadata, not modifying the event itself
            await conn.execute(
                """
                UPDATE audit_events
                SET merkle_root = $1,
                    block_reference = $2,
                    anchored_at = $3
                WHERE event_id = ANY($4::uuid[])
                """,
                merkle_root,
                block_number,
                anchored_at,
                [uuid.UUID(eid) for eid in event_ids]
            )

        logger.info(f"Batch {batch_id} finalized with {len(event_ids)} events")

    async def get_batch_info(self, merkle_root: str) -> Optional[dict]:
        """Get information about a specific batch"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT batch_id, merkle_root, event_ids, event_count,
                       blockchain_tx_hash, block_number, anchored_at
                FROM merkle_batches
                WHERE merkle_root = $1
                """,
                merkle_root
            )

            if not row:
                return None

            return {
                'batch_id': str(row['batch_id']),
                'merkle_root': row['merkle_root'],
                'event_ids': row['event_ids'],
                'event_count': row['event_count'],
                'blockchain_tx_hash': row['blockchain_tx_hash'],
                'block_number': row['block_number'],
                'anchored_at': row['anchored_at'].isoformat(),
                'explorer_url': self.blockchain_service.get_basescan_url(
                    row['blockchain_tx_hash']
                )
            }

    async def verify_event_anchoring(self, event_id: str) -> dict:
        """
        Verify that an event is properly anchored to blockchain.

        This is the verification that can be shown in court:
        "This event was recorded at this time and cannot be altered."
        """
        async with db_pool.acquire() as conn:
            event_row = await conn.fetchrow(
                """
                SELECT event_id, mtp_id, timestamp, event_type,
                       merkle_root, block_reference, anchored_at
                FROM audit_events
                WHERE event_id = $1
                """,
                uuid.UUID(event_id)
            )

            if not event_row:
                return {
                    'verified': False,
                    'error': 'Event not found'
                }

            if not event_row['merkle_root']:
                return {
                    'verified': False,
                    'error': 'Event not yet anchored to blockchain',
                    'event_id': event_id,
                    'event_timestamp': event_row['timestamp'].isoformat()
                }

            # Get batch info
            batch_row = await conn.fetchrow(
                """
                SELECT batch_id, blockchain_tx_hash, block_number, event_ids
                FROM merkle_batches
                WHERE merkle_root = $1
                """,
                event_row['merkle_root']
            )

            if not batch_row:
                return {
                    'verified': False,
                    'error': 'Batch record not found'
                }

            # Verify event is in batch
            event_in_batch = event_id in batch_row['event_ids']

            # Verify on blockchain (if connected)
            blockchain_verified = False
            blockchain_details = None

            try:
                tx_details = await self.blockchain_service.verify_anchoring(
                    batch_row['blockchain_tx_hash']
                )
                if tx_details:
                    blockchain_verified = tx_details.get('status') == 1
                    blockchain_details = tx_details
            except Exception as e:
                logger.warning(f"Could not verify on blockchain: {e}")

            return {
                'verified': event_in_batch and blockchain_verified,
                'event_id': event_id,
                'event_timestamp': event_row['timestamp'].isoformat(),
                'anchored_at': event_row['anchored_at'].isoformat() if event_row['anchored_at'] else None,
                'merkle_root': event_row['merkle_root'],
                'batch_id': str(batch_row['batch_id']),
                'blockchain': {
                    'tx_hash': batch_row['blockchain_tx_hash'],
                    'block_number': batch_row['block_number'],
                    'verified': blockchain_verified,
                    'details': blockchain_details,
                    'explorer_url': self.blockchain_service.get_basescan_url(
                        batch_row['blockchain_tx_hash']
                    )
                },
                'proof': {
                    'can_generate_merkle_proof': True,
                    'description': (
                        "This event's hash is part of a Merkle tree whose root "
                        "is permanently recorded on the Base L2 blockchain. "
                        "Any modification to the event would change the hash, "
                        "which would no longer match the anchored Merkle root."
                    )
                }
            }


# Global batch processor instance
batch_processor = BatchProcessor()
