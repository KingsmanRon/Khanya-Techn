# MTP Deployment & Testing Guide

## Quick Start (5 Minutes)

### 1. Install PostgreSQL + TimescaleDB

```bash
chmod +x /app/scripts/setup_database.sh
sudo /app/scripts/setup_database.sh
```

This will:
- Install PostgreSQL 15 + TimescaleDB extension
- Create `mtp_db` database
- Create `mtp_user` with password `mtp_password`
- Configure TimescaleDB

### 2. Get Base L2 Testnet ETH

1. Go to: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
2. Enter your wallet address (MetaMask)
3. Claim testnet ETH (free)

### 3. Configure Environment

Edit `/app/backend/.env`:

```env
POSTGRES_URL="postgresql+asyncpg://mtp_user:mtp_password@localhost:5432/mtp_db"
BASE_L2_RPC_URL="https://sepolia.base.org"
BASE_L2_PRIVATE_KEY="your_metamask_private_key_here"
```

**To get your MetaMask private key:**
- Open MetaMask → Account Details → Show Private Key
- Copy and paste into `.env`

### 4. Start the Server

```bash
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Expected output:
```
============================================================
MACHINE TRUST PROTOCOL - INITIALIZING
============================================================
✅ PostgreSQL + TimescaleDB initialized
Environment: development
Base L2 RPC: https://sepolia.base.org
============================================================
✅ MTP CORE SYSTEM OPERATIONAL
============================================================
```

### 5. Run Demo Script

```bash
cd /app/backend
python demo_mtp.py
```

This demonstrates:
- Ed25519 key generation
- MTP ID creation
- Request signing
- Merkle tree batching
- Blockchain anchoring concept

---

## Testing the Kill Switch

### Test 1: Create Organization & Supervisor

```bash
# Create organization
curl -X POST http://localhost:8001/api/identity/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "legal_name": "First National Bank of South Africa",
    "registration_number": "1929/001225/06",
    "jurisdiction": "ZA-GP",
    "kyb_status": "VERIFIED"
  }'

# Create supervisor
curl -X POST http://localhost:8001/api/identity/supervisors \
  -H "Content-Type: application/json" \
  -d '{
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "Dr. Sarah Mthembu",
    "email": "s.mthembu@fnb.co.za",
    "role_title": "Head of AI Risk & Compliance"
  }'
```

### Test 2: Register an Agent with Ed25519 Keys

```python
# Generate Ed25519 keypair
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

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

print(f"Private Key (hex): {private_bytes.hex()}")
print(f"Public Key (hex): {public_bytes.hex()}")
```

Register agent:

```bash
curl -X POST http://localhost:8001/api/identity/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "customer_service_llm",
    "base_model": "Claude 3.5 Sonnet",
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "supervisor_id": "660e8400-e29b-41d4-a716-446655440000",
    "jurisdiction": "ZA-GP",
    "public_key_hex": "YOUR_PUBLIC_KEY_HEX_HERE",
    "authorized_actions": ["query_balance", "transfer_funds"],
    "prohibited_actions": ["delete_account"],
    "transaction_limit_daily": 10000.0
  }'
```

Response will include the `mtp_id` (e.g., `MTP-a3f5b2-7k9m2p`).

### Test 3: Activate the Agent

```bash
curl -X PUT http://localhost:8001/api/identity/agents/MTP-a3f5b2-7k9m2p/status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "ACTIVE"}'
```

### Test 4: Test the Kill Switch (Invalid Signature)

```bash
curl -X POST http://localhost:8001/api/gateway/proxy \
  -H "X-MTP-ID: MTP-a3f5b2-7k9m2p" \
  -H "X-MTP-Signature: invalid_signature" \
  -H "X-MTP-Timestamp: 2025-01-15T10:00:00Z" \
  -H "X-MTP-Action: transfer_funds" \
  -H "X-MTP-Transaction-Value: 500.0" \
  -H "Content-Type: application/json" \
  -d '{"from": "12345", "to": "67890", "amount": 500}'
```

**Expected Response: 403 Forbidden** ❌

```json
{
  "detail": "Request blocked: Invalid signature"
}
```

### Test 5: Test with Valid Signature

```python
# Sign the request properly
import json
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Load your private key
private_key_hex = "YOUR_PRIVATE_KEY_HEX_FROM_STEP_2"
private_bytes = bytes.fromhex(private_key_hex)
private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)

# Prepare request
mtp_id = "MTP-a3f5b2-7k9m2p"
timestamp = datetime.now(timezone.utc).isoformat()
request_body = {"from": "12345", "to": "67890", "amount": 500}

# Create canonical message
body_json = json.dumps(request_body, sort_keys=True)
message = f"{mtp_id}|{timestamp}|{body_json}"

# Sign
signature = private_key.sign(message.encode())
signature_b64 = base64.b64encode(signature).decode()

