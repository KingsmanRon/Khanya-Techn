"""Trust Score Service - MTP-TRUST Implementation

Algorithmic trust computation based on behavioral history.
Trust scores range from 0-1000 and are composed of four weighted components.

The Trust Score:
"A single number that tells you if you can trust this AI agent."
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class TrustScoreService:
    """
    MTP-TRUST Engine

    Trust Score Components (0-1000 scale):

    RELIABILITY_SCORE (40% weight)
    - Transaction Success Rate
    - Response Time Consistency
    - Uptime/Availability
    - Error Recovery Speed

    COMPLIANCE_SCORE (25% weight)
    - Regulatory Violation Count
    - Policy Adherence Rate
    - Audit Finding Severity
    - Certification Currency

    TRANSPARENCY_SCORE (20% weight)
    - Audit Trail Completeness
    - Identity Verification Level
    - Dispute Response Quality
    - Documentation Quality

    HISTORY_SCORE (15% weight)
    - Operational Tenure
    - Transaction Volume
    - Dispute Resolution Rate
    - Endorsements from Verified Parties
    """

    # Component weights
    WEIGHTS = {
        'reliability': 0.40,
        'compliance': 0.25,
        'transparency': 0.20,
        'history': 0.15
    }

    # Score thresholds
    THRESHOLDS = {
        'EXCELLENT': 800,
        'GOOD': 650,
        'FAIR': 500,
        'POOR': 350,
        'CRITICAL': 0
    }

    # Decay rate per day of inactivity
    DECAY_RATE_PER_DAY = 0.5  # 0.5 points per day

    # Maximum decay
    MAX_DECAY = 100  # Maximum 100 points can be lost to decay

    async def calculate_trust_score(
        self,
        mtp_id: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive trust score for an agent.

        Args:
            mtp_id: Agent's MTP identifier
            lookback_days: Days of history to consider

        Returns:
            Complete trust score breakdown
        """
        logger.info(f"Calculating trust score for agent {mtp_id}")

        # Get agent info
        agent = await self._get_agent(mtp_id)
        if not agent:
            raise ValueError(f"Agent not found: {mtp_id}")

        # Calculate component scores
        reliability = await self._calculate_reliability_score(mtp_id, lookback_days)
        compliance = await self._calculate_compliance_score(mtp_id, lookback_days)
        transparency = await self._calculate_transparency_score(mtp_id, lookback_days)
        history = await self._calculate_history_score(mtp_id, agent)

        # Calculate weighted total
        total_score = int(
            reliability['score'] * self.WEIGHTS['reliability'] +
            compliance['score'] * self.WEIGHTS['compliance'] +
            transparency['score'] * self.WEIGHTS['transparency'] +
            history['score'] * self.WEIGHTS['history']
        )

        # Apply decay for inactivity
        decay = await self._calculate_decay(mtp_id, lookback_days)
        total_score = max(0, total_score - decay)

        # Determine tier
        tier = self._get_tier(total_score)

        # Store in history
        previous_score = agent.get('trust_score', 500)
        if total_score != previous_score:
            await self._record_score_change(
                mtp_id=mtp_id,
                new_score=total_score,
                previous_score=previous_score,
                components={
                    'reliability': reliability['score'],
                    'compliance': compliance['score'],
                    'transparency': transparency['score'],
                    'history': history['score'],
                    'decay': decay
                },
                reason='Scheduled recalculation'
            )

            # Update agent's trust score
            await self._update_agent_score(mtp_id, total_score)

        return {
            'mtp_id': mtp_id,
            'total_score': total_score,
            'tier': tier,
            'components': {
                'reliability': reliability,
                'compliance': compliance,
                'transparency': transparency,
                'history': history
            },
            'decay_applied': decay,
            'previous_score': previous_score,
            'change': total_score - previous_score,
            'calculated_at': datetime.now(timezone.utc).isoformat()
        }

    async def get_trust_score(self, mtp_id: str) -> Dict[str, Any]:
        """Get current trust score for an agent (quick lookup)"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT trust_score FROM agents WHERE mtp_id = $1",
                mtp_id
            )

            if not row:
                raise ValueError(f"Agent not found: {mtp_id}")

            score = row['trust_score']
            tier = self._get_tier(score)

            return {
                'mtp_id': mtp_id,
                'score': score,
                'tier': tier,
                'thresholds': self.THRESHOLDS
            }

    async def get_trust_history(
        self,
        mtp_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trust score history for an agent"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, score, score_components, change_reason,
                       previous_score, calculated_at
                FROM trust_score_history
                WHERE mtp_id = $1
                ORDER BY calculated_at DESC
                LIMIT $2
                """,
                mtp_id, limit
            )

            return [
                {
                    'id': str(row['id']),
                    'score': row['score'],
                    'components': row['score_components'],
                    'reason': row['change_reason'],
                    'previous_score': row['previous_score'],
                    'change': row['score'] - (row['previous_score'] or row['score']),
                    'calculated_at': row['calculated_at'].isoformat()
                }
                for row in rows
            ]

    async def apply_trust_impact(
        self,
        mtp_id: str,
        impact: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Apply a trust score impact (positive or negative).

        Args:
            mtp_id: Agent's MTP identifier
            impact: Points to add (positive) or subtract (negative)
            reason: Reason for the change

        Returns:
            Updated trust score info
        """
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT trust_score FROM agents WHERE mtp_id = $1",
                mtp_id
            )

            if not row:
                raise ValueError(f"Agent not found: {mtp_id}")

            current_score = row['trust_score']
            new_score = max(0, min(1000, current_score + impact))

            # Update agent
            await conn.execute(
                "UPDATE agents SET trust_score = $1 WHERE mtp_id = $2",
                new_score, mtp_id
            )

            # Record in history
            await self._record_score_change(
                mtp_id=mtp_id,
                new_score=new_score,
                previous_score=current_score,
                components={'manual_adjustment': impact},
                reason=reason
            )

            logger.info(
                f"Trust impact applied: {mtp_id} {current_score} -> {new_score} "
                f"(impact: {impact}, reason: {reason})"
            )

            return {
                'mtp_id': mtp_id,
                'previous_score': current_score,
                'new_score': new_score,
                'impact': impact,
                'reason': reason,
                'tier': self._get_tier(new_score)
            }

    async def _get_agent(self, mtp_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT mtp_id, trust_score, registered_at, status,
                       last_verified_at, activated_at
                FROM agents WHERE mtp_id = $1
                """,
                mtp_id
            )
            return dict(row) if row else None

    async def _calculate_reliability_score(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Calculate reliability component (40% weight)"""
        start_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        async with db_pool.acquire() as conn:
            # Get event statistics
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful,
                    COUNT(*) FILTER (WHERE status IN ('FAILURE', 'ERROR')) as failed,
                    AVG(CASE WHEN status = 'SUCCESS' THEN 1.0 ELSE 0.0 END) as success_rate
                FROM audit_events
                WHERE mtp_id = $1 AND timestamp >= $2
                """,
                mtp_id, start_date
            )

            total = stats['total_events'] or 0
            successful = stats['successful'] or 0
            failed = stats['failed'] or 0
            success_rate = float(stats['success_rate'] or 1.0)

            # Base score starts at 1000
            score = 1000

            # Deduct for failures
            if total > 0:
                error_rate = failed / total
                if error_rate > 0.10:  # >10% errors
                    score -= 400
                elif error_rate > 0.05:  # >5% errors
                    score -= 200
                elif error_rate > 0.02:  # >2% errors
                    score -= 100
                elif error_rate > 0.01:  # >1% errors
                    score -= 50

            # Bonus for high volume + high success
            if total > 1000 and success_rate > 0.99:
                score = min(1000, score + 50)

            return {
                'score': max(0, min(1000, score)),
                'total_events': total,
                'successful_events': successful,
                'failed_events': failed,
                'success_rate': success_rate
            }

    async def _calculate_compliance_score(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Calculate compliance component (25% weight)"""
        async with db_pool.acquire() as conn:
            # Get dispute statistics
            disputes = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_disputes,
                    COUNT(*) FILTER (WHERE finding = 'UPHELD') as at_fault,
                    COUNT(*) FILTER (WHERE finding = 'DISMISSED') as dismissed,
                    SUM(CASE WHEN finding = 'UPHELD' THEN trust_score_impact ELSE 0 END) as total_impact
                FROM disputes
                WHERE respondent_mtp_id = $1
                """,
                mtp_id
            )

            # Get active certifications
            certs = await conn.fetchrow(
                """
                SELECT COUNT(*) as active_certs
                FROM certifications
                WHERE mtp_id = $1 AND status = 'ACTIVE'
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                mtp_id
            )

            total_disputes = disputes['total_disputes'] or 0
            at_fault = disputes['at_fault'] or 0
            dismissed = disputes['dismissed'] or 0
            active_certs = certs['active_certs'] or 0

            # Base score
            score = 1000

            # Deduct for disputes at fault
            score -= at_fault * 100

            # Bonus for dismissed disputes (agent was right)
            score += dismissed * 25

            # Bonus for active certifications
            score += min(active_certs * 50, 200)

            return {
                'score': max(0, min(1000, score)),
                'total_disputes': total_disputes,
                'disputes_at_fault': at_fault,
                'disputes_dismissed': dismissed,
                'active_certifications': active_certs
            }

    async def _calculate_transparency_score(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Calculate transparency component (20% weight)"""
        start_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        async with db_pool.acquire() as conn:
            # Check audit trail completeness (anchored events)
            audit_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE merkle_root IS NOT NULL) as anchored_events
                FROM audit_events
                WHERE mtp_id = $1 AND timestamp >= $2
                """,
                mtp_id, start_date
            )

            # Check dispute response quality
            dispute_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_disputes,
                    COUNT(*) FILTER (WHERE respondent_evidence != '{}') as responded
                FROM disputes
                WHERE respondent_mtp_id = $1
                """,
                mtp_id
            )

            total_events = audit_stats['total_events'] or 0
            anchored = audit_stats['anchored_events'] or 0
            total_disputes = dispute_stats['total_disputes'] or 0
            responded = dispute_stats['responded'] or 0

            # Calculate anchoring rate
            anchor_rate = (anchored / total_events) if total_events > 0 else 1.0

            # Calculate response rate
            response_rate = (responded / total_disputes) if total_disputes > 0 else 1.0

            # Base score based on anchoring
            score = int(anchor_rate * 600)  # Up to 600 points for anchoring

            # Add points for dispute response quality
            score += int(response_rate * 300)  # Up to 300 points for responsiveness

            # Base 100 points for having identity verified
            score += 100

            return {
                'score': max(0, min(1000, score)),
                'total_events': total_events,
                'anchored_events': anchored,
                'anchor_rate': anchor_rate,
                'dispute_response_rate': response_rate
            }

    async def _calculate_history_score(
        self,
        mtp_id: str,
        agent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate history component (15% weight)"""
        registered_at = agent.get('registered_at')

        # Calculate tenure
        if registered_at:
            tenure_days = (datetime.now(timezone.utc) - registered_at).days
        else:
            tenure_days = 0

        async with db_pool.acquire() as conn:
            # Get transaction volume
            volume = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_transactions,
                    COALESCE(SUM(value_transferred), 0) as total_value
                FROM audit_events
                WHERE mtp_id = $1 AND value_transferred IS NOT NULL
                """,
                mtp_id
            )

            total_transactions = volume['total_transactions'] or 0
            total_value = float(volume['total_value'] or 0)

            # Base score starts at 500
            score = 500

            # Tenure bonus (up to 300 points)
            if tenure_days > 365:
                score += 300
            elif tenure_days > 180:
                score += 200
            elif tenure_days > 90:
                score += 100
            elif tenure_days > 30:
                score += 50

            # Volume bonus (up to 200 points)
            if total_transactions > 10000:
                score += 200
            elif total_transactions > 1000:
                score += 100
            elif total_transactions > 100:
                score += 50

            return {
                'score': max(0, min(1000, score)),
                'tenure_days': tenure_days,
                'total_transactions': total_transactions,
                'total_value': total_value
            }

    async def _calculate_decay(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> int:
        """Calculate score decay for inactivity"""
        async with db_pool.acquire() as conn:
            # Get last activity
            last_event = await conn.fetchrow(
                """
                SELECT MAX(timestamp) as last_activity
                FROM audit_events
                WHERE mtp_id = $1
                """,
                mtp_id
            )

            if not last_event or not last_event['last_activity']:
                return 0

            days_inactive = (
                datetime.now(timezone.utc) - last_event['last_activity']
            ).days

            # No decay for first 7 days of inactivity
            if days_inactive <= 7:
                return 0

            # Calculate decay
            decay = int((days_inactive - 7) * self.DECAY_RATE_PER_DAY)
            return min(decay, self.MAX_DECAY)

    async def _record_score_change(
        self,
        mtp_id: str,
        new_score: int,
        previous_score: int,
        components: Dict[str, Any],
        reason: str
    ):
        """Record a trust score change in history"""
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO trust_score_history (
                    id, mtp_id, score, score_components,
                    change_reason, previous_score, calculated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                uuid.uuid4(),
                mtp_id,
                new_score,
                components,
                reason,
                previous_score
            )

    async def _update_agent_score(self, mtp_id: str, score: int):
        """Update agent's trust score"""
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE agents SET trust_score = $1 WHERE mtp_id = $2",
                score, mtp_id
            )

    def _get_tier(self, score: int) -> str:
        """Get tier name for a score"""
        if score >= self.THRESHOLDS['EXCELLENT']:
            return 'EXCELLENT'
        elif score >= self.THRESHOLDS['GOOD']:
            return 'GOOD'
        elif score >= self.THRESHOLDS['FAIR']:
            return 'FAIR'
        elif score >= self.THRESHOLDS['POOR']:
            return 'POOR'
        else:
            return 'CRITICAL'


# Global service instance
trust_service = TrustScoreService()
