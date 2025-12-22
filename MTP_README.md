# Machine Trust Protocol (MTP) - Core Enforcement System

**"Basel III for AI Agents"**

## Overview

The Machine Trust Protocol (MTP) is a **mandatory governance layer** for autonomous AI agents. It is not a passive logger; it is an **active enforcement system**.

### The Three Pillars

1. **The Kill Switch (Gateway)** - Block rogue agents in <100ms
2. **The Black Box (Audit)** - Immutable audit trail with blockchain proof
3. **The Registry (Identity)** - Zero-liability key management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI AGENT FLEET                        │
│  (Claude, GPT-4, Custom Models, Trading Bots, etc.)        │
└───────────────────┬─────────────────────────────────────────┘
                    │ Every request flows through MTP
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    MTP GATEWAY (Kill Switch)                 │
│  1. Verify Ed25519 signature                                │
│  2. Check agent status (ACTIVE/SUSPENDED)                   │
│  3. Enforce mandate (transaction limits, actions)           │
│  4. BLOCK or ALLOW (403 Forbidden vs 200 OK)               │
└───────────────────┬─────────────────────────────────────────┘
                    │ If allowed, log to Black Box
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 AUDIT SERVICE (Black Box)                    │
│  - Log every action to TimescaleDB                          │
│  - Batch events into Merkle trees                           │
│  - Anchor Merkle root to Base L2 blockchain                 │
│  - Provide forensic query: "Show me everything at 08:00"    │
└───────────────────┬─────────────────────────────────────────┘
                    │ Merkle root anchored every 5 min
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   BASE L2 BLOCKCHAIN                         │
│  - Immutable proof on BaseScan                              │
│  - "This audit trail is mathematically impossible to alter" │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** (async API framework)
- **PostgreSQL 15** (relational data: agents, orgs, supervisors)
- **TimescaleDB** (time-series audit events)
- **Web3.py** (Base L2 blockchain integration)
- **Ed25519** (cryptographic signatures)

### Database Schema
- `organizations` - KYB-verified entities deploying agents
- `supervisors` - Human accountability chain
- `agents` - AI agent registry with public keys
- `audit_events` - TimescaleDB hypertable for forensic queries
- `mandates` - Transaction limits and authorization rules
- `merkle_batches` - Blockchain anchoring records
- `disputes` - Insurance and liability tracking

### Blockchain
- **Base L2 (Sepolia Testnet)** - Low-cost, high-throughput L2
- **Merkle Root Anchoring** - Batch 100 events → 1 blockchain tx
- **BaseScan Verification** - Public proof for regulators/auditors

---

## Project Structure

```
/app/backend/
├── mtp_core/
│   ├── models/
│   │   ├── identity.py       # Agent, Organization, Supervisor
│   │   ├── audit.py          # AuditEvent, MerkleBatch
│   │   ├── mandate.py        # Mandate, PolicyViolation
│   │   └── insurance.py      # RiskProfile, Dispute
│   ├── services/
│   │   ├── verification.py   # Ed25519 + Mandate enforcement
│   │   ├── audit.py          # Event logging + Merkle batching
│   │   └── blockchain.py     # Base L2 anchoring
│   ├── api/
│   │   ├── gateway.py        # The Kill Switch
│   │   ├── identity.py       # Agent registration
│   │   └── audit.py          # Forensic queries
│   ├── core/
│   │   ├── crypto.py         # Ed25519 utilities
│   │   ├── merkle.py         # Merkle tree implementation
│   │   └── config.py         # Configuration
│   └── db/
│       └── postgres.py       # Database connection + schema
└── server.py                 # FastAPI entry point
```

---

## Setup Instructions

### 1. Prerequisites

- **Python 3.11+**
- **PostgreSQL 15** with TimescaleDB extension
- **Base L2 Wallet** (for blockchain anchoring)

### 2. Database Setup

#### Install PostgreSQL + TimescaleDB

**Ubuntu/Debian:**
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

# Add TimescaleDB repository
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt update

# Install TimescaleDB
sudo apt install timescaledb-2-postgresql-15

# Tune PostgreSQL for TimescaleDB
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew install timescaledb

# Add to postgresql.conf
echo "shared_preload_libraries = 'timescaledb'" >> /usr/local/var/postgresql@15/postgresql.conf

brew services restart postgresql@15
```

#### Create Database

```bash
sudo -u postgres psql

CREATE DATABASE mtp_db;
CREATE USER mtp_user WITH PASSWORD 'mtp_password';
GRANT ALL PRIVILEGES ON DATABASE mtp_db TO mtp_user;
\c mtp_db
CREATE EXTENSION timescaledb;
\q
```

### 3. Environment Configuration

Update `/app/backend/.env`:

```env
# PostgreSQL Configuration
POSTGRES_URL="postgresql+asyncpg://mtp_user:mtp_password@localhost:5432/mtp_db"

