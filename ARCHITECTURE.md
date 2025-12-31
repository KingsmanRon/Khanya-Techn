# MTP System Architecture

> Comprehensive architecture documentation for the Machine Trust Protocol

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MACHINE TRUST PROTOCOL (MTP)                             │
│                         "Basel III for AI Agents"                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         CLIENT LAYER                                     │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │   │
│  │   │   Browser    │    │  AI Agents   │    │  Third-Party │              │   │
│  │   │  (React UI)  │    │  (API Calls) │    │    Systems   │              │   │
│  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │   │
│  │          │                   │                   │                       │   │
│  └──────────┼───────────────────┼───────────────────┼───────────────────────┘   │
│             │                   │                   │                           │
│             │    HTTPS/REST     │    HTTPS/REST     │    HTTPS/REST            │
│             ▼                   ▼                   ▼                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         API GATEWAY                                      │   │
│  │                                                                          │   │
│  │   ┌────────────────────────────────────────────────────────────────┐    │   │
│  │   │                    AUTHENTICATION                               │    │   │
│  │   │   • JWT Token Validation                                        │    │   │
│  │   │   • API Key Verification (X-MTP-API-Key)                        │    │   │
│  │   │   • Ed25519 Signature Check (X-MTP-Signature)                   │    │   │
│  │   └────────────────────────────────────────────────────────────────┘    │   │
│  │                               │                                          │   │
│  │   ┌────────────────────────────────────────────────────────────────┐    │   │
│  │   │                    RATE LIMITING                                │    │   │
│  │   │   • Per-organization limits                                     │    │   │
│  │   │   • Per-agent limits                                            │    │   │
│  │   └────────────────────────────────────────────────────────────────┘    │   │
│  │                               │                                          │   │
│  └───────────────────────────────┼──────────────────────────────────────────┘   │
│                                  │                                              │
│                                  ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      FASTAPI APPLICATION                                 │   │
│  │                        (server.py)                                       │   │
│  │                                                                          │   │
│  │   ┌────────────────────────────────────────────────────────────────┐    │   │
│  │   │                     API ROUTES                                  │    │   │
│  │   │                                                                 │    │   │
│  │   │  /api/v1/gateway     ──────► Kill Switch (Request Verification)│    │   │
│  │   │  /api/v1/identity    ──────► Agent Registration (MTP-ID)       │    │   │
│  │   │  /api/v1/agents      ──────► Agent Management                  │    │   │
│  │   │  /api/v1/audit       ──────► Audit Trail (MTP-AUDIT)           │    │   │
│  │   │  /api/v1/trust       ──────► Trust Scores (MTP-TRUST)          │    │   │
│  │   │  /api/v1/certifications ───► Certifications (MTP-CERT)         │    │   │
│  │   │  /api/v1/insurance   ──────► Risk Profiles (MTP-INSURE)        │    │   │
│  │   │  /api/v1/disputes    ──────► Dispute Resolution (MTP-RESOLVE)  │    │   │
│  │   │  /api/v1/blockchain  ──────► Merkle Batches (MTP-CHAIN)        │    │   │
│  │   │  /api/v1/api-keys    ──────► API Key Management                │    │   │
│  │   │  /api/ws/connect     ──────► WebSocket Real-time Updates       │    │   │
│  │   │  /api/v1/monitor     ──────► Alerts & Metrics (MTP-MONITOR)    │    │   │
│  │   │                                                                 │    │   │
│  │   └─────────────────────────────┬──────────────────────────────────┘    │   │
│  │                                 │                                        │   │
│  │   ┌─────────────────────────────▼──────────────────────────────────┐    │   │
│  │   │                   SERVICE LAYER                                 │    │   │
│  │   │                                                                 │    │   │
│  │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │    │   │
│  │   │  │Verification │ │   Audit     │ │ Blockchain  │               │    │   │
│  │   │  │  Service    │ │  Service    │ │  Service    │               │    │   │
│  │   │  └─────────────┘ └─────────────┘ └─────────────┘               │    │   │
│  │   │                                                                 │    │   │
│  │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │    │   │
│  │   │  │   Trust     │ │Certification│ │    Risk     │               │    │   │
│  │   │  │  Service    │ │  Service    │ │  Analyzer   │               │    │   │
│  │   │  └─────────────┘ └─────────────┘ └─────────────┘               │    │   │
│  │   │                                                                 │    │   │
│  │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │    │   │
│  │   │  │   Batch     │ │  Dispute    │ │  WebSocket  │               │    │   │
│  │   │  │ Processor   │ │  Service    │ │  Manager    │               │    │   │
│  │   │  └─────────────┘ └─────────────┘ └─────────────┘               │    │   │
│  │   │                                                                 │    │   │
│  │   │  ┌─────────────┐                                               │    │   │
│  │   │  │MTP-MONITOR  │ (Alerting & Metrics Service)                  │    │   │
│  │   │  └─────────────┘                                               │    │   │
│  │   │                                                                 │    │   │
│  │   └─────────────────────────────┬──────────────────────────────────┘    │   │
│  │                                 │                                        │   │
│  │   ┌─────────────────────────────▼──────────────────────────────────┐    │   │
│  │   │                    CORE LAYER                                   │    │   │
│  │   │                                                                 │    │   │
│  │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │    │   │
│  │   │  │   Crypto    │ │   Merkle    │ │   Config    │               │    │   │
│  │   │  │  (Ed25519)  │ │   Trees     │ │ Management  │               │    │   │
│  │   │  └─────────────┘ └─────────────┘ └─────────────┘               │    │   │
│  │   │                                                                 │    │   │
│  │   └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│          ┌─────────────────────────┼─────────────────────────┐                 │
│          │                         │                         │                  │
│          ▼                         ▼                         ▼                  │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐        │
│  │    PostgreSQL    │     │   TimescaleDB    │     │   Base L2        │        │
│  │    (Relational)  │     │   (Time-Series)  │     │   Blockchain     │        │
│  │                  │     │                  │     │                  │        │
│  │  • organizations │     │  • audit_events  │     │  • Merkle roots  │        │
│  │  • supervisors   │     │    (hypertable)  │     │  • Transaction   │        │
│  │  • agents        │     │                  │     │    anchors       │        │
│  │  • mandates      │     │                  │     │                  │        │
│  │  • certifications│     │                  │     │                  │        │
│  │  • disputes      │     │                  │     │                  │        │
│  │  • merkle_batches│     │                  │     │                  │        │
│  │  • api_keys      │     │                  │     │                  │        │
│  │  • trust_history │     │                  │     │                  │        │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow: The Kill Switch

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        KILL SWITCH REQUEST FLOW                              │
│                    (Gateway Verification Pipeline)                           │
└──────────────────────────────────────────────────────────────────────────────┘

    AI Agent                                                        Target
    Request                                                         Service
       │                                                               ▲
       ▼                                                               │
