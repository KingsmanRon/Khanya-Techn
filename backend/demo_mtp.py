#!/usr/bin/env python3
"""
MTP Demo Script - Test Core Functionality

This script demonstrates:
1. Ed25519 key generation
2. Agent registration
3. Request signing
4. Merkle tree creation
5. Blockchain anchoring (simulated)
"""

import asyncio
import json
from datetime import datetime, timezone

from mtp_core.core.crypto import generate_keypair, sign_message, verify_signature, generate_mtp_id, hash_data
from mtp_core.core.merkle import MerkleTree


def demo_cryptography():
    """Demo Ed25519 signature generation and verification"""
    print("=" * 60)
    print("1. CRYPTOGRAPHY DEMO - Ed25519 Signatures")
    print("=" * 60)
    
    # Generate keypair
    private_key, public_key = generate_keypair()
    print(f"\n✅ Generated Ed25519 keypair:")
    print(f"   Private Key: {private_key[:32]}...")
    print(f"   Public Key:  {public_key}")
    
    # Sign a message
    message = b"Transfer R500 from Account A to Account B"
    signature = sign_message(private_key, message)
    print(f"\n✅ Signed message:")
    print(f"   Message:   {message.decode()}")
    print(f"   Signature: {signature[:32]}...")
    
    # Verify signature
    is_valid = verify_signature(public_key, message, signature)
    print(f"\n✅ Signature verification: {is_valid}")
    
    # Test invalid signature
    fake_signature = "invalid_signature_base64=="
    is_invalid = verify_signature(public_key, message, fake_signature)
    print(f"❌ Invalid signature verification: {is_invalid}")
    
    return private_key, public_key


def demo_mtp_id_generation():
    """Demo MTP ID generation"""
    print("\n" + "=" * 60)
    print("2. MTP ID GENERATION")
    print("=" * 60)
    
    org_id = "org-fnb-001"
    agent_type = "customer_service_llm"
    
    mtp_id = generate_mtp_id(org_id, agent_type)
    print(f"\n✅ Generated MTP ID: {mtp_id}")
    print(f"   Format: MTP-{{org_hash}}-{{random}}")
    print(f"   Org ID: {org_id}")
    print(f"   Agent Type: {agent_type}")
    
    return mtp_id


def demo_request_signing(private_key: str, mtp_id: str):
    """Demo how agents sign requests"""
    print("\n" + "=" * 60)
    print("3. REQUEST SIGNING DEMO")
    print("=" * 60)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    request_body = {
        "from_account": "12345",
        "to_account": "67890",
        "amount": 500
    }
    
    # Construct canonical message
    body_json = json.dumps(request_body, sort_keys=True)
    message_str = f"{mtp_id}|{timestamp}|{body_json}"
    message_bytes = message_str.encode('utf-8')
    
    print(f"\n✅ Request details:")
    print(f"   MTP ID: {mtp_id}")
    print(f"   Timestamp: {timestamp}")
    print(f"   Body: {body_json}")
    
    # Sign the message
    signature = sign_message(private_key, message_bytes)
    
    print(f"\n✅ Request signature:")
    print(f"   Canonical message: {message_str}")
    print(f"   Signature: {signature[:32]}...")
    
    print(f"\n✅ HTTP Headers to send:")
    print(f"   X-MTP-ID: {mtp_id}")
    print(f"   X-MTP-Signature: {signature[:32]}...")
    print(f"   X-MTP-Timestamp: {timestamp}")
    print(f"   X-MTP-Action: transfer_funds")
    print(f"   X-MTP-Transaction-Value: 500.0")


def demo_merkle_tree():
    """Demo Merkle tree creation and proof verification"""
    print("\n" + "=" * 60)
    print("4. MERKLE TREE DEMO - Audit Trail Batching")
    print("=" * 60)
    
    # Simulate 5 audit events
    event_ids = [
        hash_data(f"event_{i}".encode())
        for i in range(5)
    ]
    
    print(f"\n✅ Created batch of {len(event_ids)} events:")
    for i, event_id in enumerate(event_ids):
        print(f"   Event {i+1}: {event_id[:16]}...")
    
    # Create Merkle tree
    merkle_tree = MerkleTree(event_ids)
    merkle_root = merkle_tree.get_root()
    
    print(f"\n✅ Merkle tree created:")
    print(f"   Root hash: {merkle_root}")
    print(f"   Tree height: {len(merkle_tree.tree)}")
    
    # Generate inclusion proof for event 2
    proof = merkle_tree.get_proof(2)
    
    print(f"\n✅ Inclusion proof for Event 3:")
    print(f"   Leaf hash: {proof.leaf_hash[:16]}...")
    print(f"   Root hash: {proof.root_hash[:16]}...")
    print(f"   Proof path length: {len(proof.proof)}")
    
    # Verify the proof
    is_valid = MerkleTree.verify_proof(proof)
    print(f"\n✅ Proof verification: {is_valid}")
    
    print(f"\n✅ This Merkle root would be anchored to Base L2 blockchain")
    print(f"   Transaction: 0xabc123... (example)")
    print(f"   BaseScan URL: https://sepolia.basescan.org/tx/0xabc123...")


def demo_blockchain_anchoring():
    """Demo blockchain anchoring concept"""
    print("\n" + "=" * 60)
    print("5. BLOCKCHAIN ANCHORING (Conceptual)")
    print("=" * 60)
    
    merkle_root = hash_data(b"batch_of_100_events")
    
    print(f"\n✅ Anchoring Merkle root to Base L2:")
    print(f"   Merkle root: {merkle_root}")
    print(f"   Chain: Base Sepolia (Testnet)")
    print(f"   Gas cost: ~0.0001 ETH (~$0.30)")
    
    print(f"\n✅ Result:")
    print(f"   Transaction hash: 0x{merkle_root[:40]}...")
    print(f"   Block number: 5234567")
    print(f"   Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"   Verify: https://sepolia.basescan.org/tx/0x{merkle_root[:40]}...")
    
    print(f"\n✅ The Pitch:")
    print(f"   'This audit trail is mathematically impossible to alter.'")
    print(f"   'Can your current IT department do that?'")


def main():
    """Run all demos"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        MACHINE TRUST PROTOCOL - DEMO SCRIPT              ║")
    print("║        Basel III for AI Agents                           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # 1. Cryptography
    private_key, public_key = demo_cryptography()
    
    # 2. MTP ID Generation
    mtp_id = demo_mtp_id_generation()
    
    # 3. Request Signing
    demo_request_signing(private_key, mtp_id)
    
    # 4. Merkle Tree
    demo_merkle_tree()
    
    # 5. Blockchain Anchoring
    demo_blockchain_anchoring()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start PostgreSQL + TimescaleDB")
    print("2. Update .env with BASE_L2_PRIVATE_KEY")
    print("3. Run: uvicorn server:app --host 0.0.0.0 --port 8001")
    print("4. Test Gateway: POST /api/gateway/proxy")
    print("\n")


if __name__ == "__main__":
    main()
