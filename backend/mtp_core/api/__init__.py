"""MTP API Module

API endpoints for the Machine Trust Protocol:
- gateway: Kill switch proxy for AI agent requests
- identity: Agent registration and verification
- audit: Audit event logging and querying
- disputes: Dispute resolution (MTP-RESOLVE)
- insurance: Risk profiling and insurance (MTP-INSURE)
- api_keys: API key management
- trust: Trust score queries and management (MTP-TRUST)
- certifications: Certification management (MTP-CERT)
"""

from mtp_core.api import gateway
from mtp_core.api import identity
from mtp_core.api import audit
from mtp_core.api import disputes
from mtp_core.api import insurance
from mtp_core.api import api_keys
from mtp_core.api import trust
from mtp_core.api import certifications

__all__ = [
    'gateway',
    'identity',
    'audit',
    'disputes',
    'insurance',
    'api_keys',
    'trust',
    'certifications',
]