# Base L2 Blockchain (Sepolia Testnet)
BASE_L2_RPC_URL="https://sepolia.base.org"
BASE_L2_PRIVATE_KEY="your_private_key_here"
MTP_REGISTRY_CONTRACT=""

# System
ENVIRONMENT="development"
LOG_LEVEL="INFO"
CORS_ORIGINS="*"
```

### 4. Get Base L2 Testnet ETH

1. Create a wallet (MetaMask or similar)
2. Switch to Base Sepolia network
3. Get testnet ETH from faucet: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
4. Add private key to `.env`

### 5. Install Dependencies

```bash
cd /app/backend
pip install -r requirements.txt
```

### 6. Start the Server

```bash
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

The server will:
1. Initialize PostgreSQL + TimescaleDB schema
2. Connect to Base L2 RPC
3. Start the MTP Gateway on port 8001

---

## API Endpoints

### Identity Management

#### Register an Agent
```bash
POST /api/identity/agents/register
Content-Type: application/json

{
  "agent_type": "customer_service_llm",
  "base_model": "Claude 3.5 Sonnet",
  "org_id": "uuid",
  "supervisor_id": "uuid",
  "jurisdiction": "ZA-GP",
  "public_key_hex": "a4b2c1d3e5f6...",
  "authorized_actions": ["query_balance", "transfer_funds"],
  "transaction_limit_daily": 10000.0
}
```

Returns: `mtp_id` (e.g., `MTP-a3f5b2-7k9m2p`)

#### Get Agent Details
```bash
GET /api/identity/agents/{mtp_id}
```

#### Update Agent Status
```bash
PUT /api/identity/agents/{mtp_id}/status
Content-Type: application/json

{
  "new_status": "ACTIVE"
}
```

### Gateway (Kill Switch)

#### Proxy Request (The Kill Switch)
```bash
POST /api/gateway/proxy
X-MTP-ID: MTP-a3f5b2-7k9m2p
X-MTP-Signature: base64_signature
X-MTP-Timestamp: 2025-01-15T10:30:00Z
X-MTP-Action: transfer_funds
X-MTP-Transaction-Value: 500.0

{
  "from_account": "12345",
  "to_account": "67890",
  "amount": 500
}
```

**Response:**
- `200 OK` - Request allowed (logged to audit trail)
- `403 Forbidden` - Request blocked (invalid signature, suspended agent, mandate violation)

### Audit Queries

#### Log an Event
```bash
POST /api/audit/events
Content-Type: application/json

{
  "mtp_id": "MTP-a3f5b2-7k9m2p",
  "event_type": "TRANSACTION",
  "event_category": "FINANCIAL",
  "action_description": "Transfer R500",
  "input_hash": "8a3f5b2c...",
  "output_hash": "2d1c5b3f...",
  "value_transferred": 500.0
}
```

#### Query Events (Forensic Query)
```bash
GET /api/audit/events/query?mtp_id=MTP-a3f5b2-7k9m2p&start_time=2025-01-15T08:00:00Z&end_time=2025-01-15T08:01:00Z&limit=100
```

---

## The Signature Protocol (Ed25519)

### Agent-Side (How to Sign Requests)

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import json
import base64
from datetime import datetime, timezone

# Agent's private key (agent holds this, never MTP)
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Construct message to sign
mtp_id = "MTP-a3f5b2-7k9m2p"
timestamp = datetime.now(timezone.utc).isoformat()
request_body = {"amount": 500}

message = f"{mtp_id}|{timestamp}|{json.dumps(request_body, sort_keys=True)}"
signature = private_key.sign(message.encode())
signature_b64 = base64.b64encode(signature).decode()

