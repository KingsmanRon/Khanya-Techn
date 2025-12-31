# MTP Production Checklist

> Everything required to deploy Machine Trust Protocol to production

---

## Overview

This document outlines all decisions, credentials, and configurations required before deploying MTP to a production environment. Complete each section before proceeding with deployment.

---

## 1. Deployment Decisions Required

These decisions affect your infrastructure setup and costs.

### 1.1 Deployment Target

| Option | Pros | Cons | Estimated Cost |
|--------|------|------|----------------|
| **AWS ECS** | Managed containers, auto-scaling, AWS ecosystem | Vendor lock-in | $150-500/mo |
| **AWS EKS** | Kubernetes, portable, flexible | Complex setup | $200-600/mo |
| **Google Cloud Run** | Serverless, pay-per-use | Cold starts | $100-400/mo |
| **Azure Container Apps** | Microsoft ecosystem | Limited regions | $150-500/mo |
| **DigitalOcean App Platform** | Simple, affordable | Less enterprise features | $50-200/mo |
| **Self-hosted (VPS)** | Full control, cheapest | Manual maintenance | $40-150/mo |

**Your Choice:** ______________________

### 1.2 Domain Configuration

| Item | Example | Your Value |
|------|---------|------------|
| Production Domain | `mtp.yourcompany.com` | |
| API Subdomain | `api.mtp.yourcompany.com` | |
| Staging Domain | `staging.mtp.yourcompany.com` | |

**DNS Provider:** ______________________

**SSL Certificate:**
- [ ] Let's Encrypt (free, auto-renewal)
- [ ] CloudFlare (free with proxy)
- [ ] AWS Certificate Manager
- [ ] Custom certificate

### 1.3 Database Hosting

| Option | Pros | Cons | Estimated Cost |
|--------|------|------|----------------|
| **AWS RDS PostgreSQL** | Managed, backups, scaling | Cost | $50-300/mo |
| **Timescale Cloud** | Optimized for TimescaleDB | Specialized | $30-200/mo |
| **DigitalOcean Managed DB** | Simple, affordable | Limited scaling | $15-100/mo |
| **Supabase** | PostgreSQL + extras | Newer platform | $25-100/mo |
| **Self-hosted** | Cheapest | Manual backups/maintenance | $10-50/mo |

**Your Choice:** ______________________

**Database Size Estimate:**
- Expected agents: ______
- Expected events/day: ______
- Retention period: ______ days

### 1.4 Blockchain Network

| Network | Use Case | Gas Costs | Finality |
|---------|----------|-----------|----------|
| **Base Sepolia (Testnet)** | Development, testing | Free (faucet) | ~2 seconds |
| **Base Mainnet** | Production | ~$0.01-0.10/tx | ~2 seconds |

**Your Choice:**
- [ ] Base Sepolia (testing)
- [ ] Base Mainnet (production)

**Contract Deployment:**
- [ ] Deploy new MTP Registry contract
- [ ] Use existing contract at: `0x________________`

### 1.5 CI/CD Platform

| Platform | Integration | Free Tier |
|----------|-------------|-----------|
| **GitHub Actions** | Native GitHub | 2,000 min/mo |
| **GitLab CI** | Native GitLab | 400 min/mo |
| **CircleCI** | Any Git provider | 6,000 min/mo |
| **AWS CodePipeline** | AWS ecosystem | Pay-per-use |

**Your Choice:** ______________________

---

## 2. Required Credentials

Generate and securely store these before deployment.

### 2.1 Blockchain Credentials

```bash
# Generate a new private key (DO NOT use existing wallets with funds)
# Option 1: Use MetaMask to create new wallet
# Option 2: Use ethers.js
node -e "console.log(require('ethers').Wallet.createRandom().privateKey)"
```

| Credential | Description | Format | Status |
|------------|-------------|--------|--------|
| `BASE_L2_PRIVATE_KEY` | Wallet private key for signing transactions | 64 hex chars (no 0x) | [ ] Generated |
| `BASE_L2_RPC_URL` | RPC endpoint URL | URL | [ ] Configured |
| `MTP_REGISTRY_CONTRACT` | Deployed contract address | 0x... (42 chars) | [ ] Deployed |