┌──────────────┐                                                       │
│   Headers:   │                                                       │
│ X-MTP-ID     │                                                       │
│ X-MTP-Sig    │                                                       │
│ X-MTP-Time   │                                                       │
└──────┬───────┘                                                       │
       │                                                               │
       ▼                                                               │
┌──────────────────────────────────────────────────────────────────────┤
│                     STEP 1: SIGNATURE VERIFICATION                   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  1. Extract signature from X-MTP-Signature header           │   │
│   │  2. Reconstruct signing payload (method + path + body)      │   │
│   │  3. Verify Ed25519 signature against agent's public key     │   │
│   │  4. Check timestamp is within 5-minute window               │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                   ┌──────────┴──────────┐                           │
│                   │                     │                            │
│              VALID ✓                INVALID ✗                        │
│                   │                     │                            │
│                   ▼                     ▼                            │
│              Continue            ┌──────────────┐                    │
│                                  │ 403 FORBIDDEN│                    │
│                                  │ "Invalid     │                    │
│                                  │  signature"  │                    │
│                                  └──────────────┘                    │
├──────────────────────────────────────────────────────────────────────┤
│                     STEP 2: STATUS VERIFICATION                      │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  1. Look up agent by MTP-ID in registry                     │   │
│   │  2. Check agent status is ACTIVE                            │   │
│   │  3. Verify organization is in good standing                 │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                   ┌──────────┴──────────┐                           │
│                   │                     │                            │
│              ACTIVE ✓             NOT ACTIVE ✗                       │
│                   │                     │                            │
│                   ▼                     ▼                            │
│              Continue            ┌──────────────┐                    │
│                                  │ 403 FORBIDDEN│                    │
│                                  │ "Agent       │                    │
│                                  │  suspended"  │                    │
│                                  └──────────────┘                    │
├──────────────────────────────────────────────────────────────────────┤
│                     STEP 3: MANDATE ENFORCEMENT                      │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  1. Check transaction value against max_transaction_value   │   │
│   │  2. Verify action is in allowed_operations list             │   │
│   │  3. Check daily transaction limit not exceeded              │   │
│   │  4. Verify trust score >= minimum threshold (300)           │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                   ┌──────────┴──────────┐                           │
│                   │                     │                            │
│              ALLOWED ✓           NOT ALLOWED ✗                       │
│                   │                     │                            │
│                   ▼                     ▼                            │
│              Continue            ┌──────────────┐                    │
│                                  │ 403 FORBIDDEN│                    │
│                                  │ "Mandate     │                    │
│                                  │  violation"  │                    │
│                                  └──────────────┘                    │
├──────────────────────────────────────────────────────────────────────┤
│                     STEP 4: LOG & FORWARD                            │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  1. Create audit event (BEFORE action)                      │   │
│   │  2. Forward request to target service                       │   │
│   │  3. Capture response                                        │   │
│   │  4. Log outcome (SUCCESS/FAILURE) to audit trail            │   │
│   │  5. Return response to agent                                │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│                      ┌──────────────┐                                │
│                      │ 200 OK       │───────────────────────────────►│
│                      │ (Proxied     │                                │
│                      │  response)   │                                │
│                      └──────────────┘                                │
└──────────────────────────────────────────────────────────────────────┘

    TOTAL TIME: < 100ms (The Kill Switch Promise)