print(f"X-MTP-Signature: {signature_b64}")
print(f"X-MTP-Timestamp: {timestamp}")
```

Then use those values in curl:

```bash
curl -X POST http://localhost:8001/api/gateway/proxy \
  -H "X-MTP-ID: MTP-a3f5b2-7k9m2p" \
  -H "X-MTP-Signature: YOUR_SIGNATURE_FROM_PYTHON" \
  -H "X-MTP-Timestamp: YOUR_TIMESTAMP_FROM_PYTHON" \
  -H "X-MTP-Action: transfer_funds" \
  -H "X-MTP-Transaction-Value: 500.0" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "from": "12345", "to": "67890"}'
```

**Expected Response: 200 OK** ✅

```json
{
  "status": "allowed",
  "mtp_id": "MTP-a3f5b2-7k9m2p",
  "action": "transfer_funds",
  "message": "Request verified and allowed",
  "agent_trust_score": 500
}
```

### Test 6: Test Mandate Violation (Exceed Transaction Limit)

```bash
curl -X POST http://localhost:8001/api/gateway/proxy \
  -H "X-MTP-ID: MTP-a3f5b2-7k9m2p" \
  -H "X-MTP-Signature: VALID_SIGNATURE" \
  -H "X-MTP-Timestamp: VALID_TIMESTAMP" \
  -H "X-MTP-Action: transfer_funds" \
  -H "X-MTP-Transaction-Value: 50000.0" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50000, "from": "12345", "to": "67890"}'
```

**Expected Response: 403 Forbidden** ❌

```json
{
  "detail": "Mandate violation: Transaction value 50000 exceeds daily limit 10000"
}
```

### Test 7: Query Audit Trail

```bash
# Get all audit events for the agent
curl "http://localhost:8001/api/audit/events/query?mtp_id=MTP-a3f5b2-7k9m2p&limit=100"
```

This will show:
- All blocked attempts (invalid signatures, mandate violations)
- All successful requests
- Timestamps, action descriptions, values

### Test 8: Suspend Agent (The Kill Switch)

```bash
curl -X PUT http://localhost:8001/api/identity/agents/MTP-a3f5b2-7k9m2p/status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "SUSPENDED"}'
```

Now try any request (even with valid signature):

```bash
curl -X POST http://localhost:8001/api/gateway/proxy \
  -H "X-MTP-ID: MTP-a3f5b2-7k9m2p" \
  -H "X-MTP-Signature: VALID_SIGNATURE" \
  -H "X-MTP-Timestamp: VALID_TIMESTAMP"
```

**Expected Response: 403 Forbidden** ❌

```json
{
  "detail": "Request blocked: Agent MTP-a3f5b2-7k9m2p is SUSPENDED, not ACTIVE"
}
```

**The agent is neutralized instantly. No need to shut it down, just revoke registry access.**

---

## Blockchain Anchoring Test

### Manual Merkle Batching

```python
import asyncio
from mtp_core.services.audit import AuditService
from mtp_core.services.blockchain import BlockchainService

async def test_blockchain_anchoring():
    audit_service = AuditService()
    blockchain_service = BlockchainService()
    
    # Create Merkle batch (simulate 5 events)
    event_ids = [
        "event-001", "event-002", "event-003", "event-004", "event-005"
    ]
    
    merkle_tree = await audit_service.create_merkle_batch(event_ids)
    merkle_root = merkle_tree.get_root()
    
    print(f"Merkle Root: {merkle_root}")
    
    # Anchor to Base L2
    result = await blockchain_service.anchor_merkle_root(
        merkle_root=merkle_root,
        event_count=len(event_ids)
    )
    
    if result:
        print(f"✅ Anchored to Base L2:")
        print(f"   TX Hash: {result['tx_hash']}")
        print(f"   Block: {result['block_number']}")
        print(f"   BaseScan: {blockchain_service.get_basescan_url(result['tx_hash'])}")
    else:
        print("❌ Blockchain anchoring failed (check BASE_L2_PRIVATE_KEY)")

asyncio.run(test_blockchain_anchoring())
```

### Expected Output

```
Merkle Root: 7cfa78160e5dfd93e611b01fe14fbfd99688cf5478c537e510840b3e80f21b22
✅ Anchored to Base L2:
   TX Hash: 0x9a5b3c2d1e0f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b
   Block: 5234567
   BaseScan: https://sepolia.basescan.org/tx/0x9a5b3c2d...
