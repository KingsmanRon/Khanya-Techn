"""Certification Service - MTP-CERT Implementation

Jurisdiction and use-case specific certifications for AI agents.
Certifications validate that an agent meets specific regulatory
and operational requirements.

Available Certifications:
- MTP-CERT-ZA-FIN: South Africa Financial Services
- MTP-CERT-ZA-ECOM: South Africa E-Commerce
- MTP-CERT-EU-AI: EU AI Act Compliance
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import hashlib

from mtp_core.db.postgres import db_pool

logger = logging.getLogger(__name__)


class CertificationType(str, Enum):
    """Available certification types"""
    ZA_FIN = "MTP-CERT-ZA-FIN"      # South Africa Financial Services
    ZA_ECOM = "MTP-CERT-ZA-ECOM"    # South Africa E-Commerce
    ZA_HEALTH = "MTP-CERT-ZA-HEALTH"  # South Africa Healthcare
    EU_AI = "MTP-CERT-EU-AI"        # EU AI Act Compliance
    POPIA = "MTP-CERT-POPIA"        # POPIA Data Protection
    GENERIC = "MTP-CERT-GENERIC"    # Generic Certification


class CertificationStatus(str, Enum):
    """Certification lifecycle status"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"


# Certification requirements and metadata
CERTIFICATION_DEFINITIONS = {
    CertificationType.ZA_FIN: {
        "name": "South Africa Financial Services",
        "jurisdiction": "ZA",
        "description": "Certification for AI agents operating in South African financial services",
        "validity_days": 365,
        "requirements": {
            "min_trust_score": 700,
            "min_tenure_days": 90,
            "max_error_rate": 0.02,
            "required_disclosures": True,
            "transaction_limit": 500000,  # R500,000/day
            "human_oversight_required": True
        },
        "regulatory_bodies": ["SARB", "FSCA"],
        "compliance_standards": ["SARB Compliance", "FSCA Conduct Standards", "POPIA"]
    },
    CertificationType.ZA_ECOM: {
        "name": "South Africa E-Commerce",
        "jurisdiction": "ZA",
        "description": "Certification for AI agents in South African e-commerce",
        "validity_days": 365,
        "requirements": {
            "min_trust_score": 600,
            "min_tenure_days": 30,
            "max_error_rate": 0.05,
            "dispute_resolution_required": True,
            "refund_authority_limit": 10000  # R10,000
        },
        "regulatory_bodies": ["Consumer Protection Commission"],
        "compliance_standards": ["CPA", "ECT Act", "POPIA"]
    },
    CertificationType.ZA_HEALTH: {
        "name": "South Africa Healthcare",
        "jurisdiction": "ZA",
        "description": "Certification for AI agents in healthcare settings",
        "validity_days": 180,
        "requirements": {
            "min_trust_score": 850,
            "min_tenure_days": 180,
            "max_error_rate": 0.01,
            "human_approval_required": True,
            "data_retention_years": 10
        },
        "regulatory_bodies": ["HPCSA", "Information Regulator"],
        "compliance_standards": ["NHA", "POPIA", "HPCSA Guidelines"]
    },
    CertificationType.EU_AI: {
        "name": "EU AI Act Compliance",
        "jurisdiction": "EU",
        "description": "Certification for EU AI Act high-risk AI systems",
        "validity_days": 365,
        "requirements": {
            "min_trust_score": 750,
            "risk_assessment_required": True,
            "transparency_requirements": True,
            "human_oversight_provisions": True,
            "technical_documentation": True,
            "conformity_assessment": True
        },
        "regulatory_bodies": ["National Competent Authorities"],
        "compliance_standards": ["EU AI Act", "GDPR"]
    },
    CertificationType.POPIA: {
        "name": "POPIA Data Protection",
        "jurisdiction": "ZA",
        "description": "Certification for POPIA compliance",
        "validity_days": 365,
        "requirements": {
            "min_trust_score": 600,
            "data_protection_officer": True,
            "privacy_impact_assessment": True,
            "consent_management": True,
            "data_subject_rights": True
        },
        "regulatory_bodies": ["Information Regulator"],
        "compliance_standards": ["POPIA"]
    },
    CertificationType.GENERIC: {
        "name": "Generic MTP Certification",
        "jurisdiction": "GLOBAL",
        "description": "Basic MTP certification for general use",
        "validity_days": 365,
        "requirements": {
            "min_trust_score": 500,
            "min_tenure_days": 7,
            "identity_verified": True
        },
        "regulatory_bodies": [],
        "compliance_standards": ["MTP Protocol"]
    }
}


