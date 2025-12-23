"""Dispute Resolution API Endpoints - MTP-RESOLVE

API endpoints for the formal dispute resolution process.
When AI agents cause harm, this is where accountability happens.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from mtp_core.services.dispute import dispute_service
from mtp_core.models.insurance import DisputeStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disputes", tags=["Disputes"])


# Request/Response Models
class FileDisputeRequest(BaseModel):
    """Request to file a new dispute"""
    complainant_type: str = Field(
        ...,
        description="Type of complainant: USER, ORGANIZATION, REGULATOR"
    )
    complainant_identifier: str = Field(
        ...,
        description="Email or identifier of the complainant"
    )
    respondent_mtp_id: str = Field(
        ...,
        description="MTP ID of the agent being disputed"
    )
    incident_timestamp: datetime = Field(
        ...,
        description="When the incident occurred"
    )
    incident_description: str = Field(
        ...,
        description="Detailed description of the incident"
    )
    incident_category: str = Field(
        ...,
        description="Category: unauthorized_transaction, incorrect_information, "
                   "service_failure, delayed_response, policy_violation, other"
    )
    claimed_damages: float = Field(
        default=0.0,
        description="Amount of damages claimed (in currency specified)"
    )
    currency: str = Field(
        default="ZAR",
        description="Currency for damages claim"
    )
    related_event_ids: List[str] = Field(
        default=[],
        description="List of audit event IDs as evidence"
    )
    evidence: dict = Field(
        default={},
        description="Additional evidence from complainant"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "complainant_type": "USER",
                "complainant_identifier": "customer@example.com",
                "respondent_mtp_id": "MTP-fnb-7k9m2p",
                "incident_timestamp": "2025-01-15T10:30:00Z",
                "incident_description": "Agent transferred funds without authorization",
                "incident_category": "unauthorized_transaction",
                "claimed_damages": 5000.00,
                "currency": "ZAR",
                "related_event_ids": ["evt-abc123", "evt-def456"],
                "evidence": {
                    "screenshots": ["https://..."],
                    "additional_notes": "Transaction was not requested"
                }
            }
        }


class SubmitResponseRequest(BaseModel):
    """Request to submit a response to a dispute"""
    response_statement: str = Field(
        ...,
        description="Official response statement from respondent"
    )
    evidence: dict = Field(
        default={},
        description="Evidence from respondent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response_statement": "We have reviewed the incident and found...",
                "evidence": {
                    "internal_logs": "...",
                    "agent_configuration": "..."
                }
            }
        }


class ResolveDisputeRequest(BaseModel):
    """Request to resolve a dispute (arbitrator)"""
    finding: str = Field(
        ...,
        description="Finding: UPHELD, DISMISSED, PARTIAL"
    )
    finding_details: str = Field(
        ...,
        description="Detailed explanation of the finding"
    )
    remedy_ordered: dict = Field(
        default={},
        description="Remedy to be applied"
    )
    trust_score_impact: int = Field(
        default=0,
        description="Impact to agent's trust score (negative for penalty)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "finding": "UPHELD",
                "finding_details": "Investigation confirmed unauthorized transaction",
                "remedy_ordered": {
                    "type": "full_refund",
                    "amount": 5000.00,
                    "deadline": "2025-02-01"
                },
                "trust_score_impact": -50
            }
        }


class AppealRequest(BaseModel):
    """Request to appeal a dispute resolution"""
    appeal_reason: str = Field(
        ...,
        description="Reason for appealing the decision"
    )
    additional_evidence: dict = Field(
        default={},
        description="New evidence for the appeal"
    )


class DisputeResponse(BaseModel):
    """Dispute response model"""
    id: str
    dispute_number: str
    complainant_type: str
    respondent_mtp_id: str
    incident_category: str
    incident_description: str
    claimed_damages: float
    currency: str
    status: str
    finding: Optional[str]
    finding_details: Optional[str]
    remedy_ordered: Optional[dict]
    trust_score_impact: int
    filed_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]


class DisputeListResponse(BaseModel):
    """List of disputes response"""
    disputes: List[DisputeResponse]
    total: int
    limit: int
    offset: int


# API Endpoints
@router.post("", response_model=DisputeResponse, status_code=201)
async def file_dispute(request: FileDisputeRequest):
    """
    File a new dispute against an AI agent.

    This initiates the formal dispute resolution process.
    The dispute will be automatically assessed for potential auto-resolution.
    """
    try:
        dispute = await dispute_service.file_dispute(
            complainant_type=request.complainant_type,
            complainant_identifier=request.complainant_identifier,
            respondent_mtp_id=request.respondent_mtp_id,
            incident_timestamp=request.incident_timestamp,
            incident_description=request.incident_description,
            incident_category=request.incident_category,
            claimed_damages=request.claimed_damages,
            currency=request.currency,
            related_event_ids=request.related_event_ids,
            complainant_evidence=request.evidence
        )

        logger.info(f"Dispute filed: {dispute.dispute_number}")

        return DisputeResponse(
            id=dispute.id,
            dispute_number=dispute.dispute_number,
            complainant_type=dispute.complainant_type,
            respondent_mtp_id=dispute.respondent_mtp_id,
            incident_category=dispute.incident_category,
            incident_description=dispute.incident_description,
            claimed_damages=dispute.claimed_damages,
            currency=dispute.currency,
            status=dispute.status.value,
            finding=dispute.finding,
            finding_details=dispute.finding_details,
            remedy_ordered=dispute.remedy_ordered,
            trust_score_impact=dispute.trust_score_impact,
            filed_at=dispute.filed_at,
            acknowledged_at=dispute.acknowledged_at,
            resolved_at=dispute.resolved_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to file dispute: {e}")
        raise HTTPException(status_code=500, detail="Failed to file dispute")


@router.get("", response_model=DisputeListResponse)
async def list_disputes(
    mtp_id: Optional[str] = Query(None, description="Filter by agent MTP ID"),
    org_id: Optional[str] = Query(None, description="Filter by organization ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List disputes with optional filters.

    Returns paginated list of disputes matching the criteria.
    """
    try:
        status_enum = DisputeStatus(status) if status else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    disputes = await dispute_service.list_disputes(
        mtp_id=mtp_id,
        org_id=org_id,
        status=status_enum,
        limit=limit,
        offset=offset
    )

    return DisputeListResponse(
        disputes=[
            DisputeResponse(
                id=d.id,
                dispute_number=d.dispute_number,
                complainant_type=d.complainant_type,
                respondent_mtp_id=d.respondent_mtp_id,
                incident_category=d.incident_category,
                incident_description=d.incident_description,
                claimed_damages=d.claimed_damages,
                currency=d.currency,
                status=d.status.value,
                finding=d.finding,
                finding_details=d.finding_details,
                remedy_ordered=d.remedy_ordered,
                trust_score_impact=d.trust_score_impact,
                filed_at=d.filed_at,
                acknowledged_at=d.acknowledged_at,
                resolved_at=d.resolved_at
            )
            for d in disputes
        ],
        total=len(disputes),
        limit=limit,
        offset=offset
    )


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(dispute_id: str):
    """
    Get dispute details by ID.

    Returns the full dispute record including all evidence and status.
    """
    dispute = await dispute_service.get_dispute(dispute_id)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    return DisputeResponse(
        id=dispute.id,
        dispute_number=dispute.dispute_number,
        complainant_type=dispute.complainant_type,
        respondent_mtp_id=dispute.respondent_mtp_id,
        incident_category=dispute.incident_category,
        incident_description=dispute.incident_description,
        claimed_damages=dispute.claimed_damages,
        currency=dispute.currency,
        status=dispute.status.value,
        finding=dispute.finding,
        finding_details=dispute.finding_details,
        remedy_ordered=dispute.remedy_ordered,
        trust_score_impact=dispute.trust_score_impact,
        filed_at=dispute.filed_at,
        acknowledged_at=dispute.acknowledged_at,
        resolved_at=dispute.resolved_at
    )