```

**You can now show this BaseScan link to regulators, auditors, and Whales:**
> "This audit trail is mathematically impossible to alter. See for yourself."

---

## Demo to Whales (5-Minute Pitch)

### Setup (Before Meeting)

1. Register 3 agents (Customer Service, Fraud Detection, Trading Bot)
2. Generate some audit events (transactions, queries, errors)
3. Batch and anchor to blockchain
4. Prepare BaseScan links

### The Pitch

#### Slide 1: The Problem

> "Banks deploy AI agents for customer service, trading, fraud detection. But when something goes wrong, they can't prove what the agent did. No audit trail. No accountability. **No trust.**"

#### Slide 2: The Solution (The Kill Switch)

**Live Demo:**

1. Show agent registration
2. Show Gateway endpoint
3. Send valid request → 200 OK ✅
4. Send invalid signature → 403 Forbidden ❌
5. Suspend agent → All requests blocked ❌

> "I can stop a rogue agent in 100 milliseconds. Can your current IT department do that?"

#### Slide 3: The Black Box

**Live Demo:**

1. Query audit trail: "Show me everything Agent X did at 08:00"
2. Show TimescaleDB results
3. Show Merkle root
4. **Open BaseScan link**

> "Every action is logged to a time-series database. Every 5 minutes, we batch 100 events into a Merkle tree and anchor the root to the Base L2 blockchain. This audit trail is **mathematically impossible to alter**."

#### Slide 4: The Business Model

> "We sell this data to insurance companies. They want to underwrite AI agent liability policies. We provide:
> - Risk profiles (success rate, error rate, trust score)
> - Immutable evidence for dispute resolution
> - Actuarial data for pricing
>
> We charge banks $10K/month per 100 agents. We give insurers 20% of risk data revenue. You invest $500K, we get to $5M ARR in 18 months."

#### Slide 5: Regulatory Traction

> "We're in talks with SARB, FSCA, and the Information Regulator. They want a solution like this. If we can prove this works in South Africa, we can sell it to the ECB, Fed, and PBOC."

### The Close

> "Mr. Banker, AI agents are the future. But without governance, they're a liability. We're building the protocol that makes AI agents trustworthy. We're not selling software. **We're selling Basel III for AI.**"

---

## Troubleshooting

### Database Connection Failed

```
ERROR: Failed to connect to PostgreSQL
```

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# If not, start it
sudo systemctl start postgresql

# Verify connection string in .env
POSTGRES_URL="postgresql+asyncpg://mtp_user:mtp_password@localhost:5432/mtp_db"
```

### TimescaleDB Extension Not Found

```
ERROR: extension "timescaledb" does not exist
```

**Solution:**
```bash
# Install TimescaleDB
sudo apt install timescaledb-2-postgresql-15

# Enable extension manually
sudo -u postgres psql -d mtp_db -c "CREATE EXTENSION timescaledb;"
```

### Blockchain Anchoring Failed

```
ERROR: Failed to anchor Merkle root
```

**Solution:**
1. Check if `BASE_L2_PRIVATE_KEY` is set in `.env`
2. Verify you have testnet ETH: https://sepolia.basescan.org/address/YOUR_ADDRESS
3. Check RPC connection: `curl https://sepolia.base.org`

### Invalid Signature Errors

```
ERROR: Invalid signature
```

**Solution:**
1. Verify timestamp is fresh (<5 minutes old)
2. Ensure canonical message format: `{mtp_id}|{timestamp}|{body_json}`
3. Check that `body_json` is sorted: `json.dumps(body, sort_keys=True)`

---

## Production Deployment Checklist

- [ ] **PostgreSQL**: Deploy to managed service (AWS RDS, Google Cloud SQL)
- [ ] **TimescaleDB**: Enable on managed PostgreSQL
- [ ] **Base L2**: Switch to mainnet (update `BASE_L2_RPC_URL` and `BASE_L2_CHAIN_ID`)
- [ ] **Private Key**: Use KMS (AWS KMS, HashiCorp Vault) instead of `.env`
- [ ] **Load Balancer**: Deploy behind Nginx/ALB
- [ ] **Monitoring**: Set up Prometheus + Grafana
- [ ] **Alerting**: Integrate PagerDuty/Slack for suspicious activity
- [ ] **Backup**: Configure automated database backups
- [ ] **DR**: Multi-region deployment (af-south-1, eu-west-1)
- [ ] **Rate Limiting**: Add per-organization rate limits
- [ ] **API Keys**: Implement API key authentication for organizations
- [ ] **Audit Retention**: Configure data retention policies (7 years for compliance)

---

## Next Steps

### Phase 2: Trust & Compliance
- Implement Trust Score algorithm (behavioral analysis)
- Build Compliance Certification system (MTP-CERT)
- Integrate with insurance providers (RiskProfile API)
- Create dispute resolution workflow

### Phase 3: Scale & Monitoring
- Real-time alerting (Kafka + Flink)
- Agent-to-agent trust verification (MTP-MESH)
- Consumer-facing trust widget (MTP-VERIFY)
- Multi-region deployment

---

## Support

For questions or issues:
- Check logs: `tail -f /var/log/mtp/*.log`
- Run demo: `python demo_mtp.py`
- Review architecture: `/app/MTP_README.md`
- Database schema: `/app/backend/mtp_core/db/postgres.py`
