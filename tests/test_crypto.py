"""Unit Tests for Cryptographic Utilities"""
import pytest
from mtp_core.core.crypto import (
    generate_keypair,
    sign_message,
    verify_signature,
    hash_data,
    generate_mtp_id
)


class TestEd25519Cryptography:
    """Tests for Ed25519 signature operations"""

    def test_generate_keypair_returns_valid_keys(self):
        """Test that keypair generation produces valid hex strings"""
        private_key, public_key = generate_keypair()

        # Ed25519 private key is 32 bytes = 64 hex chars
        assert len(private_key) == 64
        assert all(c in '0123456789abcdef' for c in private_key)

        # Ed25519 public key is 32 bytes = 64 hex chars
        assert len(public_key) == 64
        assert all(c in '0123456789abcdef' for c in public_key)

    def test_generate_keypair_is_unique(self):
        """Test that each keypair is unique"""
        keys1 = generate_keypair()
        keys2 = generate_keypair()

        assert keys1[0] != keys2[0]  # Different private keys
        assert keys1[1] != keys2[1]  # Different public keys

    def test_sign_message_produces_valid_signature(self):
        """Test that signing produces a base64-encoded signature"""
        private_key, _ = generate_keypair()
        message = b"Test message for signing"

        signature = sign_message(private_key, message)

        # Signature should be base64-encoded
        assert isinstance(signature, str)
        # Ed25519 signature is 64 bytes, base64 encoded is ~88 chars
        assert len(signature) > 80

    def test_verify_signature_accepts_valid_signature(self):
        """Test that a valid signature is accepted"""
        private_key, public_key = generate_keypair()
        message = b"This is a test message"

        signature = sign_message(private_key, message)
        is_valid = verify_signature(public_key, message, signature)

        assert is_valid is True

    def test_verify_signature_rejects_invalid_signature(self):
        """Test that an invalid signature is rejected"""
        _, public_key = generate_keypair()
        message = b"This is a test message"

        fake_signature = "aW52YWxpZF9zaWduYXR1cmU="  # "invalid_signature" in base64
        is_valid = verify_signature(public_key, message, fake_signature)

        assert is_valid is False

    def test_verify_signature_rejects_wrong_message(self):
        """Test that signature doesn't verify for different message"""
        private_key, public_key = generate_keypair()
        message = b"Original message"
        wrong_message = b"Different message"

        signature = sign_message(private_key, message)
        is_valid = verify_signature(public_key, wrong_message, signature)

        assert is_valid is False

    def test_verify_signature_rejects_wrong_key(self):
        """Test that signature doesn't verify with different public key"""
        private_key1, _ = generate_keypair()
        _, public_key2 = generate_keypair()
        message = b"Test message"

        signature = sign_message(private_key1, message)
        is_valid = verify_signature(public_key2, message, signature)

        assert is_valid is False

    def test_verify_signature_handles_malformed_input(self):
        """Test that malformed inputs return False, not exceptions"""
        # Invalid hex public key
        is_valid = verify_signature("invalid_hex", b"message", "signature")
        assert is_valid is False

        # Invalid base64 signature
        _, public_key = generate_keypair()
        is_valid = verify_signature(public_key, b"message", "not_base64!!!")
        assert is_valid is False


class TestHashData:
    """Tests for SHA-256 hashing"""

    def test_hash_data_returns_hex_string(self):
        """Test that hash returns a hex string"""
        data = b"Test data"
        result = hash_data(data)

        # SHA-256 produces 32 bytes = 64 hex chars
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)

    def test_hash_data_is_deterministic(self):
        """Test that same input produces same hash"""
        data = b"Consistent data"

        hash1 = hash_data(data)
        hash2 = hash_data(data)

        assert hash1 == hash2

    def test_hash_data_is_unique(self):
        """Test that different inputs produce different hashes"""
        hash1 = hash_data(b"Data 1")
        hash2 = hash_data(b"Data 2")

        assert hash1 != hash2

    def test_hash_data_empty_input(self):
        """Test hashing empty data"""
        result = hash_data(b"")

        # SHA-256 of empty string is well-known
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected


class TestMTPIdGeneration:
    """Tests for MTP ID generation"""

    def test_mtp_id_format(self):
        """Test that MTP ID follows correct format"""
        mtp_id = generate_mtp_id("org-123", "llm_agent")

        # Format: MTP-{6 char org hash}-{6 char random}
        assert mtp_id.startswith("MTP-")
        parts = mtp_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 6  # org hash
        assert len(parts[2]) == 6  # random suffix

    def test_mtp_id_includes_org_hash(self):
        """Test that same org produces same hash prefix"""
        mtp_id1 = generate_mtp_id("org-abc", "type1")
        mtp_id2 = generate_mtp_id("org-abc", "type2")

        # Same org should produce same org hash
        org_hash1 = mtp_id1.split("-")[1]
        org_hash2 = mtp_id2.split("-")[1]
        assert org_hash1 == org_hash2

    def test_mtp_id_is_unique(self):
        """Test that each MTP ID is unique"""
        ids = [generate_mtp_id("org", "type") for _ in range(100)]
        unique_ids = set(ids)

        assert len(unique_ids) == 100  # All should be unique

    def test_mtp_id_different_orgs(self):
        """Test that different orgs produce different hash prefixes"""
        mtp_id1 = generate_mtp_id("org-one", "type")
        mtp_id2 = generate_mtp_id("org-two", "type")

        org_hash1 = mtp_id1.split("-")[1]
        org_hash2 = mtp_id2.split("-")[1]

        assert org_hash1 != org_hash2


class TestMessageConstruction:
    """Tests for canonical message format used in signature verification"""

    def test_canonical_message_format(self):
        """Test the format used for signing requests"""
        import json

        mtp_id = "MTP-abc123-def456"
        timestamp = "2025-01-15T10:30:00Z"
        request_body = {"action": "transfer", "amount": 100}

        body_json = json.dumps(request_body, sort_keys=True)
        message_str = f"{mtp_id}|{timestamp}|{body_json}"
        message = message_str.encode('utf-8')

        # Verify format
        assert b"|" in message
        parts = message.decode().split("|")
        assert len(parts) == 3
        assert parts[0] == mtp_id
        assert parts[1] == timestamp

    def test_canonical_message_is_deterministic(self):
        """Test that message construction is deterministic"""
        import json

        mtp_id = "MTP-test-123456"
        timestamp = "2025-01-15T10:30:00Z"

        # Same dict with keys in different order
        body1 = {"b": 2, "a": 1}
        body2 = {"a": 1, "b": 2}

        msg1 = f"{mtp_id}|{timestamp}|{json.dumps(body1, sort_keys=True)}"
        msg2 = f"{mtp_id}|{timestamp}|{json.dumps(body2, sort_keys=True)}"

        assert msg1 == msg2  # sort_keys ensures determinism