# Send request to MTP Gateway
headers = {
    "X-MTP-ID": mtp_id,
    "X-MTP-Signature": signature_b64,
    "X-MTP-Timestamp": timestamp,
    "X-MTP-Action": "transfer_funds",
    "X-MTP-Transaction-Value": "500.0"
}
```

### MTP Verification (Automatic)

MTP Gateway automatically:
1. Retrieves agent's public key from database
2. Verifies signature matches message
3. Checks timestamp is fresh (<5 minutes old)
4. Checks agent status is ACTIVE
5. Enforces mandate (transaction limits, allowed actions)

**If any check fails → 403 Forbidden (Kill Switch activated)**

---

## Blockchain Anchoring

### How It Works

1. **Event Logging**: Every agent action is logged to TimescaleDB
2. **Merkle Batching**: Every 5 minutes (or 100 events), create Merkle tree
3. **Blockchain Anchoring**: Submit Merkle root to Base L2
4. **Immutable Proof**: Transaction hash on BaseScan proves events occurred

### Verify on BaseScan

```
https://sepolia.basescan.org/tx/{transaction_hash}
```

This is what you show regulators, auditors, and Whales:
**"This audit trail is mathematically impossible to alter. See for yourself."**

---

## The Pitch

### To Banks & Insurers

> "Mr. Banker, I can **stop a rogue agent in 100 milliseconds**, and I have the **immutable logs to prove what it did**. Can your current IT department do that?"

### To Regulators

> "Every AI action is logged to a **time-series database** with **blockchain-anchored proof**. You can query: 'Show me everything Agent X did on January 15 at 08:00.' We can prove it in court."

### To Insurance Companies

> "We calculate **actuarial risk profiles** for AI agents. You get data like: success rate, error rate, disputes, trust score. You price policies accurately. We get a cut."

---

## Key Security Features

### 1. Zero-Liability Key Management
- Agents generate and hold their own Ed25519 keys
- MTP only verifies signatures, never holds private keys
- If agent is hacked, it's **their** liability, not ours

### 2. The Kill Switch
- Agent status can be changed to SUSPENDED instantly
- All future requests are blocked by the Gateway
- No need to shut down the agent, just revoke registry access

### 3. Immutable Audit Trail
- Events logged to TimescaleDB (optimized for time-series queries)
- Merkle roots anchored to Base L2 blockchain
- Can prove any event occurred, with cryptographic proof

### 4. Mandate Enforcement
- Transaction limits (daily, per-transaction)
- Allowed/forbidden actions
- Trust score thresholds
- Human approval requirements

---

## Next Steps (Production Readiness)

### Phase 1: Core Enforcement ✅ (COMPLETE)
- ✅ Identity Service (Ed25519 verification)
- ✅ Audit Service (TimescaleDB + Merkle batching)
- ✅ Gateway Service (Kill Switch)
- ✅ Blockchain Service (Base L2 anchoring)

### Phase 2: Trust & Compliance (TODO)
- [ ] Trust Score Algorithm (behavioral analysis)
- [ ] Compliance Certification (MTP-CERT)
- [ ] Insurance Integration (RiskProfile API)
- [ ] Dispute Resolution System

### Phase 3: Scale & Monitoring (TODO)
- [ ] Real-time alerting (Kafka/Flink)
- [ ] Agent-to-agent trust verification
- [ ] Multi-region deployment
- [ ] Consumer-facing trust widget

---

## Demo Script

### 1. Create an Organization
```bash
curl -X POST http://localhost:8001/api/identity/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "id": "org-001",
    "legal_name": "First National Bank",
    "registration_number": "1929/001225/06",
    "jurisdiction": "ZA-GP",
    "kyb_status": "VERIFIED"
  }'
```

### 2. Create a Supervisor
```bash
curl -X POST http://localhost:8001/api/identity/supervisors \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sup-001",
    "org_id": "org-001",
    "full_name": "Dr. Sarah Mthembu",
    "email": "s.mthembu@fnb.co.za",
    "role_title": "Head of AI Risk"
  }'
```

### 3. Register an Agent
```bash
curl -X POST http://localhost:8001/api/identity/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "customer_service",
    "base_model": "Claude 3.5 Sonnet",
    "org_id": "org-001",
    "supervisor_id": "sup-001",
    "jurisdiction": "ZA-GP",
    "public_key_hex": "abc123...",
    "authorized_actions": ["transfer_funds"],
    "transaction_limit_daily": 10000.0
  }'
```

Returns: `{"mtp_id": "MTP-a3f5b2-7k9m2p"}`

### 4. Activate the Agent
```bash
curl -X PUT http://localhost:8001/api/identity/agents/MTP-a3f5b2-7k9m2p/status \
  -H "Content-Type: application/json" \
  -d '{"new_status": "ACTIVE"}'
```

### 5. Test the Kill Switch (Unsigned Request)
```bash
curl -X POST http://localhost:8001/api/gateway/proxy \
  -H "X-MTP-ID: MTP-a3f5b2-7k9m2p" \
  -H "X-MTP-Signature: invalid" \
  -H "X-MTP-Timestamp: 2025-01-15T10:00:00Z"
```

**Expected: 403 Forbidden** ❌

### 6. Query Audit Trail
```bash
curl "http://localhost:8001/api/audit/events/query?mtp_id=MTP-a3f5b2-7k9m2p&limit=10"
```

Shows all blocked attempts and successful actions.

---

## Contact

For integration support, contact the MTP team or see the full documentation at `/app/backend/mtp_core/`.

**Remember: If you mock the blockchain, you are just a database admin. If you use the blockchain, you are a Protocol.**
