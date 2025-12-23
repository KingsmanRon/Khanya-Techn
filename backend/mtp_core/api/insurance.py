"""Insurance API Endpoints - MTP-INSURE

API endpoints for insurance integration, risk profiling, and claims.
This is where risk data becomes revenue through insurance partnerships.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging
import uuid

from mtp_core.services.risk import risk_service
from mtp_core.services.dispute import dispute_service
from mtp_core.models.insurance import RiskTier, DisputeStatus
from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insurance", tags=["Insurance"])


# Request/Response Models
class RiskProfileResponse(BaseModel):
    """Risk profile response for underwriting"""
    mtp_id: str
    calculated_at: datetime

    # Agent info
    agent_type: str
    base_model: str
    jurisdiction: str

    # Activity metrics
    total_events: int
    total_transactions: int
    total_value_transferred: float

    # Performance
    success_rate: float
    error_rate: float
    average_transaction_value: float

    # Trust
    current_trust_score: int
    trust_score_trend: str  # IMPROVING, STABLE, DECLINING

    # Incidents
    disputes_filed: int
    disputes_at_fault: int

    # Risk assessment
    risk_tier: str
    risk_score: float

    # Financial
    max_potential_loss: float
    recommended_coverage: float

    # Factors
    risk_factors: dict


class PremiumQuoteRequest(BaseModel):
    """Request for insurance premium quote"""
    mtp_id: str = Field(..., description="Agent MTP ID")
    coverage_amount: float = Field(
        ...,
        description="Desired coverage amount in ZAR",
        gt=0
    )
    coverage_period_months: int = Field(
        default=12,
        description="Coverage period in months",
        ge=1,
        le=36
    )
    coverage_type: str = Field(
        default="STANDARD",
        description="Type of coverage: STANDARD, COMPREHENSIVE, BASIC"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mtp_id": "MTP-fnb-7k9m2p",
                "coverage_amount": 1000000.00,
                "coverage_period_months": 12,
                "coverage_type": "STANDARD"
            }
        }


class PremiumQuoteResponse(BaseModel):
    """Insurance premium quote response"""
    quote_id: str
    mtp_id: str
    coverage_amount: float
    coverage_period_months: int
    risk_tier: str
    base_rate: float
    base_premium: float
    adjustment_factor: float
    final_premium: float
    monthly_premium: float
    currency: str
    quote_valid_until: str


class FileClaimRequest(BaseModel):
    """Request to file an insurance claim"""
    mtp_id: str = Field(..., description="Agent MTP ID")
    dispute_id: str = Field(..., description="Related dispute ID")
    policy_reference: str = Field(..., description="Insurance policy reference")
    claim_amount: float = Field(..., description="Amount being claimed", gt=0)
    claim_description: str = Field(..., description="Description of the claim")

    class Config:
        json_schema_extra = {
            "example": {
                "mtp_id": "MTP-fnb-7k9m2p",
                "dispute_id": "uuid-of-dispute",
                "policy_reference": "POL-2025-001234",
                "claim_amount": 5000.00,
                "claim_description": "Claim for unauthorized transaction damages"
            }
        }


class ClaimResponse(BaseModel):
    """Insurance claim response"""
    claim_id: str
    mtp_id: str
    dispute_id: str
    policy_reference: str
    claim_amount: float
    claim_description: str
    status: str
    filed_at: datetime
    evidence_summary: dict


class ClaimListResponse(BaseModel):
    """List of claims response"""
    claims: List[ClaimResponse]
    total: int


# API Endpoints
@router.get("/risk-profile/{mtp_id}", response_model=RiskProfileResponse)
async def get_risk_profile(
    mtp_id: str,
    coverage_type: str = Query("STANDARD", description="Coverage type"),
    lookback_days: int = Query(365, ge=30, le=730, description="Days of history")
):
    """
    Get comprehensive risk profile for an agent.

    This endpoint provides all data needed for insurance underwriting:
    - Agent characteristics and tenure
    - Activity and performance metrics
    - Trust score and compliance history
    - Incident history and damages
    - Risk tier classification
    - Recommended coverage amounts

    Used by insurance partners for pricing and underwriting decisions.
    """
    try:
        profile = await risk_service.calculate_risk_profile(
            mtp_id=mtp_id,
            coverage_type=coverage_type,
            lookback_days=lookback_days
        )

        # Calculate trend
        if len(profile.trust_score_history) >= 2:
            first = profile.trust_score_history[0]
            last = profile.trust_score_history[-1]
            if last > first + 20:
                trend = "IMPROVING"
            elif last < first - 20:
                trend = "DECLINING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        return RiskProfileResponse(
            mtp_id=profile.mtp_id,
            calculated_at=profile.calculated_at,
            agent_type=profile.agent_type,
            base_model=profile.base_model,
            jurisdiction=profile.jurisdiction,
            total_events=profile.total_events,
            total_transactions=profile.total_transactions,
            total_value_transferred=profile.total_value_transferred,
            success_rate=profile.success_rate,
            error_rate=profile.error_rate,
            average_transaction_value=profile.average_transaction_value,
            current_trust_score=profile.current_trust_score,
            trust_score_trend=trend,
            disputes_filed=profile.disputes_filed,
            disputes_at_fault=profile.disputes_filed - profile.disputes_resolved_favorably,
            risk_tier=profile.risk_tier.value,
            risk_score=profile.risk_score,
            max_potential_loss=profile.max_potential_loss,
            recommended_coverage=profile.recommended_coverage,
            risk_factors=profile.risk_factors
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate risk profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate risk profile")


@router.post("/quote", response_model=PremiumQuoteResponse)
async def get_premium_quote(request: PremiumQuoteRequest):
    """
    Get an insurance premium quote for an agent.

    Based on the agent's risk profile, calculates:
    - Base premium from risk tier
    - Adjustments based on trust score, error rate, and history
    - Final premium with monthly breakdown

    Quote is valid for 30 days.
    """
    try:
        # Get risk profile first
        profile = await risk_service.calculate_risk_profile(
            mtp_id=request.mtp_id,
            coverage_type=request.coverage_type
        )

        # Calculate premium
        quote = await risk_service.calculate_premium(
            risk_profile=profile,
            coverage_amount=request.coverage_amount,
            coverage_period_months=request.coverage_period_months
        )

        quote_id = f"QUO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        return PremiumQuoteResponse(
            quote_id=quote_id,
            mtp_id=request.mtp_id,
            coverage_amount=quote['coverage_amount'],
            coverage_period_months=quote['coverage_period_months'],
            risk_tier=quote['risk_tier'],
            base_rate=quote['base_rate'],
            base_premium=quote['base_premium'],
            adjustment_factor=quote['adjustment_factor'],
            final_premium=quote['final_premium'],
            monthly_premium=quote['monthly_premium'],
            currency=quote['currency'],
            quote_valid_until=quote['quote_valid_until']
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate premium quote")


@router.post("/claims", response_model=ClaimResponse, status_code=201)
async def file_claim(request: FileClaimRequest):
    """
    File an insurance claim linked to a dispute.

    A claim can only be filed when:
    - A dispute exists and is resolved with finding against agent
    - The agent has a valid insurance policy

    This endpoint creates the claim record and links it to the dispute.
    """
    # Verify dispute exists and is resolved
    dispute = await dispute_service.get_dispute(request.dispute_id)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status != DisputeStatus.RESOLVED:
        raise HTTPException(
            status_code=400,
            detail="Can only file claims for resolved disputes"
        )

    if dispute.finding not in ['UPHELD', 'PARTIAL']:
        raise HTTPException(
            status_code=400,
            detail="Can only file claims when agent is found at fault"
        )

    if dispute.respondent_mtp_id != request.mtp_id:
        raise HTTPException(
            status_code=400,
            detail="MTP ID must match dispute respondent"
        )

    # Create claim record
    claim_id = str(uuid.uuid4())
    claim_ref = f"CLM-{datetime.now().strftime('%Y%m%d')}-{claim_id[:8].upper()}"

    # Get evidence summary
    evidence = await dispute_service.get_audit_evidence(request.dispute_id)

    try:
        async with db_pool.acquire() as conn:
            # Update dispute with insurance claim reference
            await conn.execute(
                """
                UPDATE disputes
                SET insurance_claim_ref = $1
                WHERE id = $2
                """,
                claim_ref,
                uuid.UUID(request.dispute_id)
            )

        logger.info(f"Insurance claim {claim_ref} filed for dispute {dispute.dispute_number}")

        return ClaimResponse(
            claim_id=claim_id,
            mtp_id=request.mtp_id,
            dispute_id=request.dispute_id,
            policy_reference=request.policy_reference,
            claim_amount=request.claim_amount,
            claim_description=request.claim_description,
            status="FILED",
            filed_at=datetime.now(),
            evidence_summary={
                "dispute_number": dispute.dispute_number,
                "finding": dispute.finding,
                "remedy_ordered": dispute.remedy_ordered,
                "audit_events_count": len(evidence),
                "blockchain_anchored": any(e.get('blockchain_proof') for e in evidence)
            }
        )

    except Exception as e:
        logger.error(f"Failed to file claim: {e}")
        raise HTTPException(status_code=500, detail="Failed to file claim")


@router.get("/claims", response_model=ClaimListResponse)
async def list_claims(
    mtp_id: Optional[str] = Query(None, description="Filter by agent MTP ID"),
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List insurance claims with optional filters.

    Returns claims linked to disputes with insurance references.
    """
    # Query disputes that have insurance claims
    query = """
        SELECT id, respondent_mtp_id, dispute_number, insurance_claim_ref,
               claimed_damages, finding, remedy_ordered, filed_at
        FROM disputes
        WHERE insurance_claim_ref IS NOT NULL
    """
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

    query += f" ORDER BY filed_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    params.extend([limit, offset])

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    claims = []
    for row in rows:
        claims.append(ClaimResponse(
            claim_id=row['insurance_claim_ref'].replace('CLM-', ''),
            mtp_id=row['respondent_mtp_id'],
            dispute_id=str(row['id']),
            policy_reference="",  # Would be stored in separate claims table
            claim_amount=float(row['claimed_damages'] or 0),
            claim_description=f"Claim for dispute {row['dispute_number']}",
            status="FILED",
            filed_at=row['filed_at'],
            evidence_summary={
                "dispute_number": row['dispute_number'],
                "finding": row['finding'],
                "remedy_ordered": row['remedy_ordered']
            }
        ))

    return ClaimListResponse(
        claims=claims,
        total=len(claims)
    )


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: str):
    """
    Get insurance claim details by ID.
    """
    # Find dispute with this claim reference
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, respondent_mtp_id, dispute_number, insurance_claim_ref,
                   claimed_damages, finding, remedy_ordered, filed_at
            FROM disputes
            WHERE insurance_claim_ref LIKE $1
            """,
            f"%{claim_id}%"
        )

    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")

    return ClaimResponse(
        claim_id=claim_id,
        mtp_id=row['respondent_mtp_id'],
        dispute_id=str(row['id']),
        policy_reference="",
        claim_amount=float(row['claimed_damages'] or 0),
        claim_description=f"Claim for dispute {row['dispute_number']}",
        status="FILED",
        filed_at=row['filed_at'],
        evidence_summary={
            "dispute_number": row['dispute_number'],
            "finding": row['finding'],
            "remedy_ordered": row['remedy_ordered']
        }
    )


@router.get("/risk-tiers")
async def get_risk_tiers():
    """
    Get information about risk tier classifications.

    Returns the criteria and characteristics of each risk tier.
    """
    return {
        "tiers": [
            {
                "tier": RiskTier.LOW_RISK.value,
                "score_range": "80-100",
                "characteristics": [
                    "Trust score 700+",
                    "Error rate < 1%",
                    "No disputes at fault",
                    "Operational tenure > 6 months"
                ],
                "base_rate_per_10k": 50,
                "typical_adjustment_range": "0.9x - 1.0x"
            },
            {
                "tier": RiskTier.MEDIUM_RISK.value,
                "score_range": "60-79",
                "characteristics": [
                    "Trust score 500-700",
                    "Error rate 1-3%",
                    "0-1 disputes",
                    "Standard operation"
                ],
                "base_rate_per_10k": 100,
                "typical_adjustment_range": "1.0x - 1.2x"
            },
            {
                "tier": RiskTier.HIGH_RISK.value,
                "score_range": "40-59",
                "characteristics": [
                    "Trust score 300-500",
                    "Error rate 3-5%",
                    "1-2 disputes at fault",
                    "Declining trust trend"
                ],
                "base_rate_per_10k": 200,
                "typical_adjustment_range": "1.2x - 1.5x"
            },
            {
                "tier": RiskTier.VERY_HIGH_RISK.value,
                "score_range": "0-39",
                "characteristics": [
                    "Trust score < 300",
                    "Error rate > 5%",
                    "Multiple disputes at fault",
                    "Recent policy violations"
                ],
                "base_rate_per_10k": 400,
                "typical_adjustment_range": "1.5x - 2.0x",
                "note": "May require additional underwriting review"
            }
        ],
        "currency": "ZAR",
        "rate_description": "Annual rate per R10,000 of coverage"
    }