```

---

## Audit Trail & Blockchain Anchoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUDIT TRAIL & BLOCKCHAIN ANCHORING                        │
│                         (MTP-AUDIT + MTP-CHAIN)                             │
└─────────────────────────────────────────────────────────────────────────────┘

  Events Stream                                                    Blockchain
       │                                                               │
       ▼                                                               │
┌──────────────┐                                                       │
│ Audit Event  │                                                       │
│  • mtp_id    │                                                       │
│  • action    │                                                       │
│  • timestamp │                                                       │
│  • input_hash│                                                       │
│  • output_hsh│                                                       │
└──────┬───────┘                                                       │
       │                                                               │
       ▼                                                               │
┌──────────────────────────────────────────────────────────────────────┤
│                      TIMESCALEDB                                     │
│                   (audit_events hypertable)                          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Time-partitioned storage for efficient queries              │  │
│   │  "Show me everything Agent X did at 08:00"                   │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     BATCH PROCESSOR                                   │
│                  (Every 5 minutes or 100 events)                     │
│                                                                      │
│   Pending Events Queue:                                              │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ... ┌─────┐                       │
│   │ E1  │ │ E2  │ │ E3  │ │ E4  │     │E100 │                       │
│   │hash │ │hash │ │hash │ │hash │     │hash │                       │
│   └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘     └──┬──┘                       │
│      │       │       │       │           │                           │
│      └───────┴───────┴───────┴───────────┘                           │
│                      │                                                │
│                      ▼                                                │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                  MERKLE TREE CONSTRUCTION                    │  │
│   │                                                              │  │
│   │                        ROOT                                  │  │
│   │                       /    \                                 │  │
│   │                    H12      H34                              │  │
│   │                   /   \    /   \                             │  │
│   │                 H1    H2  H3   H4   ...                      │  │
│   │                  │     │   │    │                            │  │
│   │                 E1    E2  E3   E4                            │  │
│   │                                                              │  │
│   └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                      │
│                       Merkle Root                                    │
│                 0x7a3f8b2c9d4e5f6a...                               │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      BASE L2 BLOCKCHAIN                              │
│                       (Sepolia Testnet)                              │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Transaction:                                                │  │
│   │    • To: MTP Registry Contract                               │  │
│   │    • Data: anchorBatch(batchId, merkleRoot)                  │  │
│   │    • Gas: ~45,000                                            │  │
│   │    • Cost: ~$0.30                                            │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Block #12345678                                             │  │
│   │    TX: 0x8f2a9c3d4e5f6a7b8c9d...                            │  │
│   │    Merkle Root: 0x7a3f8b2c9d4e5f6a...                       │  │
│   │                                                              │  │
│   │  ✓ Immutable                                                 │  │
│   │  ✓ Publicly verifiable on BaseScan                          │  │
│   │  ✓ Mathematically impossible to alter                        │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

    RESULT: 100 events anchored for ~$0.30 (cost-efficient forensic proof)
```

