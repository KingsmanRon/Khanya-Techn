"""Dispute Resolution Service - MTP-RESOLVE Implementation

This service handles the formal dispute resolution process when AI agents
cause harm or fail to perform as expected.

Key Features:
1. Dispute filing and tracking
2. Evidence collection from audit trails
3. Automated resolution for clear-cut cases
4. Manual arbitration workflow for complex cases
5. Trust score impact application
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from mtp_core.models.insurance import Dispute, DisputeStatus
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class DisputeResolutionService:
    """
    MTP-RESOLVE Dispute Handler

    When AI agents go wrong, this is where accountability happens.
    Every dispute is linked to immutable audit events, creating
    courtroom-ready evidence chains.
    """

    # Auto-resolution rules for clear-cut cases
    AUTO_RESOLUTION_RULES = {
        "unauthorized_transaction": {
            "condition": "transaction outside agent mandate",
            "finding": "UPHELD",
            "remedy": {"type": "full_refund", "description": "Full refund of transaction amount"},
            "trust_impact": -50
        },
        "incorrect_information": {
            "condition": "agent provided verifiably false information",
            "finding": "UPHELD",
            "remedy": {"type": "correction", "description": "Correction + formal apology"},
            "trust_impact": -25
        },
        "service_failure": {
            "condition": "agent failed to complete authorized action",
            "finding": "UPHELD",
            "remedy": {"type": "retry_or_refund", "description": "Retry service or refund"},
            "trust_impact": -15
        },
        "delayed_response": {
            "condition": "response time exceeded SLA",
            "finding": "UPHELD",
            "remedy": {"type": "service_credit", "description": "Service credit issued"},
            "trust_impact": -5
        },
        "policy_violation": {
            "condition": "agent violated organization policy",
            "finding": "UPHELD",
            "remedy": {"type": "review_and_remediate", "description": "Policy review and remediation"},
            "trust_impact": -30
        }
    }

    async def file_dispute(
        self,
        complainant_type: str,
        complainant_identifier: str,
        respondent_mtp_id: str,
        incident_timestamp: datetime,
        incident_description: str,
        incident_category: str,
        claimed_damages: float = 0.0,
        currency: str = "ZAR",
        related_event_ids: List[str] = None,
        complainant_evidence: Dict[str, Any] = None
    ) -> Dispute:
        """
        File a new dispute against an AI agent.

        Args:
            complainant_type: Type of complainant (USER, ORGANIZATION, REGULATOR)
            complainant_identifier: Email or identifier of complainant
            respondent_mtp_id: MTP ID of the agent being disputed
            incident_timestamp: When the incident occurred
            incident_description: Detailed description of the incident
            incident_category: Category of incident
            claimed_damages: Amount of damages claimed
            currency: Currency for damages
            related_event_ids: List of audit event IDs as evidence
            complainant_evidence: Additional evidence from complainant

        Returns:
            Created Dispute record
        """
        # Get organization ID for the agent
        async with db_pool.acquire() as conn:
            agent_row = await conn.fetchrow(
                "SELECT org_id FROM agents WHERE mtp_id = $1",
                respondent_mtp_id
            )

            if not agent_row:
                raise ValueError(f"Agent not found: {respondent_mtp_id}")

            org_id = str(agent_row['org_id'])

            # Generate dispute number
            year = datetime.now().year
            count_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as count FROM disputes
                WHERE EXTRACT(YEAR FROM filed_at) = $1
                """,
                year
            )
            count = (count_row['count'] or 0) + 1
            dispute_number = f"DISP-{year}-{count:06d}"

            dispute_id = str(uuid.uuid4())

            # Insert dispute
            await conn.execute(
                """
                INSERT INTO disputes (
                    id, dispute_number, complainant_type, complainant_identifier,
                    respondent_mtp_id, respondent_org_id, incident_timestamp,
                    incident_description, incident_category, claimed_damages,
                    currency, related_event_ids, complainant_evidence, status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
                """,
                uuid.UUID(dispute_id),
                dispute_number,
                complainant_type,
                complainant_identifier,
                respondent_mtp_id,
                uuid.UUID(org_id),
                incident_timestamp,
                incident_description,
                incident_category,
                Decimal(str(claimed_damages)),
                currency,
                related_event_ids or [],
                complainant_evidence or {},
                DisputeStatus.FILED.value
            )

        logger.info(
            f"Dispute {dispute_number} filed against agent {respondent_mtp_id} "
            f"by {complainant_type} {complainant_identifier}"
        )

        # Attempt auto-resolution for clear-cut cases
        dispute = await self.get_dispute(dispute_id)
        await self._attempt_auto_resolution(dispute)

        return await self.get_dispute(dispute_id)

    async def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get a dispute by ID"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, dispute_number, complainant_type, complainant_identifier,
                       respondent_mtp_id, respondent_org_id, incident_timestamp,
                       incident_description, incident_category, claimed_damages,
                       currency, related_event_ids, complainant_evidence,
                       respondent_evidence, status, finding, finding_details,
                       remedy_ordered, trust_score_impact, filed_at,
                       acknowledged_at, resolved_at, insurance_claim_ref,
                       insurance_payout
                FROM disputes WHERE id = $1
                """,
                uuid.UUID(dispute_id)
            )

            if not row:
                return None

            return Dispute(
                id=str(row['id']),
                dispute_number=row['dispute_number'],
                complainant_type=row['complainant_type'],
                complainant_identifier=row['complainant_identifier'],
                respondent_mtp_id=row['respondent_mtp_id'],
                respondent_org_id=str(row['respondent_org_id']),
                incident_timestamp=row['incident_timestamp'],
                incident_description=row['incident_description'],
                incident_category=row['incident_category'],
                claimed_damages=float(row['claimed_damages'] or 0),
                currency=row['currency'],
                related_event_ids=row['related_event_ids'] or [],
                complainant_evidence=row['complainant_evidence'] or {},
                respondent_evidence=row['respondent_evidence'] or {},
                status=DisputeStatus(row['status']),
                finding=row['finding'],
                finding_details=row['finding_details'],
                remedy_ordered=row['remedy_ordered'],
                trust_score_impact=row['trust_score_impact'] or 0,
                filed_at=row['filed_at'],
                acknowledged_at=row['acknowledged_at'],
                resolved_at=row['resolved_at'],
                insurance_claim_ref=row['insurance_claim_ref'],
                insurance_payout=float(row['insurance_payout']) if row['insurance_payout'] else None
            )

    async def get_dispute_by_number(self, dispute_number: str) -> Optional[Dispute]:
        """Get a dispute by dispute number"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM disputes WHERE dispute_number = $1",
                dispute_number
            )
            if row:
                return await self.get_dispute(str(row['id']))
            return None

    async def list_disputes(
        self,
        mtp_id: Optional[str] = None,
        org_id: Optional[str] = None,
        status: Optional[DisputeStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dispute]:
        """List disputes with optional filters"""
        query = "SELECT id FROM disputes WHERE 1=1"
        params = []
        param_idx = 1

        if mtp_id:
            query += f" AND respondent_mtp_id = ${param_idx}"
            params.append(mtp_id)
            param_idx += 1

        if org_id:
            query += f" AND respondent_org_id = ${param_idx}"
            params.append(uuid.UUID(org_id))
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status.value)
            param_idx += 1

        query += f" ORDER BY filed_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        disputes = []
        for row in rows:
            dispute = await self.get_dispute(str(row['id']))
            if dispute:
                disputes.append(dispute)

        return disputes

    async def submit_response(
        self,
        dispute_id: str,
        respondent_evidence: Dict[str, Any],
        response_statement: str
    ) -> Dispute:
        """
        Submit a response to a dispute from the respondent organization.

        Args:
            dispute_id: Dispute ID
            respondent_evidence: Evidence from respondent
            response_statement: Official response statement

        Returns:
            Updated Dispute
        """
        async with db_pool.acquire() as conn:
            evidence = {
                **respondent_evidence,
                'response_statement': response_statement,
                'submitted_at': datetime.now(timezone.utc).isoformat()
            }

            await conn.execute(
                """
                UPDATE disputes
                SET respondent_evidence = $1,
                    status = $2,
                    acknowledged_at = NOW()
                WHERE id = $3
                """,
                evidence,
                DisputeStatus.UNDER_REVIEW.value,
                uuid.UUID(dispute_id)
            )

        logger.info(f"Response submitted for dispute {dispute_id}")
        return await self.get_dispute(dispute_id)

    async def resolve_dispute(
        self,
        dispute_id: str,
        finding: str,
        finding_details: str,
        remedy_ordered: Dict[str, Any] = None,
        trust_score_impact: int = 0,
        arbitrator_id: Optional[str] = None
    ) -> Dispute:
        """
        Resolve a dispute with a finding.

        Args:
            dispute_id: Dispute ID
            finding: Finding (UPHELD, DISMISSED, PARTIAL)
            finding_details: Detailed explanation of finding
            remedy_ordered: Remedy to be applied
            trust_score_impact: Impact to agent's trust score
            arbitrator_id: ID of arbitrator (if manual resolution)

        Returns:
            Resolved Dispute
        """
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE disputes
                SET finding = $1,
                    finding_details = $2,
                    remedy_ordered = $3,
                    trust_score_impact = $4,
                    status = $5,
                    resolved_at = NOW()
                WHERE id = $6
                """,
                finding,
                finding_details,
                remedy_ordered or {},
                trust_score_impact,
                DisputeStatus.RESOLVED.value,
                uuid.UUID(dispute_id)
            )

            # Apply trust score impact if agent found at fault
            if finding in ('UPHELD', 'PARTIAL') and trust_score_impact != 0:
                dispute = await self.get_dispute(dispute_id)
                if dispute:
                    await self._apply_trust_impact(
                        dispute.respondent_mtp_id,
                        trust_score_impact
                    )

        logger.info(
            f"Dispute {dispute_id} resolved with finding: {finding}, "
            f"trust impact: {trust_score_impact}"
        )

        return await self.get_dispute(dispute_id)

    async def appeal_dispute(
        self,
        dispute_id: str,
        appeal_reason: str,
        additional_evidence: Dict[str, Any] = None
    ) -> Dispute:
        """
        File an appeal against a dispute resolution.

        Args:
            dispute_id: Dispute ID
            appeal_reason: Reason for appeal
            additional_evidence: New evidence for appeal

        Returns:
            Updated Dispute
        """
        dispute = await self.get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute not found: {dispute_id}")

        if dispute.status != DisputeStatus.RESOLVED:
            raise ValueError("Can only appeal resolved disputes")

        # Check appeal deadline (14 days)
        if dispute.resolved_at:
            deadline = dispute.resolved_at + timedelta(days=14)
            if datetime.now(timezone.utc) > deadline:
                raise ValueError("Appeal deadline has passed (14 days)")

        async with db_pool.acquire() as conn:
            # Store appeal details in respondent_evidence
            current_evidence = dispute.respondent_evidence or {}
            current_evidence['appeal'] = {
                'reason': appeal_reason,
                'additional_evidence': additional_evidence or {},
                'filed_at': datetime.now(timezone.utc).isoformat()
            }

            await conn.execute(
                """
                UPDATE disputes
                SET status = $1,
                    respondent_evidence = $2
                WHERE id = $3
                """,
                DisputeStatus.APPEALED.value,
                current_evidence,
                uuid.UUID(dispute_id)
            )

        logger.info(f"Appeal filed for dispute {dispute_id}")
        return await self.get_dispute(dispute_id)

    async def get_audit_evidence(
        self,
        dispute_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all audit events related to a dispute.

        This provides the immutable evidence chain for arbitration.
        """
        dispute = await self.get_dispute(dispute_id)
        if not dispute or not dispute.related_event_ids:
            return []

        async with db_pool.acquire() as conn:
            # Get events by ID
            placeholders = ', '.join([f'${i+1}' for i in range(len(dispute.related_event_ids))])
            rows = await conn.fetch(
                f"""
                SELECT event_id, mtp_id, timestamp, event_type, event_category,
                       action_description, input_hash, output_hash, tool_calls,
                       status, affected_parties, value_transferred, error_details,
                       merkle_root, block_reference, anchored_at
                FROM audit_events
                WHERE event_id = ANY($1::uuid[])
                ORDER BY timestamp ASC
                """,
                [uuid.UUID(eid) for eid in dispute.related_event_ids]
            )

            events = []
            for row in rows:
                events.append({
                    'event_id': str(row['event_id']),
                    'mtp_id': row['mtp_id'],
                    'timestamp': row['timestamp'].isoformat(),
                    'event_type': row['event_type'],
                    'event_category': row['event_category'],
                    'action_description': row['action_description'],
                    'status': row['status'],
                    'value_transferred': float(row['value_transferred']) if row['value_transferred'] else None,
                    'error_details': row['error_details'],
                    'blockchain_proof': {
                        'merkle_root': row['merkle_root'],
                        'block_reference': row['block_reference'],
                        'anchored_at': row['anchored_at'].isoformat() if row['anchored_at'] else None
                    } if row['merkle_root'] else None
                })

            return events

    async def _attempt_auto_resolution(self, dispute: Dispute) -> bool:
        """
        Attempt to automatically resolve clear-cut disputes.

        Returns True if auto-resolved, False if manual review needed.
        """
        if dispute.incident_category not in self.AUTO_RESOLUTION_RULES:
            logger.info(
                f"Dispute {dispute.dispute_number} category '{dispute.incident_category}' "
                f"not auto-resolvable, requires manual review"
            )
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE disputes SET status = $1 WHERE id = $2",
                    DisputeStatus.PENDING_RESPONSE.value,
                    uuid.UUID(dispute.id)
                )
            return False

        rule = self.AUTO_RESOLUTION_RULES[dispute.incident_category]

        # Verify condition is clearly met by checking audit events
        events = await self.get_audit_evidence(dispute.id)

        if not events:
            # No evidence - can't auto-resolve
            logger.info(
                f"Dispute {dispute.dispute_number} has no linked events, "
                f"requires manual review"
            )
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE disputes SET status = $1 WHERE id = $2",
                    DisputeStatus.INVESTIGATING.value,
                    uuid.UUID(dispute.id)
                )
            return False

        # For now, auto-resolve if we have clear evidence
        # In production, this would have more sophisticated verification
        can_auto_resolve = len(events) > 0 and dispute.claimed_damages < 10000

        if can_auto_resolve:
            await self.resolve_dispute(
                dispute_id=dispute.id,
                finding=rule['finding'],
                finding_details=f"Auto-resolved: {rule['condition']}",
                remedy_ordered=rule['remedy'],
                trust_score_impact=rule['trust_impact']
            )

            logger.info(
                f"Dispute {dispute.dispute_number} auto-resolved with "
                f"finding: {rule['finding']}"
            )
            return True

        # Needs manual review
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE disputes SET status = $1 WHERE id = $2",
                DisputeStatus.PENDING_RESPONSE.value,
                uuid.UUID(dispute.id)
            )
        return False

    async def _apply_trust_impact(self, mtp_id: str, impact: int):
        """Apply trust score impact to an agent"""
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agents
                SET trust_score = GREATEST(0, LEAST(1000, trust_score + $1))
                WHERE mtp_id = $2
                """,
                impact,
                mtp_id
            )

        logger.info(f"Applied trust impact {impact} to agent {mtp_id}")


# Global service instance
dispute_service = DisputeResolutionService()