class CertificationService:
    """
    MTP-CERT Certification Manager

    Handles issuance, verification, and lifecycle management
    of compliance certifications for AI agents.
    """

    async def check_eligibility(
        self,
        mtp_id: str,
        cert_type: CertificationType
    ) -> Dict[str, Any]:
        """
        Check if an agent is eligible for a certification.

        Args:
            mtp_id: Agent's MTP identifier
            cert_type: Type of certification to check

        Returns:
            Eligibility result with details
        """
        definition = CERTIFICATION_DEFINITIONS.get(cert_type)
        if not definition:
            raise ValueError(f"Unknown certification type: {cert_type}")

        requirements = definition['requirements']
        results = {
            'eligible': True,
            'mtp_id': mtp_id,
            'cert_type': cert_type.value,
            'requirements_checked': [],
            'requirements_failed': []
        }

        # Get agent data
        agent = await self._get_agent(mtp_id)
        if not agent:
            return {
                'eligible': False,
                'error': f"Agent not found: {mtp_id}"
            }

        # Check trust score
        if 'min_trust_score' in requirements:
            min_score = requirements['min_trust_score']
            current_score = agent.get('trust_score', 0)
            passed = current_score >= min_score

            results['requirements_checked'].append({
                'requirement': 'min_trust_score',
                'required': min_score,
                'actual': current_score,
                'passed': passed
            })

            if not passed:
                results['eligible'] = False
                results['requirements_failed'].append('min_trust_score')

        # Check tenure
        if 'min_tenure_days' in requirements:
            min_days = requirements['min_tenure_days']
            registered_at = agent.get('registered_at')
            if registered_at:
                tenure = (datetime.now(timezone.utc) - registered_at).days
            else:
                tenure = 0

            passed = tenure >= min_days

            results['requirements_checked'].append({
                'requirement': 'min_tenure_days',
                'required': min_days,
                'actual': tenure,
                'passed': passed
            })

            if not passed:
                results['eligible'] = False
                results['requirements_failed'].append('min_tenure_days')

        # Check error rate
        if 'max_error_rate' in requirements:
            max_rate = requirements['max_error_rate']
            error_rate = await self._get_error_rate(mtp_id)
            passed = error_rate <= max_rate

            results['requirements_checked'].append({
                'requirement': 'max_error_rate',
                'required': f"<= {max_rate*100}%",
                'actual': f"{error_rate*100:.2f}%",
                'passed': passed
            })

            if not passed:
                results['eligible'] = False
                results['requirements_failed'].append('max_error_rate')

        # Check identity verification
        if requirements.get('identity_verified'):
            verified = agent.get('status') == 'ACTIVE'

            results['requirements_checked'].append({
                'requirement': 'identity_verified',
                'required': True,
                'actual': verified,
                'passed': verified
            })

            if not verified:
                results['eligible'] = False
                results['requirements_failed'].append('identity_verified')

        return results

    async def issue_certification(
        self,
        mtp_id: str,
        cert_type: CertificationType,
        issued_by: str = "MTP System",
        custom_expiry: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Issue a certification to an agent.

        Args:
            mtp_id: Agent's MTP identifier
            cert_type: Type of certification
            issued_by: Entity issuing the certification
            custom_expiry: Optional custom expiration date

        Returns:
            Issued certification details
        """
        # Check eligibility first
        eligibility = await self.check_eligibility(mtp_id, cert_type)
        if not eligibility.get('eligible'):
            raise ValueError(
                f"Agent not eligible for {cert_type.value}: "
                f"Failed requirements: {eligibility.get('requirements_failed')}"
            )

        definition = CERTIFICATION_DEFINITIONS[cert_type]

        # Calculate expiry
        if custom_expiry:
            expires_at = custom_expiry
        else:
            validity_days = definition['validity_days']
            expires_at = datetime.now(timezone.utc) + timedelta(days=validity_days)

        # Generate certificate hash
        cert_id = str(uuid.uuid4())
        cert_data = f"{mtp_id}:{cert_type.value}:{cert_id}:{datetime.now(timezone.utc).isoformat()}"
        certificate_hash = hashlib.sha256(cert_data.encode()).hexdigest()

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO certifications (
                    id, mtp_id, cert_type, cert_name, jurisdiction,
                    issued_at, expires_at, status, requirements_met,
                    issued_by, certificate_hash
                ) VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8, $9, $10)
                """,
                uuid.UUID(cert_id),
                mtp_id,
                cert_type.value,
                definition['name'],
                definition['jurisdiction'],
                expires_at,
                CertificationStatus.ACTIVE.value,
                eligibility,
                issued_by,
                certificate_hash
            )

        logger.info(f"Certification {cert_type.value} issued to agent {mtp_id}")

        return {
            'certification_id': cert_id,
            'mtp_id': mtp_id,
            'cert_type': cert_type.value,
            'cert_name': definition['name'],
            'jurisdiction': definition['jurisdiction'],
            'issued_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': expires_at.isoformat(),
            'status': CertificationStatus.ACTIVE.value,
            'certificate_hash': certificate_hash,
            'issued_by': issued_by,
            'compliance_standards': definition['compliance_standards']
        }

    async def get_certification(self, cert_id: str) -> Optional[Dict[str, Any]]:
        """Get certification by ID"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, mtp_id, cert_type, cert_name, jurisdiction,
                       issued_at, expires_at, status, requirements_met,
                       issued_by, certificate_hash, blockchain_tx_hash
                FROM certifications WHERE id = $1
                """,
                uuid.UUID(cert_id)
            )

            if not row:
                return None

            return self._row_to_dict(row)

    async def get_agent_certifications(
        self,
        mtp_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all certifications for an agent"""
        query = """
            SELECT id, mtp_id, cert_type, cert_name, jurisdiction,
                   issued_at, expires_at, status, requirements_met,
                   issued_by, certificate_hash, blockchain_tx_hash
            FROM certifications
            WHERE mtp_id = $1
        """

        if active_only:
            query += " AND status = 'ACTIVE' AND (expires_at IS NULL OR expires_at > NOW())"

        query += " ORDER BY issued_at DESC"

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, mtp_id)
            return [self._row_to_dict(row) for row in rows]

    async def verify_certification(
        self,
        mtp_id: str,
        cert_type: CertificationType
    ) -> Dict[str, Any]:
        """
        Verify if an agent has a valid certification.

        Args:
            mtp_id: Agent's MTP identifier
            cert_type: Type of certification to verify

        Returns:
            Verification result
        """
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, cert_type, cert_name, issued_at, expires_at,
                       status, certificate_hash
                FROM certifications
                WHERE mtp_id = $1 AND cert_type = $2
                  AND status = 'ACTIVE'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY issued_at DESC
                LIMIT 1
                """,
                mtp_id, cert_type.value
            )

            if row:
                return {
                    'verified': True,
                    'mtp_id': mtp_id,
                    'cert_type': cert_type.value,
                    'certification_id': str(row['id']),
                    'cert_name': row['cert_name'],
                    'issued_at': row['issued_at'].isoformat(),
                    'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
                    'certificate_hash': row['certificate_hash']
                }
            else:
                return {
                    'verified': False,
                    'mtp_id': mtp_id,
                    'cert_type': cert_type.value,
                    'reason': 'No active certification found'
                }

    async def revoke_certification(
        self,
        cert_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Revoke a certification"""
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE certifications
                SET status = $1
                WHERE id = $2
                """,
                CertificationStatus.REVOKED.value,
                uuid.UUID(cert_id)
            )

            if result == "UPDATE 0":
                raise ValueError(f"Certification not found: {cert_id}")

        logger.info(f"Certification {cert_id} revoked: {reason}")

        return {
            'certification_id': cert_id,
            'status': CertificationStatus.REVOKED.value,
            'reason': reason
        }

    async def renew_certification(
        self,
        mtp_id: str,
        cert_type: CertificationType
    ) -> Dict[str, Any]:
        """Renew an existing certification"""
        # Check current certification exists
        current = await self.verify_certification(mtp_id, cert_type)

        if current.get('verified'):
            # Revoke current
            await self.revoke_certification(
                current['certification_id'],
                "Renewed"
            )

        # Issue new certification
        return await self.issue_certification(mtp_id, cert_type)

    async def _get_agent(self, mtp_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details"""
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT mtp_id, trust_score, registered_at, status,
                       jurisdiction, transaction_limit_daily
                FROM agents WHERE mtp_id = $1
                """,
                mtp_id
            )
            return dict(row) if row else None

    async def _get_error_rate(self, mtp_id: str, days: int = 90) -> float:
        """Get agent's error rate"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status IN ('FAILURE', 'ERROR')) as errors
                FROM audit_events
                WHERE mtp_id = $1 AND timestamp >= $2
                """,
                mtp_id, start_date
            )

            total = stats['total'] or 0
            errors = stats['errors'] or 0

            return errors / total if total > 0 else 0.0

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        return {
            'certification_id': str(row['id']),
            'mtp_id': row['mtp_id'],
            'cert_type': row['cert_type'],
            'cert_name': row['cert_name'],
            'jurisdiction': row['jurisdiction'],
            'issued_at': row['issued_at'].isoformat(),
            'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
            'status': row['status'],
            'requirements_met': row['requirements_met'],
            'issued_by': row['issued_by'],
            'certificate_hash': row['certificate_hash'],
            'blockchain_tx_hash': row['blockchain_tx_hash']
        }

    def get_available_certifications(self) -> List[Dict[str, Any]]:
        """Get list of all available certifications"""
        return [
            {
                'cert_type': cert_type.value,
                'name': definition['name'],
                'jurisdiction': definition['jurisdiction'],
                'description': definition['description'],
                'validity_days': definition['validity_days'],
                'requirements': definition['requirements'],
                'compliance_standards': definition['compliance_standards']
            }
            for cert_type, definition in CERTIFICATION_DEFINITIONS.items()
        ]


# Global service instance
certification_service = CertificationService()