---

## Trust Score Calculation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRUST SCORE CALCULATION                                │
│                           (MTP-TRUST)                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                         TRUST SCORE = 1000 (max)
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
    │ RELIABILITY │       │ COMPLIANCE  │       │TRANSPARENCY │
    │    (30%)    │       │    (30%)    │       │    (20%)    │
    └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
    │ • Uptime    │       │ • Policy    │       │ • Audit log │
    │ • Response  │       │   adherence │       │   complete- │
    │   consistency│      │ • No        │       │   ness      │
    │ • Error rate│       │   violations│       │ • Explain-  │
    │             │       │ • Mandate   │       │   ability   │
    │             │       │   compliance│       │             │
    └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │
                                 ▼
                         ┌─────────────┐
                         │   HISTORY   │
                         │    (20%)    │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ • Past      │
                         │   performance│
                         │ • Trend     │
                         │   direction │
                         │ • Time in   │
                         │   operation │
                         └──────┬──────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │  EXCELLENT  │      │    GOOD     │      │    FAIR     │
    │   800-1000  │      │   600-799   │      │   400-599   │
    │     (45%)   │      │    (32%)    │      │    (18%)    │
    │   ████████  │      │   ██████    │      │   ████      │
    └─────────────┘      └─────────────┘      └─────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │    POOR     │
                         │    <400     │
                         │     (5%)    │
                         │   ██        │
                         │             │
                         │ ⚠ AT RISK   │
                         └─────────────┘
