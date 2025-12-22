"""Ed25519 Cryptographic Utilities for Agent Identity"""
import hashlib
import secrets
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64


def generate_keypair() -> Tuple[str, str]:
    """
    Generate Ed25519 keypair for agent identity.
    
    Returns:
        Tuple of (private_key_hex, public_key_hex)
    
    NOTE: In production, agents generate their own keys.
    This function is for testing/demo purposes only.
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    return private_bytes.hex(), public_bytes.hex()


def sign_message(private_key_hex: str, message: bytes) -> str:
    """
    Sign a message using Ed25519 private key.
    
    Args:
        private_key_hex: Hex-encoded private key
        message: Message bytes to sign
    
    Returns:
        Base64-encoded signature
    """
    private_bytes = bytes.fromhex(private_key_hex)
    private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
    
    signature = private_key.sign(message)
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(
    public_key_hex: str,
    message: bytes,
    signature_b64: str
) -> bool:
    """
    Verify Ed25519 signature.
    
    Args:
        public_key_hex: Hex-encoded public key
        message: Original message bytes
        signature_b64: Base64-encoded signature
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        public_bytes = bytes.fromhex(public_key_hex)
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, message)
        return True
    except (ValueError, InvalidSignature):
        return False


def hash_data(data: bytes) -> str:
    """SHA-256 hash of data, returns hex string."""
    return hashlib.sha256(data).hexdigest()


def generate_mtp_id(org_id: str, agent_type: str) -> str:
    """
    Generate a globally unique MTP ID for an agent.
    
    Format: MTP-{org_hash}-{random}
    Example: MTP-a3f5b2-7k9m2p
    """
    org_hash = hashlib.sha256(org_id.encode()).hexdigest()[:6]
    random_suffix = secrets.token_hex(3)
    return f"MTP-{org_hash}-{random_suffix}"