**Wallet Funding:**
- [ ] Testnet: Get ETH from [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
- [ ] Mainnet: Transfer ~0.05 ETH for gas

### 2.2 Database Credentials

```bash
# Generate secure password
openssl rand -base64 32
```

| Credential | Description | Format | Status |
|------------|-------------|--------|--------|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | [ ] Configured |
| `POSTGRES_USER` | Database username | String | [ ] Created |
| `POSTGRES_PASSWORD` | Database password | 32+ random chars | [ ] Generated |
| `POSTGRES_DB` | Database name | String (e.g., `mtp_prod`) | [ ] Created |

### 2.3 Security Credentials

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate API encryption key
openssl rand -hex 32
```

| Credential | Description | Format | Status |
|------------|-------------|--------|--------|
| `JWT_SECRET` | Secret for signing JWT tokens | 64 hex chars | [ ] Generated |
| `API_ENCRYPTION_KEY` | Key for encrypting API keys at rest | 64 hex chars | [ ] Generated |

### 2.4 Optional Service Credentials

| Credential | Service | Required For | Status |
|------------|---------|--------------|--------|
| `SENTRY_DSN` | Sentry | Error tracking | [ ] Optional |
| `SMTP_HOST/USER/PASS` | Email provider | Email notifications | [ ] Optional |
| `SLACK_WEBHOOK_URL` | Slack | Alert notifications | [ ] Optional |
| `DATADOG_API_KEY` | DataDog | APM monitoring | [ ] Optional |

---

## 3. Environment Configuration

### 3.1 Production Environment Variables

Create a `.env.production` file (never commit to Git):

```bash
# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=production
LOG_LEVEL=INFO

# ===========================================
# DATABASE
# ===========================================
DATABASE_URL=postgresql://mtp_user:YOUR_SECURE_PASSWORD@your-db-host:5432/mtp_prod
POSTGRES_USER=mtp_user
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
POSTGRES_DB=mtp_prod

# ===========================================
# BLOCKCHAIN
# ===========================================
BASE_L2_RPC_URL=https://mainnet.base.org
BASE_L2_PRIVATE_KEY=YOUR_PRIVATE_KEY_WITHOUT_0x
MTP_REGISTRY_CONTRACT=0xYOUR_CONTRACT_ADDRESS

# ===========================================
# SECURITY
# ===========================================
JWT_SECRET=YOUR_64_CHAR_HEX_SECRET
API_ENCRYPTION_KEY=YOUR_64_CHAR_HEX_KEY

# ===========================================
# CORS
# ===========================================
CORS_ORIGINS=https://mtp.yourcompany.com,https://api.mtp.yourcompany.com

# ===========================================
# PORTS
# ===========================================
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 3.2 GitHub Actions Secrets

Add these to your repository settings (Settings → Secrets → Actions):

| Secret Name | Value Source |
|-------------|--------------|
| `DATABASE_URL` | From 2.2 |
| `BASE_L2_PRIVATE_KEY` | From 2.1 |
| `JWT_SECRET` | From 2.3 |
| `API_ENCRYPTION_KEY` | From 2.3 |
| `GHCR_TOKEN` | GitHub token with `packages:write` |

---

## 4. Pre-Deployment Checklist

### 4.1 Security Audit

- [ ] All secrets use environment variables (not hardcoded)
- [ ] `.env` files are in `.gitignore`
- [ ] No API keys or passwords in commit history
- [ ] CORS origins are restrictive (not `*`)
- [ ] Rate limiting is configured
- [ ] JWT expiration is reasonable (24h or less)

### 4.2 Database Preparation

- [ ] Production database created
- [ ] TimescaleDB extension installed
- [ ] Database user has limited privileges
- [ ] Connection pooling configured (PgBouncer recommended)
- [ ] Automated backups enabled
- [ ] Point-in-time recovery configured

### 4.3 Blockchain Preparation

- [ ] Wallet funded with gas
- [ ] MTP Registry contract deployed (or address known)
- [ ] Contract verified on BaseScan
- [ ] Test transaction successful

### 4.4 Monitoring Setup

- [ ] Health check endpoints responding
- [ ] Prometheus scraping configured
- [ ] Grafana dashboards imported
- [ ] Alert rules configured
- [ ] Error tracking (Sentry) connected
- [ ] Log aggregation configured

### 4.5 DNS & SSL

- [ ] DNS records configured
- [ ] SSL certificates issued
- [ ] HTTPS redirect enabled
- [ ] HSTS headers configured

---

## 5. Deployment Commands

### 5.1 Docker Compose (Self-hosted)

```bash
# Pull latest images
docker compose pull

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend

# Run with monitoring
docker compose --profile monitoring up -d
```

### 5.2 GitHub Actions (Automated)

Push to `main` branch triggers:
1. CI pipeline runs tests
2. Docker images built and pushed to GHCR
3. CD pipeline deploys to staging
4. Manual approval for production

---

## 6. Post-Deployment Verification

### 6.1 Health Checks

```bash
# Backend health
curl https://api.mtp.yourcompany.com/api/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "blockchain": "connected",
  "batch_processor": {"running": true, "pending_events": 0},
  "websocket": {"connected_clients": 0},
  "monitor": {"running": true, "active_alerts": 0}
}
```

### 6.2 Functional Tests

- [ ] Frontend loads without errors
- [ ] Login works with demo credentials
- [ ] Agent registration creates new agent
- [ ] Audit events are being logged
- [ ] Trust scores are calculated
- [ ] WebSocket connects and receives events
- [ ] Blockchain batches are being anchored

### 6.3 Performance Baseline

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time (p95) | < 200ms | |
| Kill Switch Latency | < 100ms | |
| Database Query Time | < 50ms | |
| WebSocket Connect Time | < 500ms | |

---

## 7. Rollback Plan

If deployment fails:

```bash
# Revert to previous version
docker compose down
docker compose pull previous-tag
docker compose up -d

# Or with GitHub Actions
# Re-run previous successful deployment
```

---

## 8. Support Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| DevOps Lead | | |
| Database Admin | | |
| Security Team | | |
| On-call Engineer | | |

---

## Document Status

| Section | Status | Last Updated |
|---------|--------|--------------|
| Deployment Decisions | ⏳ Pending | |
| Required Credentials | ⏳ Pending | |
| Environment Config | ⏳ Pending | |
| Pre-Deployment | ⏳ Pending | |

**Ready for Production:** [ ] No - Complete all sections above

---

*Machine Trust Protocol - Production Checklist v1.0*