```

---

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND ARCHITECTURE                                 │
│                         (React 19 + Tailwind)                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              App.js                                          │
│                         (Router Configuration)                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                       CONTEXT PROVIDERS                             │  │
│   │                                                                     │  │
│   │   ┌─────────────────┐         ┌─────────────────┐                  │  │
│   │   │  AuthProvider   │         │  ThemeProvider  │                  │  │
│   │   │  • user state   │         │  • dark/light   │                  │  │
│   │   │  • login/logout │         │  • theme toggle │                  │  │
│   │   │  • permissions  │         │                 │                  │  │
│   │   └─────────────────┘         └─────────────────┘                  │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         ROUTES                                      │  │
│   │                                                                     │  │
│   │   /login ─────────────► Login.jsx (Public)                         │  │
│   │                                                                     │  │
│   │   / ──────────────────┐                                            │  │
│   │   /agents ────────────┤                                            │  │
│   │   /agents/:id ────────┤                                            │  │
│   │   /agents/new ────────┤                                            │  │
│   │   /audit ─────────────┼──────► Layout.jsx (Protected)              │  │
│   │   /trust ─────────────┤            │                               │  │
│   │   /certifications ────┤            ├──► Sidebar.jsx                │  │
│   │   /disputes ──────────┤            ├──► Header.jsx                 │  │
│   │   /blockchain ────────┤            └──► <Outlet/> (Page Content)   │  │
│   │   /settings ──────────┘                                            │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          PAGE COMPONENTS                                     │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│   Dashboard.jsx  │  AgentList.jsx   │   AgentDetail    │   AgentForm.jsx    │
│   • Stats cards  │  • Search/filter │   • Profile      │   • Multi-step     │
│   • Charts       │  • Pagination    │   • Activity     │     wizard         │
│   • Recent agents│  • Actions menu  │   • Trust chart  │   • Validation     │
│   • Recent events│                  │   • Certs tab    │                    │
├──────────────────┼──────────────────┼──────────────────┼────────────────────┤
│   Audit.jsx      │   Trust.jsx      │ Certifications   │   Disputes.jsx     │
│   • Event search │   • Score trends │   • Cert types   │   • File dispute   │
│   • Filters      │   • Distribution │   • Apply wizard │   • Status tracker │
│   • Detail modal │   • At-risk list │   • Expiry alerts│   • Timeline       │
├──────────────────┼──────────────────┼──────────────────┼────────────────────┤
│   Blockchain.jsx │   Settings.jsx   │   Login.jsx      │ CommandPalette.jsx │
│   • Batch list   │   • Profile      │   • Login form   │   • Cmd+K search   │
│   • Pending count│   • Notifications│   • Demo creds   │   • Quick nav      │
│   • BaseScan link│   • API keys     │                  │   • Recent items   │
└──────────────────┴──────────────────┴──────────────────┴────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         API SERVICE LAYER                                    │
│                          (services/api.js)                                   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  axios instance with:                                               │  │
│   │    • Base URL configuration                                         │  │
│   │    • Auth token injection (interceptor)                             │  │
│   │    • API key header (X-MTP-API-Key)                                 │  │
│   │    • Error handling (401 → redirect to login)                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│   │ agentAPI   │ │ auditAPI   │ │ trustAPI   │ │ certAPI    │             │
│   │ • list()   │ │ • list()   │ │ • get()    │ │ • list()   │             │
│   │ • get()    │ │ • get()    │ │ • history()│ │ • apply()  │             │
│   │ • register │ │ • log()    │ │ • breakdown│ │ • renew()  │             │
│   │ • suspend  │ │ • stats()  │ │            │ │            │             │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘             │
│                                                                             │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│   │ disputeAPI │ │blockchainAPI│ │ insuranceAPI│ │ authAPI   │             │
│   │ • list()   │ │ • batches()│ │ • risk()   │ │ • login()  │             │
│   │ • create() │ │ • verify() │ │ • premium()│ │ • logout() │             │
│   │ • update() │ │ • pending()│ │            │ │ • keys()   │             │
│   └────────────┘ └────────────┘ └────────────┘ └────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATABASE SCHEMA                                     │
│                    (PostgreSQL + TimescaleDB)                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL (Relational)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                           │
│  │  organizations  │         │   supervisors   │                           │
│  ├─────────────────┤         ├─────────────────┤                           │
│  │ org_id (PK)     │◄────────│ org_id (FK)     │                           │
│  │ name            │         │ supervisor_id   │                           │
│  │ registration_no │         │ name            │                           │
│  │ status          │         │ email           │                           │
│  │ created_at      │         │ public_key      │                           │
│  └────────┬────────┘         └────────┬────────┘                           │
│           │                           │                                     │
│           │         ┌─────────────────┘                                     │
│           │         │                                                       │
│           ▼         ▼                                                       │
│  ┌─────────────────────┐         ┌─────────────────┐                       │
│  │       agents        │         │     mandates    │                       │
│  ├─────────────────────┤         ├─────────────────┤                       │
│  │ mtp_id (PK)         │◄───────►│ mtp_id (FK)     │                       │
│  │ org_id (FK)         │         │ max_transaction │                       │
│  │ supervisor_id (FK)  │         │ daily_limit     │                       │
│  │ agent_type          │         │ allowed_ops[]   │                       │
│  │ base_model          │         │ forbidden_ops[] │                       │
│  │ public_key          │         │ require_human   │                       │
│  │ status              │         └─────────────────┘                       │
│  │ trust_score         │                                                   │
│  │ created_at          │         ┌─────────────────┐                       │
│  └──────────┬──────────┘         │ certifications  │                       │
│             │                    ├─────────────────┤                       │
│             │                    │ cert_id (PK)    │                       │
│             └───────────────────►│ mtp_id (FK)     │                       │
│                                  │ cert_type       │                       │
│                                  │ status          │                       │
│                                  │ issued_at       │                       │
│                                  │ expires_at      │                       │
│                                  └─────────────────┘                       │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ merkle_batches  │  │    disputes     │  │    api_keys     │            │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤            │
│  │ batch_id (PK)   │  │ dispute_id (PK) │  │ key_id (PK)     │            │
│  │ merkle_root     │  │ mtp_id (FK)     │  │ org_id (FK)     │            │
│  │ event_count     │  │ type            │  │ key_hash        │            │
│  │ tx_hash         │  │ status          │  │ prefix          │            │
│  │ block_number    │  │ resolution      │  │ created_at      │            │
│  │ timestamp       │  │ created_at      │  │ last_used       │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌─────────────────────────────┐                                           │
│  │    trust_score_history      │                                           │
│  ├─────────────────────────────┤                                           │
│  │ id (PK)                     │                                           │
│  │ mtp_id (FK)                 │                                           │
│  │ score                       │                                           │
│  │ reliability                 │                                           │
│  │ compliance                  │                                           │
│  │ transparency                │                                           │
│  │ history_component           │                                           │
│  │ recorded_at                 │                                           │
│  └─────────────────────────────┘                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       TIMESCALEDB (Time-Series)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    audit_events (Hypertable)                         │   │
│  │                  Partitioned by timestamp                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  event_id (PK)        │  UUID, unique identifier                    │   │
│  │  mtp_id (FK)          │  Agent that performed action                │   │
│  │  event_type           │  TRANSACTION, DECISION, POLICY_VIOLATION    │   │
│  │  action_description   │  Human-readable description                 │   │
│  │  input_hash           │  SHA-256 of request payload                 │   │
│  │  output_hash          │  SHA-256 of response payload                │   │
│  │  status               │  SUCCESS, BLOCKED, FAILURE                  │   │
│  │  metadata             │  JSONB for additional context               │   │
│  │  timestamp (PK)       │  Time-series partition key                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Optimized for:                                                            │
│    • Time-range queries: "Events between 08:00 and 09:00"                  │
│    • Agent queries: "All events for MTP-a3f5b2"                            │
│    • Type queries: "All POLICY_VIOLATION events"                           │
│    • Automatic data retention (configurable)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY MODEL                                      │
│                   (Zero-Liability Key Management)                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      KEY MANAGEMENT PRINCIPLE                                │
│                                                                             │
│          "Never hold the weapon; only hold the lock."                       │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │     AGENT                              MTP REGISTRY                 │  │
│   │   ┌───────┐                           ┌───────────┐                 │  │
│   │   │Private│  ◄── Agent holds ──►      │ Public    │                 │  │
│   │   │ Key   │      exclusively          │  Key      │                 │  │
│   │   └───────┘                           └───────────┘                 │  │
│   │       │                                    │                        │  │
│   │       │ Signs requests                     │ Verifies signatures    │  │
│   │       ▼                                    ▼                        │  │
│   │   ┌───────────────┐               ┌───────────────┐                 │  │
│   │   │ X-MTP-Sig:    │  ──────────►  │ Ed25519       │                 │  │
│   │   │ ed25519(msg)  │               │ Verify(sig)   │                 │  │
│   │   └───────────────┘               └───────────────┘                 │  │
│   │                                                                     │  │
│   │   LIABILITY:                       LIABILITY:                       │  │
│   │   • Key compromise = Agent's       • Registry integrity = MTP's    │  │
│   │   • Misuse = Agent's               • Revocation = MTP's            │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION LAYERS                                   │
│                                                                             │
│   Layer 1: API Key (Organization Level)                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Header: X-MTP-API-Key: mtp_prod_xxxxxxxxxxxxxxxx                   │  │
│   │  Purpose: Identify organization, rate limiting, billing             │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Layer 2: Ed25519 Signature (Agent Level)                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Header: X-MTP-Signature: base64(ed25519.sign(payload))             │  │
│   │  Header: X-MTP-Timestamp: 2024-02-26T10:30:00Z                      │  │
│   │  Header: X-MTP-ID: MTP-a3f5b2-7k9m2p                                │  │
│   │  Purpose: Cryptographic proof of agent identity                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   Layer 3: JWT Token (Dashboard Users)                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...              │  │
│   │  Purpose: Session management for human users                        │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT ARCHITECTURE                                 │
│                        (Production Setup)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                           │
│                              │                                               │
│                              ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │   CloudFlare    │                                      │
│                    │   (CDN + WAF)   │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│            ┌────────────────┼────────────────┐                              │
│            │                │                │                               │
│            ▼                ▼                ▼                               │
│     ┌───────────┐    ┌───────────┐    ┌───────────┐                        │
│     │  Frontend │    │  Backend  │    │  Backend  │                        │
│     │  (Vercel) │    │ (AWS ECS) │    │ (AWS ECS) │                        │
│     │  React    │    │  FastAPI  │    │  FastAPI  │                        │
│     │  Static   │    │ Instance 1│    │ Instance 2│                        │
│     └───────────┘    └─────┬─────┘    └─────┬─────┘                        │
│                            │                │                               │
│                            └────────┬───────┘                               │
│                                     │                                       │
│                                     ▼                                       │
│                           ┌─────────────────┐                               │
│                           │   Application   │                               │
│                           │ Load Balancer   │                               │
│                           └────────┬────────┘                               │
│                                    │                                        │
│            ┌───────────────────────┼───────────────────────┐               │
│            │                       │                       │                │
│            ▼                       ▼                       ▼                │
│     ┌───────────────┐       ┌───────────────┐       ┌───────────────┐      │
│     │  PostgreSQL   │       │  TimescaleDB  │       │   Redis       │      │
│     │  (AWS RDS)    │       │  (AWS RDS)    │       │   (Cache)     │      │
│     │  Primary      │       │  Primary      │       │               │      │
│     └───────┬───────┘       └───────┬───────┘       └───────────────┘      │
│             │                       │                                       │
│             ▼                       ▼                                       │
│     ┌───────────────┐       ┌───────────────┐                              │
│     │  PostgreSQL   │       │  TimescaleDB  │                              │
│     │  (Read Replica)│      │  (Read Replica)│                             │
│     └───────────────┘       └───────────────┘                              │
│                                                                             │
│                                    │                                        │
│                                    ▼                                        │
│                           ┌─────────────────┐                               │
│                           │   Base L2       │                               │
│                           │   Mainnet       │                               │
│                           │   (Blockchain)  │                               │
│                           └─────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING & OBSERVABILITY                            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   Prometheus    │  │    Grafana      │  │   PagerDuty     │            │
│   │   (Metrics)     │  │   (Dashboards)  │  │   (Alerting)    │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   CloudWatch    │  │    Sentry       │  │   DataDog       │            │
│   │   (AWS Logs)    │  │ (Error Tracking)│  │   (APM)         │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WebSocket Real-time Updates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WEBSOCKET ARCHITECTURE                                  │
│                    (Real-time Event Streaming)                              │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         FRONTEND CLIENTS                                 │
  │                                                                         │
  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
  │   │  Dashboard   │    │ Agent Detail │    │   Audit      │             │
  │   │   Page       │    │    Page      │    │   Explorer   │             │
  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │
  │          │                   │                   │                      │
  │          └───────────────────┼───────────────────┘                      │
  │                              │                                          │
  │                    ┌─────────▼─────────┐                               │
  │                    │  useWebSocket()   │                               │
  │                    │  React Hook       │                               │
  │                    │  • Auto-reconnect │                               │
  │                    │  • Subscriptions  │                               │
  │                    │  • Event handlers │                               │
  │                    └─────────┬─────────┘                               │
  │                              │                                          │
  └──────────────────────────────┼──────────────────────────────────────────┘
                                 │
                       WebSocket │ ws://api.mtp.io/api/ws/connect
                                 │
  ┌──────────────────────────────┼──────────────────────────────────────────┐
  │                              ▼                                          │
  │   ┌─────────────────────────────────────────────────────────────────┐  │
  │   │                    WEBSOCKET MANAGER                             │  │
  │   │                  (backend/mtp_core/services/websocket.py)        │  │
  │   │                                                                  │  │
  │   │   ┌──────────────────────────────────────────────────────────┐  │  │
  │   │   │  Connection Pool                                          │  │  │
  │   │   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │  │  │
  │   │   │  │Client 1│ │Client 2│ │Client 3│ │Client N│             │  │  │
  │   │   │  │user_id │ │org_id  │ │anon    │ │...     │             │  │  │
  │   │   │  └────────┘ └────────┘ └────────┘ └────────┘             │  │  │
  │   │   └──────────────────────────────────────────────────────────┘  │  │
  │   │                              │                                   │  │
  │   │   ┌──────────────────────────▼───────────────────────────────┐  │  │
  │   │   │  Subscription Management                                  │  │  │
  │   │   │                                                          │  │  │
  │   │   │  agent_subscriptions: { mtp_id → [client_ids] }          │  │  │
  │   │   │  org_subscriptions:   { org_id → [client_ids] }          │  │  │
  │   │   │  event_subscriptions: { event_type → [client_ids] }      │  │  │
  │   │   └──────────────────────────────────────────────────────────┘  │  │
  │   └─────────────────────────────────────────────────────────────────┘  │
  │                              │                                          │
  │         ┌────────────────────┼────────────────────┐                    │
  │         │                    │                    │                     │
  │         ▼                    ▼                    ▼                     │
  │   ┌───────────┐       ┌───────────┐       ┌───────────┐                │
  │   │ AUDIT     │       │ TRUST     │       │ KILL      │                │
  │   │ SERVICE   │       │ SERVICE   │       │ SWITCH    │                │
  │   │           │       │           │       │           │                │
  │   │ → broadcast│      │ → broadcast│      │ → broadcast│               │
  │   │  _audit_  │       │  _trust_  │       │  _kill_   │                │
  │   │  event()  │       │  update() │       │  switch() │                │
  │   └───────────┘       └───────────┘       └───────────┘                │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  EVENT TYPES:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ • audit_event          - New audit event logged                         │
  │ • audit_batch_anchored - Batch anchored to blockchain                   │
  │ • trust_score_update   - Agent trust score changed                      │
  │ • trust_threshold_alert- Trust dropped below threshold                  │
  │ • kill_switch_triggered- Agent suspended                                │
  │ • agent_activated      - Agent reactivated                              │
  │ • certification_granted- New certification issued                       │
  │ • dispute_filed        - New dispute created                            │
  │ • system_alert         - MTP-MONITOR alert                              │
  │ • metrics_update       - System metrics broadcast                       │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## MTP-MONITOR Alerting Service

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MTP-MONITOR SERVICE                                  │
│                      (Alerting & Metrics)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        MONITORING LOOP                                   │
  │                    (runs every 10 seconds)                              │
  │                                                                         │
  │   ┌──────────────────────────────────────────────────────────────────┐ │
  │   │  1. Collect Metrics                                               │ │
  │   │     • WebSocket client count                                      │ │
  │   │     • Batch processor status                                      │ │
  │   │     • Pending events count                                        │ │
  │   │     • Active alert count                                          │ │
  │   └───────────────────────────────┬──────────────────────────────────┘ │
  │                                   │                                     │
  │   ┌───────────────────────────────▼──────────────────────────────────┐ │
  │   │  2. Check Monitoring Rules                                        │ │
  │   │     • Trust score thresholds                                      │ │
  │   │     • Error rate thresholds                                       │ │
  │   │     • System health checks                                        │ │
  │   └───────────────────────────────┬──────────────────────────────────┘ │
  │                                   │                                     │
  │   ┌───────────────────────────────▼──────────────────────────────────┐ │
  │   │  3. Broadcast Metrics                                             │ │
  │   │     → WebSocket: metrics_update event                            │ │
  │   └──────────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────────┘

  ALERT TRIGGERS:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │   TRUST SCORE MONITORING                                               │
  │   ┌────────────────────────────────────────────────────────────────┐  │
  │   │  • Trust < 300 → CRITICAL alert                                 │  │
  │   │  • Trust < 500 → WARNING alert                                  │  │
  │   │  • Trust drop > 10% → WARNING alert                             │  │
  │   └────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │   SYSTEM HEALTH MONITORING                                             │
  │   ┌────────────────────────────────────────────────────────────────┐  │
  │   │  • Error rate > 10% → WARNING/CRITICAL                          │  │
  │   │  • Batch anchor failure → CRITICAL                              │  │
  │   │  • Kill switch triggered → EMERGENCY                            │  │
  │   └────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │   ALERT SEVERITIES                                                     │
  │   ┌────────────────────────────────────────────────────────────────┐  │
  │   │  INFO      → Informational, no action required                  │  │
  │   │  WARNING   → Attention needed, not urgent                       │  │
  │   │  CRITICAL  → Immediate attention required                       │  │
  │   │  EMERGENCY → Kill switch or system failure                      │  │
  │   └────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  API ENDPOINTS:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  GET  /api/v1/monitor/alerts          - List alerts (with filters)     │
  │  GET  /api/v1/monitor/alerts/{id}     - Get specific alert             │
  │  POST /api/v1/monitor/alerts/{id}/acknowledge - Acknowledge alert      │
  │  GET  /api/v1/monitor/metrics         - Get current metrics            │
  │  GET  /api/v1/monitor/status          - Get monitoring service status  │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | Dec 2024 | MVP - Core enforcement system |
| 0.2.0 | Dec 2024 | Added MTP-TRUST, MTP-CERT services |
| 0.3.0 | Dec 2024 | Complete frontend dashboard |
| 0.4.0 | Dec 2024 | Production infrastructure (Docker, CI/CD, WebSocket, MTP-MONITOR) |

---

*Machine Trust Protocol - "Basel III for AI Agents"*
