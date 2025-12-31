# Machine Trust Protocol (MTP)

> **"Basel III for AI Agents"** - Governance, Compliance, and Trust Infrastructure for AI Agents in Financial Services

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![React](https://img.shields.io/badge/react-19.0-61dafb.svg)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.110+-009688.svg)]()

---

## Overview

MTP is a comprehensive governance layer for AI agents operating in financial services. It provides:

- **The Kill Switch**: Stop rogue agents in <100ms
- **The Black Box**: Immutable blockchain-anchored audit trail
- **The Registry**: Zero-liability cryptographic identity management

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ & Yarn
- PostgreSQL 15+ with TimescaleDB
- Docker (recommended)

### 1. Start Database (Docker)

```bash
docker run -d --name mtp-timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=mtp_password \
  -e POSTGRES_USER=mtp_user \
  -e POSTGRES_DB=mtp_db \
  -v mtp_pgdata:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg16
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend

```bash
cd frontend
yarn install
yarn start
```

### 4. Access Dashboard

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@mtp.io` | `admin123` |
| Auditor | `auditor@fnb.co.za` | `audit123` |
| Operator | `operator@standard.co.za` | `oper123` |
| Viewer | `viewer@demo.com` | `view123` |

---

## The Five Pillars

### MTP-ID (Identity)
Zero-liability cryptographic identity for AI agents. Agents generate and hold their own Ed25519 keys; MTP only verifies signatures.

### MTP-AUDIT (Audit Trail)
Forensic-grade logging with TimescaleDB. Every action is logged with input/output hashes and can be queried by time range.

### MTP-TRUST (Trust Scores)
4-component weighted trust calculation: Reliability (30%), Compliance (30%), Transparency (20%), History (20%).

### MTP-CHAIN (Blockchain)
Merkle-batched anchoring to Base L2. 100 events per batch, anchored to blockchain.

### MTP-CERT (Certifications)
Compliance certifications: ZA-FIN, ZA-ECOM, ZA-HEALTH, EU-AI, POPIA, ISO-27001.

---

## Project Structure

```
Khanya-Techn/
├── backend/
│   ├── mtp_core/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── gateway.py    # Kill Switch endpoint
│   │   │   ├── identity.py   # Agent registration
│   │   │   ├── audit.py      # Audit event logging
│   │   │   ├── trust.py      # Trust score queries
│   │   │   ├── certifications.py
│   │   │   ├── insurance.py
│   │   │   ├── disputes.py
│   │   │   ├── websocket.py  # WebSocket endpoints
│   │   │   └── monitor.py    # Alerting API
│   │   ├── services/         # Business logic
│   │   │   ├── websocket.py  # WebSocket manager
│   │   │   └── monitor.py    # MTP-MONITOR service
│   │   ├── models/           # Pydantic data models
│   │   ├── core/             # Crypto, Merkle, Config
│   │   └── db/               # PostgreSQL + TimescaleDB
│   ├── server.py             # FastAPI application
│   ├── Dockerfile            # Backend container
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components (shadcn/ui)
│   │   ├── contexts/         # Auth, Theme contexts
│   │   ├── hooks/            # Custom hooks (useWebSocket)
│   │   ├── pages/            # Route pages
│   │   ├── services/         # API client
│   │   └── App.js            # Router setup
│   ├── Dockerfile            # Frontend container
│   └── package.json
├── tests/                    # Python tests
│   ├── test_api.py           # API integration tests
│   ├── test_services.py      # Service unit tests
│   └── conftest.py           # Pytest fixtures
├── monitoring/               # Prometheus & Grafana config
├── .github/workflows/        # CI/CD pipelines
├── docker-compose.yml        # Full stack containerization
└── docs/                     # Documentation
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Tailwind CSS, shadcn/ui, Recharts |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | PostgreSQL 16 + TimescaleDB |
| **Blockchain** | Base L2 (Sepolia testnet) |
| **Crypto** | Ed25519 signatures, SHA-256, Merkle trees |

---

## Documentation

### Core Documentation
- [Architecture Diagram](./ARCHITECTURE.md) - System architecture with ASCII diagrams
- [Architecture Details](./mtp-architecture.md) - Technical architecture deep-dive
- [Integration Guide](./mtp-integration-architecture.md) - How to integrate with MTP

### Deployment & Operations
- [Production Checklist](./PRODUCTION_CHECKLIST.md) - **Required credentials & decisions**
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Deployment instructions
- [Optional Enhancements](./OPTIONAL_ENHANCEMENTS.md) - Future features roadmap

### Reference
- [Project Summary](./PROJECT_SUMMARY.md) - High-level project overview
- [Production Additions](./mtp-production-additions.md) - Production considerations

---

## License

Proprietary - All Rights Reserved

---

**Machine Trust Protocol** - *"When you can stop a rogue agent in 100 milliseconds and prove what it did on the blockchain, that's not a product. That's a Protocol."*
