"""Trust Score API Endpoints - MTP-TRUST

API endpoints for trust score queries and management.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from mtp_core.services.trust import trust_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trust", tags=["Trust Score"])


# Response Models
class TrustScoreResponse(BaseModel):
    """Basic trust score response"""
    mtp_id: str
    score: int
    tier: str
    thresholds: dict


class TrustScoreDetailResponse(BaseModel):
    """Detailed trust score with components"""
    mtp_id: str
    total_score: int
    tier: str
    components: dict
    decay_applied: int
    previous_score: int
    change: int
    calculated_at: str


class TrustHistoryItem(BaseModel):
    """Trust score history item"""
    id: str
    score: int
    components: Optional[dict]
    reason: Optional[str]
    previous_score: Optional[int]
    change: int
    calculated_at: str


class TrustHistoryResponse(BaseModel):
    """Trust score history response"""
    mtp_id: str
    history: List[TrustHistoryItem]
    total: int


class TrustImpactRequest(BaseModel):
    """Request to apply trust score impact"""
    impact: int = Field(..., description="Points to add (positive) or subtract (negative)")
    reason: str = Field(..., description="Reason for the change")

    class Config:
        json_schema_extra = {
            "example": {
                "impact": -25,
                "reason": "Policy violation detected"
            }
        }


class TrustImpactResponse(BaseModel):
    """Trust impact response"""
    mtp_id: str
    previous_score: int
    new_score: int
    impact: int
    reason: str
    tier: str


# API Endpoints
@router.get("/{mtp_id}", response_model=TrustScoreResponse)
async def get_trust_score(mtp_id: str):
    """
    Get current trust score for an agent.

    Returns the current trust score, tier, and threshold definitions.
    This is a quick lookup without recalculation.
    """
    try:
        result = await trust_service.get_trust_score(mtp_id)
        return TrustScoreResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{mtp_id}/calculate", response_model=TrustScoreDetailResponse)
async def calculate_trust_score(
    mtp_id: str,
    lookback_days: int = Query(90, ge=7, le=365, description="Days of history to analyze")
):
    """
    Calculate comprehensive trust score for an agent.

    This performs a full recalculation of the trust score including
    all component scores (reliability, compliance, transparency, history).

    The calculated score is stored in history and updates the agent's
    current trust score.
    """
    try:
        result = await trust_service.calculate_trust_score(mtp_id, lookback_days)
        return TrustScoreDetailResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{mtp_id}/history", response_model=TrustHistoryResponse)
async def get_trust_history(
    mtp_id: str,
    limit: int = Query(30, ge=1, le=100, description="Number of history items")
):
    """
    Get trust score history for an agent.

    Returns historical trust score changes with reasons and component breakdowns.
    """
    try:
        history = await trust_service.get_trust_history(mtp_id, limit)
        return TrustHistoryResponse(
            mtp_id=mtp_id,
            history=[TrustHistoryItem(**h) for h in history],
            total=len(history)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{mtp_id}/impact", response_model=TrustImpactResponse)
async def apply_trust_impact(mtp_id: str, request: TrustImpactRequest):
    """
    Apply a trust score impact to an agent.

    This allows manual adjustment of trust scores for:
    - Policy violations (negative impact)
    - Successful audits (positive impact)
    - Dispute resolutions (impact based on finding)
    - Manual corrections

    The impact is clamped to keep scores in 0-1000 range.
    """
    try:
        result = await trust_service.apply_trust_impact(
            mtp_id=mtp_id,
            impact=request.impact,
            reason=request.reason
        )
        return TrustImpactResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tiers/info")
async def get_tier_info():
    """
    Get information about trust score tiers.

    Returns threshold values and descriptions for each tier.
    """
    return {
        "tiers": [
            {
                "tier": "EXCELLENT",
                "min_score": 800,
                "description": "Highly trusted agent with excellent track record"
            },
            {
                "tier": "GOOD",
                "min_score": 650,
                "description": "Well-performing agent with good compliance"
            },
            {
                "tier": "FAIR",
                "min_score": 500,
                "description": "Standard agent with acceptable performance"
            },
            {
                "tier": "POOR",
                "min_score": 350,
                "description": "Agent with issues requiring attention"
            },
            {
                "tier": "CRITICAL",
                "min_score": 0,
                "description": "Agent with severe issues, may require suspension"
            }
        ],
        "max_score": 1000,
        "initial_score": 500,
        "components": {
            "reliability": {
                "weight": "40%",
                "factors": ["Success rate", "Error rate", "Uptime"]
            },
            "compliance": {
                "weight": "25%",
                "factors": ["Dispute history", "Certifications", "Policy adherence"]
            },
            "transparency": {
                "weight": "20%",
                "factors": ["Audit trail completeness", "Blockchain anchoring", "Dispute response"]
            },
            "history": {
                "weight": "15%",
                "factors": ["Tenure", "Transaction volume", "Experience"]
            }
        }
    }
