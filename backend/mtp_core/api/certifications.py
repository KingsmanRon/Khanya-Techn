"""Certification API Endpoints - MTP-CERT

API endpoints for certification management and verification.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from mtp_core.services.certification import (
    certification_service,
    CertificationType,
    CertificationStatus,
    CERTIFICATION_DEFINITIONS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certifications", tags=["Certifications"])


# Request/Response Models
class EligibilityCheckResponse(BaseModel):
    """Eligibility check response"""
    eligible: bool
    mtp_id: str
    cert_type: str
    requirements_checked: List[dict]
    requirements_failed: List[str]


class IssueCertificationRequest(BaseModel):
    """Request to issue a certification"""
    cert_type: str = Field(
        ...,
        description="Certification type (e.g., MTP-CERT-ZA-FIN)"
    )
    issued_by: str = Field(
        default="MTP System",
        description="Entity issuing the certification"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cert_type": "MTP-CERT-ZA-ECOM",
                "issued_by": "MTP Certification Authority"
            }
        }


class CertificationResponse(BaseModel):
    """Certification response"""
    certification_id: str
    mtp_id: str
    cert_type: str
    cert_name: str
    jurisdiction: str
    issued_at: str
    expires_at: Optional[str]
    status: str
    certificate_hash: Optional[str]
    issued_by: Optional[str]


class CertificationListResponse(BaseModel):
    """List of certifications"""
    certifications: List[CertificationResponse]
    total: int


class VerificationResponse(BaseModel):
    """Certification verification response"""
    verified: bool
    mtp_id: str
    cert_type: str
    certification_id: Optional[str] = None
    cert_name: Optional[str] = None
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    certificate_hash: Optional[str] = None
    reason: Optional[str] = None


class RevokeCertificationRequest(BaseModel):
    """Request to revoke a certification"""
    reason: str = Field(..., description="Reason for revocation")


class CertificationDefinition(BaseModel):
    """Certification definition"""
    cert_type: str
    name: str
    jurisdiction: str
    description: str
    validity_days: int
    requirements: dict
    compliance_standards: List[str]


# API Endpoints
@router.get("/available", response_model=List[CertificationDefinition])
async def get_available_certifications():
    """
    Get list of all available certification types.

    Returns definitions, requirements, and compliance standards for each
    certification type that can be issued.
    """
    certs = certification_service.get_available_certifications()
    return [CertificationDefinition(**c) for c in certs]


@router.get("/agent/{mtp_id}", response_model=CertificationListResponse)
async def get_agent_certifications(
    mtp_id: str,
    active_only: bool = Query(True, description="Only return active certifications")
):
    """
    Get all certifications for an agent.

    Returns the list of certifications held by the agent.
    """
    certs = await certification_service.get_agent_certifications(mtp_id, active_only)

    return CertificationListResponse(
        certifications=[
            CertificationResponse(
                certification_id=c['certification_id'],
                mtp_id=c['mtp_id'],
                cert_type=c['cert_type'],
                cert_name=c['cert_name'],
                jurisdiction=c['jurisdiction'],
                issued_at=c['issued_at'],
                expires_at=c['expires_at'],
                status=c['status'],
                certificate_hash=c['certificate_hash'],
                issued_by=c['issued_by']
            )
            for c in certs
        ],
        total=len(certs)
    )


@router.get("/agent/{mtp_id}/eligibility/{cert_type}", response_model=EligibilityCheckResponse)
async def check_eligibility(mtp_id: str, cert_type: str):
    """
    Check if an agent is eligible for a certification.

    Returns detailed breakdown of requirements checked and which ones failed.
    """
    try:
        cert_type_enum = CertificationType(cert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid certification type: {cert_type}. "
                   f"Valid types: {[c.value for c in CertificationType]}"
        )

    try:
        result = await certification_service.check_eligibility(mtp_id, cert_type_enum)

        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])

        return EligibilityCheckResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agent/{mtp_id}/issue", response_model=CertificationResponse, status_code=201)
async def issue_certification(mtp_id: str, request: IssueCertificationRequest):
    """
    Issue a certification to an agent.

    The agent must meet all requirements for the certification type.
    """
    try:
        cert_type_enum = CertificationType(request.cert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid certification type: {request.cert_type}. "
                   f"Valid types: {[c.value for c in CertificationType]}"
        )

    try:
        result = await certification_service.issue_certification(
            mtp_id=mtp_id,
            cert_type=cert_type_enum,
            issued_by=request.issued_by
        )

        logger.info(f"Certification {request.cert_type} issued to {mtp_id}")

        return CertificationResponse(
            certification_id=result['certification_id'],
            mtp_id=result['mtp_id'],
            cert_type=result['cert_type'],
            cert_name=result['cert_name'],
            jurisdiction=result['jurisdiction'],
            issued_at=result['issued_at'],
            expires_at=result['expires_at'],
            status=result['status'],
            certificate_hash=result['certificate_hash'],
            issued_by=result['issued_by']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify/{mtp_id}/{cert_type}", response_model=VerificationResponse)
async def verify_certification(mtp_id: str, cert_type: str):
    """
    Verify if an agent has a valid certification.

    Returns verification status and certification details if valid.
    """
    try:
        cert_type_enum = CertificationType(cert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid certification type: {cert_type}"
        )

    result = await certification_service.verify_certification(mtp_id, cert_type_enum)
    return VerificationResponse(**result)


@router.get("/{cert_id}", response_model=CertificationResponse)
async def get_certification(cert_id: str):
    """
    Get certification details by ID.
    """
    cert = await certification_service.get_certification(cert_id)

    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")

    return CertificationResponse(
        certification_id=cert['certification_id'],
        mtp_id=cert['mtp_id'],
        cert_type=cert['cert_type'],
        cert_name=cert['cert_name'],
        jurisdiction=cert['jurisdiction'],
        issued_at=cert['issued_at'],
        expires_at=cert['expires_at'],
        status=cert['status'],
        certificate_hash=cert['certificate_hash'],
        issued_by=cert['issued_by']
    )


@router.post("/{cert_id}/revoke")
async def revoke_certification(cert_id: str, request: RevokeCertificationRequest):
    """
    Revoke a certification.

    This immediately invalidates the certification.
    """
    try:
        result = await certification_service.revoke_certification(cert_id, request.reason)
        logger.info(f"Certification {cert_id} revoked: {request.reason}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/agent/{mtp_id}/renew/{cert_type}", response_model=CertificationResponse)
async def renew_certification(mtp_id: str, cert_type: str):
    """
    Renew an existing certification.

    This revokes the current certification and issues a new one
    if the agent still meets requirements.
    """
    try:
        cert_type_enum = CertificationType(cert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid certification type: {cert_type}"
        )

    try:
        result = await certification_service.renew_certification(mtp_id, cert_type_enum)

        logger.info(f"Certification {cert_type} renewed for {mtp_id}")

        return CertificationResponse(
            certification_id=result['certification_id'],
            mtp_id=result['mtp_id'],
            cert_type=result['cert_type'],
            cert_name=result['cert_name'],
            jurisdiction=result['jurisdiction'],
            issued_at=result['issued_at'],
            expires_at=result['expires_at'],
            status=result['status'],
            certificate_hash=result['certificate_hash'],
            issued_by=result['issued_by']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/types/{cert_type}/requirements")
async def get_certification_requirements(cert_type: str):
    """
    Get detailed requirements for a certification type.
    """
    try:
        cert_type_enum = CertificationType(cert_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid certification type: {cert_type}"
        )

    definition = CERTIFICATION_DEFINITIONS.get(cert_type_enum)
    if not definition:
        raise HTTPException(status_code=404, detail="Certification definition not found")

    return {
        "cert_type": cert_type,
        "name": definition['name'],
        "jurisdiction": definition['jurisdiction'],
        "description": definition['description'],
        "validity_days": definition['validity_days'],
        "requirements": definition['requirements'],
        "regulatory_bodies": definition['regulatory_bodies'],
        "compliance_standards": definition['compliance_standards']
    }
