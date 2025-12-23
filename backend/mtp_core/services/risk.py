"""Risk Calculation Service - MTP-INSURE Implementation

This service generates comprehensive risk profiles for insurance underwriting
and actuarial pricing. It analyzes agent behavior from audit trails to
classify risk tiers and calculate insurance premiums.

The Insurance Trap:
"Every AI action creates data. That data determines your insurance rate."
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from mtp_core.models.insurance import RiskProfile, RiskTier, Dispute
from mtp_core.models.identity import Agent
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class RiskCalculationService:
    """
    MTP-INSURE Risk Profile Calculator

    Generates comprehensive risk profiles for insurance underwriting by analyzing:
    1. Agent characteristics and tenure
    2. Activity metrics (volume, value, frequency)
    3. Performance metrics (success/error rates)
    4. Trust metrics (score, trend, violations)
    5. Incident history (disputes, damages)

    Risk classification follows actuarial principles:
    - LOW_RISK: Agents with proven track record, high trust, zero incidents
    - MEDIUM_RISK: Standard operational agents
    - HIGH_RISK: Agents with incidents or declining trust
    - VERY_HIGH_RISK: Agents with multiple faults or very low trust
    """

    # Risk scoring weights
    WEIGHTS = {
        'trust_score': 0.25,       # Current trust score impact
        'trust_trend': 0.10,       # Trust score trajectory
        'error_rate': 0.20,        # Error/failure rate
        'dispute_history': 0.20,   # Past disputes at fault
        'transaction_exposure': 0.15,  # Financial exposure
        'tenure': 0.10            # Operational experience
    }

    # Thresholds for risk tier classification
    TIER_THRESHOLDS = {
        'LOW_RISK': 80,
        'MEDIUM_RISK': 60,
        'HIGH_RISK': 40
    }

    async def calculate_risk_profile(
        self,
        mtp_id: str,
        coverage_type: str = "STANDARD",
        lookback_days: int = 365
    ) -> RiskProfile:
        """
        Generate a comprehensive risk profile for an agent.

        Args:
            mtp_id: Agent's MTP identifier
            coverage_type: Type of insurance coverage requested
            lookback_days: Number of days of history to analyze

        Returns:
            Complete RiskProfile for insurance underwriting
        """
        logger.info(f"Calculating risk profile for agent {mtp_id}")

        # Fetch agent data
        agent = await self._get_agent(mtp_id)
        if not agent:
            raise ValueError(f"Agent not found: {mtp_id}")

        # Fetch historical data
        events = await self._get_events(mtp_id, lookback_days)
        disputes = await self._get_disputes(mtp_id)
        trust_history = await self._get_trust_history(mtp_id, lookback_days)

        # Calculate metrics
        activity_metrics = self._calculate_activity_metrics(events)
        performance_metrics = self._calculate_performance_metrics(events)
        trust_metrics = self._calculate_trust_metrics(agent, trust_history)
        incident_metrics = self._calculate_incident_metrics(disputes)

        # Calculate overall risk score (0-100, higher = safer)
        risk_score = self._calculate_risk_score(
            agent=agent,
            activity_metrics=activity_metrics,
            performance_metrics=performance_metrics,
            trust_metrics=trust_metrics,
            incident_metrics=incident_metrics
        )

        # Classify risk tier
        risk_tier = self._classify_risk_tier(risk_score)

        # Calculate financial exposure and coverage recommendation
        financial_exposure = self._calculate_financial_exposure(
            agent=agent,
            activity_metrics=activity_metrics,
            incident_metrics=incident_metrics
        )

        # Build risk factors explanation
        risk_factors = self._build_risk_factors(
            trust_metrics=trust_metrics,
            performance_metrics=performance_metrics,
            incident_metrics=incident_metrics,
            risk_score=risk_score
        )

        return RiskProfile(
            mtp_id=mtp_id,
            calculated_at=datetime.now(timezone.utc),

            # Agent characteristics
            agent_type=agent['agent_type'],
            base_model=agent['base_model'],
            jurisdiction=agent['jurisdiction'],

            # Activity metrics
            total_events=activity_metrics['total_events'],
            total_transactions=activity_metrics['total_transactions'],
            total_value_transferred=activity_metrics['total_value'],

            # Performance metrics
            success_rate=performance_metrics['success_rate'],
            error_rate=performance_metrics['error_rate'],
            average_transaction_value=activity_metrics['avg_transaction_value'],

            # Trust & Compliance
            current_trust_score=trust_metrics['current_score'],
            trust_score_history=trust_metrics['history'],
            policy_violations=incident_metrics['violations'],
            disputes_filed=incident_metrics['total_disputes'],
            disputes_resolved_favorably=incident_metrics['favorable_resolutions'],

            # Risk Assessment
            risk_tier=risk_tier,
            risk_score=risk_score / 100.0,  # Normalize to 0-1
            risk_factors=risk_factors,

            # Financial Exposure
            max_potential_loss=financial_exposure['max_loss'],
            recommended_coverage=financial_exposure['recommended_coverage']
        )

    async def _get_agent(self, mtp_id: str) -> Optional[Dict[str, Any]]:
        """Fetch agent details from database"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT mtp_id, agent_type, base_model, jurisdiction,
                       trust_score, transaction_limit_daily, registered_at,
                       status, authorized_actions, prohibited_actions
                FROM agents WHERE mtp_id = $1
                """,
                mtp_id
            )
            return dict(row) if row else None

    async def _get_events(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> List[Dict[str, Any]]:
        """Fetch audit events for analysis"""
        start_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, event_category, status,
                       value_transferred, timestamp, error_details
                FROM audit_events
                WHERE mtp_id = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
                """,
                mtp_id, start_date
            )
            return [dict(row) for row in rows]

    async def _get_disputes(self, mtp_id: str) -> List[Dict[str, Any]]:
        """Fetch disputes where agent is respondent"""
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, dispute_number, incident_category, status,
                       finding, claimed_damages, trust_score_impact,
                       filed_at, resolved_at, insurance_payout
                FROM disputes
                WHERE respondent_mtp_id = $1
                ORDER BY filed_at DESC
                """,
                mtp_id
            )
            return [dict(row) for row in rows]

    async def _get_trust_history(
        self,
        mtp_id: str,
        lookback_days: int
    ) -> List[int]:
        """
        Get historical trust scores.

        Note: In production, this would query a trust_score_history table.
        For now, we'll return the current trust score as a single point.
        """
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT trust_score FROM agents WHERE mtp_id = $1",
                mtp_id
            )
            if row:
                return [row['trust_score']]
            return [500]  # Default

    def _calculate_activity_metrics(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate activity-related metrics"""
        total_events = len(events)

        # Filter for transactions (events with value transfer)
        transactions = [e for e in events if e.get('value_transferred')]
        total_transactions = len(transactions)

        total_value = sum(
            float(e['value_transferred'] or 0)
            for e in transactions
        )

        avg_transaction_value = (
            total_value / total_transactions
            if total_transactions > 0 else 0.0
        )

        # Calculate daily averages
        if events:
            first_event = min(e['timestamp'] for e in events)
            last_event = max(e['timestamp'] for e in events)
            days_active = max((last_event - first_event).days, 1)
            events_per_day = total_events / days_active
            transactions_per_day = total_transactions / days_active
        else:
            events_per_day = 0
            transactions_per_day = 0

        return {
            'total_events': total_events,
            'total_transactions': total_transactions,
            'total_value': total_value,
            'avg_transaction_value': avg_transaction_value,
            'events_per_day': events_per_day,
            'transactions_per_day': transactions_per_day
        }

    def _calculate_performance_metrics(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate performance-related metrics"""
        if not events:
            return {
                'success_rate': 1.0,
                'error_rate': 0.0,
                'escalation_rate': 0.0
            }

        total = len(events)

        # Count by status
        successful = len([e for e in events if e['status'] == 'SUCCESS'])
        failed = len([e for e in events if e['status'] in ('FAILURE', 'ERROR')])
        escalated = len([e for e in events if e['status'] == 'ESCALATED'])

        return {
            'success_rate': successful / total if total > 0 else 1.0,
            'error_rate': failed / total if total > 0 else 0.0,
            'escalation_rate': escalated / total if total > 0 else 0.0
        }

    def _calculate_trust_metrics(
        self,
        agent: Dict[str, Any],
        trust_history: List[int]
    ) -> Dict[str, Any]:
        """Calculate trust-related metrics"""
        current_score = agent.get('trust_score', 500)

        # Calculate trend (positive = improving, negative = declining)
        if len(trust_history) >= 2:
            trend = trust_history[-1] - trust_history[0]
        else:
            trend = 0

        return {
            'current_score': current_score,
            'history': trust_history,
            'trend': trend,
            'lowest_score': min(trust_history) if trust_history else current_score,
            'highest_score': max(trust_history) if trust_history else current_score,
            'volatility': self._calculate_volatility(trust_history)
        }

    def _calculate_volatility(self, scores: List[int]) -> float:
        """Calculate score volatility (standard deviation)"""
        if len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance ** 0.5

    def _calculate_incident_metrics(
        self,
        disputes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate incident-related metrics"""
        total_disputes = len(disputes)

        # Count by finding
        at_fault = len([d for d in disputes if d.get('finding') == 'UPHELD'])
        no_fault = len([d for d in disputes if d.get('finding') == 'DISMISSED'])
        partial_fault = len([d for d in disputes if d.get('finding') == 'PARTIAL'])
        pending = len([d for d in disputes if d.get('finding') is None])

        # Calculate total damages paid
        total_damages = sum(
            float(d.get('claimed_damages') or 0)
            for d in disputes
            if d.get('finding') in ('UPHELD', 'PARTIAL')
        )

        # Calculate total trust score impact
        total_trust_impact = sum(
            d.get('trust_score_impact') or 0
            for d in disputes
        )

        return {
            'total_disputes': total_disputes,
            'at_fault': at_fault,
            'no_fault': no_fault,
            'partial_fault': partial_fault,
            'pending': pending,
            'favorable_resolutions': no_fault,
            'violations': at_fault + partial_fault,
            'total_damages': total_damages,
            'total_trust_impact': total_trust_impact
        }

    def _calculate_risk_score(
        self,
        agent: Dict[str, Any],
        activity_metrics: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        trust_metrics: Dict[str, Any],
        incident_metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate overall risk score (0-100, higher = lower risk/safer).

        Uses weighted components:
        - Trust score (25%): Current trust score normalized
        - Trust trend (10%): Score trajectory
        - Error rate (20%): Performance reliability
        - Dispute history (20%): Past incidents
        - Transaction exposure (15%): Financial risk
        - Tenure (10%): Operational experience
        """
        score = 100.0  # Start at maximum (lowest risk)

        # Trust score component (25%)
        # Score of 500 is baseline, 1000 is perfect, 0 is terrible
        trust_score = trust_metrics['current_score']
        if trust_score < 500:
            score -= self.WEIGHTS['trust_score'] * 100 * (1 - trust_score / 500)
        else:
            # Bonus for high trust scores
            bonus = (trust_score - 500) / 500 * 10  # Up to 10 point bonus
            score = min(100, score + bonus)

        # Trust trend component (10%)
        trend = trust_metrics['trend']
        if trend < -50:  # Significant decline
            score -= self.WEIGHTS['trust_trend'] * 100
        elif trend < 0:  # Minor decline
            score -= self.WEIGHTS['trust_trend'] * 50
        # Positive trend doesn't add extra (already reflected in current score)

        # Error rate component (20%)
        error_rate = performance_metrics['error_rate']
        if error_rate > 0.05:  # More than 5% errors
            score -= self.WEIGHTS['error_rate'] * 100
        elif error_rate > 0.02:  # More than 2% errors
            score -= self.WEIGHTS['error_rate'] * 50
        elif error_rate > 0.01:  # More than 1% errors
            score -= self.WEIGHTS['error_rate'] * 25

        # Dispute history component (20%)
        at_fault_disputes = incident_metrics['at_fault']
        if at_fault_disputes >= 3:
            score -= self.WEIGHTS['dispute_history'] * 100
        elif at_fault_disputes >= 2:
            score -= self.WEIGHTS['dispute_history'] * 75
        elif at_fault_disputes >= 1:
            score -= self.WEIGHTS['dispute_history'] * 50

        # Transaction exposure component (15%)
        daily_limit = float(agent.get('transaction_limit_daily', 0))
        if daily_limit > 100000:
            score -= self.WEIGHTS['transaction_exposure'] * 50
        elif daily_limit > 50000:
            score -= self.WEIGHTS['transaction_exposure'] * 25

        # Tenure component (10%)
        registered_at = agent.get('registered_at')
        if registered_at:
            tenure_days = (datetime.now(timezone.utc) - registered_at).days
            if tenure_days > 365:
                score += self.WEIGHTS['tenure'] * 25  # Tenure bonus
            elif tenure_days > 180:
                score += self.WEIGHTS['tenure'] * 15
            elif tenure_days < 30:
                score -= self.WEIGHTS['tenure'] * 50  # New agent risk

        return max(0, min(100, score))

    def _classify_risk_tier(self, risk_score: float) -> RiskTier:
        """Classify risk tier based on score"""
        if risk_score >= self.TIER_THRESHOLDS['LOW_RISK']:
            return RiskTier.LOW_RISK
        elif risk_score >= self.TIER_THRESHOLDS['MEDIUM_RISK']:
            return RiskTier.MEDIUM_RISK
        elif risk_score >= self.TIER_THRESHOLDS['HIGH_RISK']:
            return RiskTier.HIGH_RISK
        else:
            return RiskTier.VERY_HIGH_RISK

    def _calculate_financial_exposure(
        self,
        agent: Dict[str, Any],
        activity_metrics: Dict[str, Any],
        incident_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate financial exposure and recommended coverage"""
        daily_limit = float(agent.get('transaction_limit_daily', 0))

        # Maximum potential loss in a worst-case scenario
        # Consider daily limit x 30 days of undetected fraud
        max_loss = daily_limit * 30

        # Add historical damages as floor
        historical_damages = incident_metrics['total_damages']
        max_loss = max(max_loss, historical_damages * 2)

        # Recommended coverage is max loss with 20% buffer
        recommended_coverage = max_loss * 1.2

        return {
            'max_loss': max_loss,
            'recommended_coverage': recommended_coverage,
            'daily_exposure': daily_limit,
            'historical_damages': historical_damages
        }

    def _build_risk_factors(
        self,
        trust_metrics: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        incident_metrics: Dict[str, Any],
        risk_score: float
    ) -> Dict[str, Any]:
        """Build explanatory risk factors for underwriters"""
        factors = {
            'score_breakdown': {
                'trust_component': trust_metrics['current_score'] / 10,  # 0-100
                'performance_component': (1 - performance_metrics['error_rate']) * 100,
                'incident_component': max(0, 100 - incident_metrics['at_fault'] * 25),
                'overall_score': risk_score
            },
            'risk_indicators': [],
            'positive_indicators': []
        }

        # Flag risk indicators
        if trust_metrics['current_score'] < 500:
            factors['risk_indicators'].append({
                'type': 'LOW_TRUST_SCORE',
                'severity': 'HIGH',
                'value': trust_metrics['current_score'],
                'threshold': 500
            })

        if trust_metrics['trend'] < -50:
            factors['risk_indicators'].append({
                'type': 'DECLINING_TRUST',
                'severity': 'MEDIUM',
                'value': trust_metrics['trend'],
                'description': 'Trust score is declining significantly'
            })

        if performance_metrics['error_rate'] > 0.05:
            factors['risk_indicators'].append({
                'type': 'HIGH_ERROR_RATE',
                'severity': 'HIGH',
                'value': f"{performance_metrics['error_rate']*100:.1f}%",
                'threshold': '5%'
            })

        if incident_metrics['at_fault'] > 0:
            factors['risk_indicators'].append({
                'type': 'DISPUTE_HISTORY',
                'severity': 'HIGH' if incident_metrics['at_fault'] > 1 else 'MEDIUM',
                'value': incident_metrics['at_fault'],
                'description': f"{incident_metrics['at_fault']} disputes found at fault"
            })

        # Flag positive indicators
        if trust_metrics['current_score'] >= 800:
            factors['positive_indicators'].append({
                'type': 'HIGH_TRUST_SCORE',
                'value': trust_metrics['current_score']
            })

        if performance_metrics['error_rate'] < 0.01:
            factors['positive_indicators'].append({
                'type': 'LOW_ERROR_RATE',
                'value': f"{performance_metrics['error_rate']*100:.2f}%"
            })

        if incident_metrics['total_disputes'] == 0:
            factors['positive_indicators'].append({
                'type': 'NO_DISPUTE_HISTORY',
                'description': 'No disputes filed against this agent'
            })

        return factors

    async def calculate_premium(
        self,
        risk_profile: RiskProfile,
        coverage_amount: float,
        coverage_period_months: int = 12
    ) -> Dict[str, Any]:
        """
        Calculate insurance premium based on risk profile.

        This is a simplified actuarial model for demonstration.
        Real implementation would use more sophisticated pricing.

        Args:
            risk_profile: The agent's risk profile
            coverage_amount: Desired coverage amount in ZAR
            coverage_period_months: Coverage period

        Returns:
            Premium calculation details
        """
        # Base rate by risk tier (annual rate per R10,000 coverage)
        BASE_RATES = {
            RiskTier.LOW_RISK: 50,      # R50 per R10,000 per year
            RiskTier.MEDIUM_RISK: 100,  # R100 per R10,000 per year
            RiskTier.HIGH_RISK: 200,    # R200 per R10,000 per year
            RiskTier.VERY_HIGH_RISK: 400  # R400 per R10,000 per year
        }

        base_rate = BASE_RATES[risk_profile.risk_tier]

        # Calculate base premium
        units = coverage_amount / 10000
        annual_premium = base_rate * units

        # Adjust for coverage period
        premium = annual_premium * (coverage_period_months / 12)

        # Apply adjustments based on risk factors
        adjustment_factor = 1.0

        # Trust score adjustment
        if risk_profile.current_trust_score >= 800:
            adjustment_factor *= 0.9  # 10% discount
        elif risk_profile.current_trust_score < 400:
            adjustment_factor *= 1.2  # 20% surcharge

        # Error rate adjustment
        if risk_profile.error_rate > 0.05:
            adjustment_factor *= 1.3  # 30% surcharge

        # Dispute history adjustment
        if risk_profile.disputes_filed > 0:
            adjustment_factor *= 1 + (risk_profile.disputes_filed * 0.1)  # 10% per dispute

        final_premium = premium * adjustment_factor

        return {
            'coverage_amount': coverage_amount,
            'coverage_period_months': coverage_period_months,
            'risk_tier': risk_profile.risk_tier.value,
            'base_rate': base_rate,
            'base_premium': premium,
            'adjustment_factor': adjustment_factor,
            'final_premium': round(final_premium, 2),
            'monthly_premium': round(final_premium / coverage_period_months, 2),
            'currency': 'ZAR',
            'quote_valid_until': (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat()
        }


# Global service instance
risk_service = RiskCalculationService()