@router.get("/number/{dispute_number}", response_model=DisputeResponse)
async def get_dispute_by_number(dispute_number: str):
    """
    Get dispute details by dispute number (e.g., DISP-2025-000001).
    """
    dispute = await dispute_service.get_dispute_by_number(dispute_number)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    return DisputeResponse(
        id=dispute.id,
        dispute_number=dispute.dispute_number,
        complainant_type=dispute.complainant_type,
        respondent_mtp_id=dispute.respondent_mtp_id,
        incident_category=dispute.incident_category,
        incident_description=dispute.incident_description,
        claimed_damages=dispute.claimed_damages,
        currency=dispute.currency,
        status=dispute.status.value,
        finding=dispute.finding,
        finding_details=dispute.finding_details,
        remedy_ordered=dispute.remedy_ordered,
        trust_score_impact=dispute.trust_score_impact,
        filed_at=dispute.filed_at,
        acknowledged_at=dispute.acknowledged_at,
        resolved_at=dispute.resolved_at
    )


@router.post("/{dispute_id}/respond", response_model=DisputeResponse)
async def submit_response(dispute_id: str, request: SubmitResponseRequest):
    """
    Submit a response to a dispute (respondent organization).

    The respondent can provide evidence and a statement in their defense.
    """
    dispute = await dispute_service.get_dispute(dispute_id)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status not in [DisputeStatus.FILED, DisputeStatus.PENDING_RESPONSE]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot respond to dispute in status: {dispute.status.value}"
        )

    try:
        updated = await dispute_service.submit_response(
            dispute_id=dispute_id,
            respondent_evidence=request.evidence,
            response_statement=request.response_statement
        )

        return DisputeResponse(
            id=updated.id,
            dispute_number=updated.dispute_number,
            complainant_type=updated.complainant_type,
            respondent_mtp_id=updated.respondent_mtp_id,
            incident_category=updated.incident_category,
            incident_description=updated.incident_description,
            claimed_damages=updated.claimed_damages,
            currency=updated.currency,
            status=updated.status.value,
            finding=updated.finding,
            finding_details=updated.finding_details,
            remedy_ordered=updated.remedy_ordered,
            trust_score_impact=updated.trust_score_impact,
            filed_at=updated.filed_at,
            acknowledged_at=updated.acknowledged_at,
            resolved_at=updated.resolved_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(dispute_id: str, request: ResolveDisputeRequest):
    """
    Resolve a dispute with a finding (arbitrator only).

    This endpoint should be protected and only accessible to authorized arbitrators.
    """
    dispute = await dispute_service.get_dispute(dispute_id)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.CLOSED]:
        raise HTTPException(
            status_code=400,
            detail=f"Dispute already {dispute.status.value}"
        )

    valid_findings = ['UPHELD', 'DISMISSED', 'PARTIAL']
    if request.finding not in valid_findings:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid finding. Must be one of: {valid_findings}"
        )

    try:
        resolved = await dispute_service.resolve_dispute(
            dispute_id=dispute_id,
            finding=request.finding,
            finding_details=request.finding_details,
            remedy_ordered=request.remedy_ordered,
            trust_score_impact=request.trust_score_impact
        )

        return DisputeResponse(
            id=resolved.id,
            dispute_number=resolved.dispute_number,
            complainant_type=resolved.complainant_type,
            respondent_mtp_id=resolved.respondent_mtp_id,
            incident_category=resolved.incident_category,
            incident_description=resolved.incident_description,
            claimed_damages=resolved.claimed_damages,
            currency=resolved.currency,
            status=resolved.status.value,
            finding=resolved.finding,
            finding_details=resolved.finding_details,
            remedy_ordered=resolved.remedy_ordered,
            trust_score_impact=resolved.trust_score_impact,
            filed_at=resolved.filed_at,
            acknowledged_at=resolved.acknowledged_at,
            resolved_at=resolved.resolved_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{dispute_id}/appeal", response_model=DisputeResponse)
async def appeal_dispute(dispute_id: str, request: AppealRequest):
    """
    File an appeal against a dispute resolution.

    Appeals must be filed within 14 days of resolution.
    """
    try:
        appealed = await dispute_service.appeal_dispute(
            dispute_id=dispute_id,
            appeal_reason=request.appeal_reason,
            additional_evidence=request.additional_evidence
        )

        return DisputeResponse(
            id=appealed.id,
            dispute_number=appealed.dispute_number,
            complainant_type=appealed.complainant_type,
            respondent_mtp_id=appealed.respondent_mtp_id,
            incident_category=appealed.incident_category,
            incident_description=appealed.incident_description,
            claimed_damages=appealed.claimed_damages,
            currency=appealed.currency,
            status=appealed.status.value,
            finding=appealed.finding,
            finding_details=appealed.finding_details,
            remedy_ordered=appealed.remedy_ordered,
            trust_score_impact=appealed.trust_score_impact,
            filed_at=appealed.filed_at,
            acknowledged_at=appealed.acknowledged_at,
            resolved_at=appealed.resolved_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dispute_id}/evidence")
async def get_dispute_evidence(dispute_id: str):
    """
    Get all audit event evidence for a dispute.

    Returns the immutable audit trail linked to this dispute,
    including blockchain anchoring proof.
    """
    dispute = await dispute_service.get_dispute(dispute_id)

    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    evidence = await dispute_service.get_audit_evidence(dispute_id)

    return {
        "dispute_number": dispute.dispute_number,
        "audit_events": evidence,
        "event_count": len(evidence),
        "complainant_evidence": dispute.complainant_evidence,
        "respondent_evidence": dispute.respondent_evidence
    }
