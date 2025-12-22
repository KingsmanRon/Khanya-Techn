# Machine Trust Protocol (MTP)
## Integration Architecture: The "Stripe for AI Trust" Model

**Goal:** Make MTP integration as simple as Stripe—a few lines of code to add identity, audit, and trust to any AI agent deployment.

---

## The Vision: 3 Lines of Code

```python
# Before MTP
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(model="claude-sonnet-4-20250514", messages=[...])

# After MTP (3 lines changed)
from mtp import MTPClient
client = MTPClient(api_key="sk_mtp_live_...", agent_id="mtp_za_ecom_acme_cs_x7k2")
response = client.messages.create(model="claude-sonnet-4-20250514", messages=[...])
# ✓ Identity verified, audit logged, trust score updated automatically
```

---

## Integration Models Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MTP INTEGRATION MODELS                                    │
│                                                                             │
│   Choose the model that fits your architecture:                             │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   MODEL 1       │  │   MODEL 2       │  │   MODEL 3       │            │
│   │   SDK WRAPPER   │  │   PROXY/GATEWAY │  │   WEBHOOK       │            │
│   │                 │  │                 │  │                 │            │
│   │   Best for:     │  │   Best for:     │  │   Best for:     │            │
│   │   New projects  │  │   Existing apps │  │   Legacy systems│            │
│   │   Full control  │  │   Zero code     │  │   Async logging │            │
│   │                 │  │   change        │  │                 │            │
│   │   Effort: Low   │  │   Effort: Low   │  │   Effort: Medium│            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   MODEL 4       │  │   MODEL 5       │  │   MODEL 6       │            │
│   │   SIDECAR       │  │   FRAMEWORK     │  │   NATIVE        │            │
│   │                 │  │   PLUGIN        │  │   (Future)      │            │
│   │   Best for:     │  │   Best for:     │  │                 │            │
│   │   Kubernetes    │  │   LangChain     │  │   Best for:     │            │
│   │   Microservices │  │   AutoGen users │  │   Everyone      │            │
│   │                 │  │                 │  │   (Anthropic    │            │
│   │   Effort: Low   │  │   Effort: Low   │  │    native)      │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Model 1: SDK Wrapper (Recommended for New Projects)

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SDK WRAPPER MODEL                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    Your Application
          │
          ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                     MTP SDK                                         │
    │  ┌───────────────────────────────────────────────────────────────┐ │
    │  │  • Wraps Anthropic/OpenAI client                              │ │
    │  │  • Auto-signs requests                                        │ │
    │  │  • Auto-logs events                                           │ │
    │  │  • Checks mandate before execution                            │ │
    │  │  • Updates trust score                                        │ │
    │  └───────────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────┬───────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌─────────────────┐                ┌─────────────────┐
          │   AI Provider   │                │   MTP Backend   │
          │   (Anthropic)   │                │   (Audit/Trust) │
          └─────────────────┘                └─────────────────┘
```

### Python SDK

```python
# Installation
# pip install mtp-sdk

# ============================================================
# BASIC USAGE - Drop-in replacement for Anthropic client
# ============================================================

from mtp import MTPAnthropic

# Initialize with MTP credentials
client = MTPAnthropic(
    mtp_api_key="sk_mtp_live_abc123",          # Your MTP API key
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2",   # Your registered agent
    anthropic_api_key="sk-ant-..."              # Optional: uses env var if not set
)

# Use exactly like the normal Anthropic client
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "I want to return my order #12345"}
    ]
)

# That's it! MTP automatically:
# ✓ Verified agent identity before the call
# ✓ Checked the action is within mandate
# ✓ Logged the request/response to audit trail
# ✓ Updated trust score based on outcome
# ✓ Anchored to blockchain in background

print(response.content[0].text)


# ============================================================
# WITH TOOLS - Automatic tool call auditing
# ============================================================

tools = [
    {
        "name": "process_refund",
        "description": "Process a refund for an order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"}
            },
            "required": ["order_id", "amount"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "Please refund order #12345 for R450"}
    ]
)

# MTP automatically:
# ✓ Logged each tool call with input hash
# ✓ Verified refund amount is within agent's mandate (R1000 limit)
# ✓ Created audit event with transaction details
# ✓ Would have blocked if amount exceeded limit


# ============================================================
# WITH CONTEXT - Enhanced audit trail
# ============================================================

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[...],
    
    # MTP-specific context (optional but recommended)
    mtp_context={
        "user_id": "customer_789",           # Links audit to user
        "session_id": "sess_abc123",         # Groups related events
        "transaction_value": 450.00,         # For financial tracking
        "transaction_currency": "ZAR",
        "metadata": {                         # Custom fields
            "order_id": "ORD-12345",
            "channel": "web_chat"
        }
    }
)


# ============================================================
# ASYNC SUPPORT
# ============================================================

from mtp import AsyncMTPAnthropic

async_client = AsyncMTPAnthropic(
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2"
)

async def handle_customer():
    response = await async_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[...]
    )
    return response


# ============================================================
# STREAMING SUPPORT
# ============================================================

with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[...]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# MTP logs the complete response after stream ends
```

### JavaScript/TypeScript SDK

```typescript
// Installation
// npm install @mtp/sdk

// ============================================================
// BASIC USAGE
// ============================================================

import { MTPAnthropic } from '@mtp/sdk';

const client = new MTPAnthropic({
  mtpApiKey: 'sk_mtp_live_abc123',
  mtpAgentId: 'mtp_za_ecom_acme_cs_x7k2',
  anthropicApiKey: process.env.ANTHROPIC_API_KEY  // Optional
});

const response = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'I want to return my order #12345' }
  ]
});

console.log(response.content[0].text);


// ============================================================
// EXPRESS.JS MIDDLEWARE
// ============================================================

import express from 'express';
import { mtpMiddleware } from '@mtp/sdk/express';

const app = express();

// Add MTP middleware - automatically logs all AI interactions
app.use(mtpMiddleware({
  apiKey: 'sk_mtp_live_abc123',
  agentId: 'mtp_za_ecom_acme_cs_x7k2'
}));

app.post('/chat', async (req, res) => {
  // req.mtp is automatically available
  const response = await req.mtp.messages.create({
    model: 'claude-sonnet-4-20250514',
    messages: req.body.messages,
    mtp_context: {
      user_id: req.user.id,
      session_id: req.sessionID
    }
  });
  
  res.json(response);
});


// ============================================================
// NEXT.JS API ROUTE
// ============================================================

// app/api/chat/route.ts
import { MTPAnthropic } from '@mtp/sdk';
import { NextRequest, NextResponse } from 'next/server';

const client = new MTPAnthropic({
  mtpApiKey: process.env.MTP_API_KEY!,
  mtpAgentId: process.env.MTP_AGENT_ID!
});

export async function POST(req: NextRequest) {
  const { messages, userId } = await req.json();
  
  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1024,
    messages,
    mtp_context: { user_id: userId }
  });
  
  return NextResponse.json(response);
}
```

### OpenAI SDK Wrapper

```python
# Same pattern works for OpenAI
from mtp import MTPOpenAI

client = MTPOpenAI(
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_ecom_acme_gpt_x7k2",
    openai_api_key="sk-..."  # Optional
)

response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "user", "content": "Help me with my order"}
    ]
)

# Identical MTP benefits - provider agnostic
```

---

## Model 2: Proxy/Gateway (Zero Code Change)

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROXY/GATEWAY MODEL                                    │
│                                                                             │
│   Your existing code stays exactly the same!                                │
│   Just change the API endpoint.                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    Your Application                          
    (No code changes!)                        
          │                                   
          │ api.anthropic.com → api.mtp.proxy
          │                                   
          ▼                                   
    ┌─────────────────────────────────────────────────────────────────────┐
    │                       MTP PROXY                                      │
    │                                                                      │
    │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
    │   │   Verify    │    │   Forward   │    │    Log      │            │
    │   │   Agent     │───►│   to AI     │───►│   Audit     │            │
    │   │   Identity  │    │   Provider  │    │   Event     │            │
    │   └─────────────┘    └─────────────┘    └─────────────┘            │
    │                                                                      │
    └─────────────────────────────────┬───────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌─────────────────┐                ┌─────────────────┐
          │   AI Provider   │                │   MTP Backend   │
          │   (Anthropic)   │                │   (Audit/Trust) │
          └─────────────────┘                └─────────────────┘
```

### Setup (2 Minutes)

```bash
# Step 1: Get your proxy endpoint from MTP dashboard
# https://dashboard.mtprotocol.io/proxy

# Step 2: Set environment variable
export ANTHROPIC_BASE_URL="https://proxy.mtprotocol.io/v1/anthropic"
export MTP_AGENT_ID="mtp_za_ecom_acme_cs_x7k2"
export MTP_API_KEY="sk_mtp_live_abc123"

# Step 3: Your existing code works unchanged!
```

```python
# Your existing code - NO CHANGES NEEDED
from anthropic import Anthropic

client = Anthropic()  # Automatically uses ANTHROPIC_BASE_URL

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

# MTP proxy automatically:
# ✓ Extracts agent ID from header/env
# ✓ Verifies identity
# ✓ Forwards to real Anthropic API
# ✓ Logs audit event
# ✓ Returns response unchanged
```

### Custom Headers (More Control)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://proxy.mtprotocol.io/v1/anthropic",
    default_headers={
        "X-MTP-Agent-ID": "mtp_za_ecom_acme_cs_x7k2",
        "X-MTP-API-Key": "sk_mtp_live_abc123",
        "X-MTP-User-ID": "customer_789",      # Optional context
        "X-MTP-Session-ID": "sess_abc123"     # Optional context
    }
)

# Everything else stays the same
response = client.messages.create(...)
```

### Docker Compose (Self-Hosted Proxy)

```yaml
# docker-compose.yml
version: '3.8'

services:
  mtp-proxy:
    image: mtprotocol/proxy:latest
    ports:
      - "8080:8080"
    environment:
      - MTP_API_KEY=sk_mtp_live_abc123
      - MTP_AGENT_ID=mtp_za_ecom_acme_cs_x7k2
      - ANTHROPIC_API_KEY=sk-ant-...
      - UPSTREAM_URL=https://api.anthropic.com
    
  your-app:
    build: .
    environment:
      - ANTHROPIC_BASE_URL=http://mtp-proxy:8080/v1
    depends_on:
      - mtp-proxy
```

---

## Model 3: Webhook Integration (Async Logging)

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       WEBHOOK MODEL                                          │
│                                                                             │
│   For when you can't modify the AI call path                                │
│   Log events after the fact via webhooks                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    Your Application                          
          │                                   
          ├───────────────────────────────────────────┐
          │                                           │
          ▼                                           ▼
    ┌─────────────────┐                     ┌─────────────────┐
    │   AI Provider   │                     │   Your Webhook  │
    │   (Direct)      │                     │   Handler       │
    └─────────────────┘                     └────────┬────────┘
                                                     │
                                                     │ POST /mtp/events
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │   MTP Backend   │
                                            │   (Audit/Trust) │
                                            └─────────────────┘
```

### Implementation

```python
import httpx
from your_app import after_ai_call  # Your hook system

MTP_ENDPOINT = "https://api.mtprotocol.io/v1/events"
MTP_API_KEY = "sk_mtp_live_abc123"
MTP_AGENT_ID = "mtp_za_ecom_acme_cs_x7k2"

async def log_to_mtp(event_data: dict):
    """Send audit event to MTP after AI call completes"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MTP_ENDPOINT,
            headers={
                "Authorization": f"Bearer {MTP_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "mtp_id": MTP_AGENT_ID,
                "event_type": event_data["type"],
                "action_name": event_data["action"],
                "status": event_data["status"],
                "input_hash": hash_content(event_data["input"]),
                "output_hash": hash_content(event_data["output"]),
                "user_identifier": event_data.get("user_id"),
                "session_id": event_data.get("session_id"),
                "transaction_amount": event_data.get("amount"),
                "metadata": event_data.get("metadata", {})
            }
        )
        return response.json()


# Hook into your existing system
@after_ai_call
async def mtp_audit_hook(request, response, context):
    """Called after every AI interaction"""
    
    await log_to_mtp({
        "type": "AI_INTERACTION",
        "action": "messages.create",
        "status": "SUCCESS" if not response.error else "FAILURE",
        "input": request.messages,
        "output": response.content,
        "user_id": context.user_id,
        "session_id": context.session_id,
        "metadata": {
            "model": request.model,
            "tokens_used": response.usage.total_tokens
        }
    })
```

---

## Model 4: Kubernetes Sidecar

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SIDECAR MODEL                                          │
│                                                                             │
│   MTP runs alongside your app in the same pod                               │
│   Intercepts traffic automatically                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         KUBERNETES POD                               │
    │                                                                      │
    │   ┌─────────────────────┐        ┌─────────────────────┐           │
    │   │                     │        │                     │           │
    │   │   Your Application  │◄──────►│   MTP Sidecar       │           │
    │   │   Container         │        │   Container         │           │
    │   │                     │        │                     │           │
    │   │   localhost:8080    │        │   localhost:9090    │           │
    │   │                     │        │   (intercepts AI    │           │
    │   │                     │        │    traffic)         │           │
    │   └─────────────────────┘        └──────────┬──────────┘           │
    │                                             │                       │
    └─────────────────────────────────────────────┼───────────────────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    │                           │
                                    ▼                           ▼
                          ┌─────────────────┐        ┌─────────────────┐
                          │   AI Provider   │        │   MTP Backend   │
                          └─────────────────┘        └─────────────────┘
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent
  template:
    metadata:
      labels:
        app: ai-agent
      annotations:
        mtp.io/inject: "true"  # Auto-inject sidecar
    spec:
      containers:
        # Your application container
        - name: app
          image: your-app:latest
          ports:
            - containerPort: 8080
          env:
            # Point AI calls to sidecar
            - name: ANTHROPIC_BASE_URL
              value: "http://localhost:9090/v1/anthropic"
        
        # MTP Sidecar (auto-injected or manual)
        - name: mtp-sidecar
          image: mtprotocol/sidecar:latest
          ports:
            - containerPort: 9090
          env:
            - name: MTP_API_KEY
              valueFrom:
                secretKeyRef:
                  name: mtp-credentials
                  key: api-key
            - name: MTP_AGENT_ID
              value: "mtp_za_ecom_acme_cs_x7k2"
          resources:
            limits:
              memory: "128Mi"
              cpu: "100m"

---
# Automatic sidecar injection (like Istio)
apiVersion: v1
kind: Namespace
metadata:
  name: ai-agents
  labels:
    mtp.io/injection: enabled
```

### Helm Chart

```bash
# Install MTP sidecar injector
helm repo add mtp https://charts.mtprotocol.io
helm install mtp-injector mtp/sidecar-injector \
  --namespace mtp-system \
  --set apiKey=sk_mtp_live_abc123

# Your deployments in labeled namespaces automatically get MTP sidecar
```

---

## Model 5: Framework Plugins

### LangChain Integration

```python
# pip install mtp-langchain

from langchain_anthropic import ChatAnthropic
from mtp_langchain import MTPCallbackHandler, MTPWrapper

# Option 1: Callback Handler (logging only)
mtp_handler = MTPCallbackHandler(
    api_key="sk_mtp_live_abc123",
    agent_id="mtp_za_ecom_acme_cs_x7k2"
)

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

response = llm.invoke(
    "Help me with my order",
    config={"callbacks": [mtp_handler]}
)

# Option 2: Full Wrapper (logging + enforcement)
llm = MTPWrapper(
    llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2"
)

# Automatically enforces mandate, logs tools, etc.
response = llm.invoke("Process refund for $500")


# ============================================================
# LANGCHAIN AGENT WITH MTP
# ============================================================

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([...])
tools = [refund_tool, order_lookup_tool, shipping_tool]

# Wrap the LLM
mtp_llm = MTPWrapper(
    llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2"
)

agent = create_tool_calling_agent(mtp_llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# Every tool call is automatically audited
result = executor.invoke({"input": "Refund order #12345"})
```

### AutoGen Integration

```python
# pip install mtp-autogen

from autogen import AssistantAgent, UserProxyAgent
from mtp_autogen import MTPAssistantAgent

# Replace AssistantAgent with MTP version
assistant = MTPAssistantAgent(
    name="customer_service_agent",
    llm_config={"model": "claude-sonnet-4-20250514"},
    mtp_config={
        "api_key": "sk_mtp_live_abc123",
        "agent_id": "mtp_za_ecom_acme_cs_x7k2"
    }
)

user_proxy = UserProxyAgent(
    name="customer",
    human_input_mode="NEVER"
)

# All interactions automatically audited
user_proxy.initiate_chat(
    assistant,
    message="I need help with my order"
)
```

### CrewAI Integration

```python
# pip install mtp-crewai

from crewai import Agent, Task, Crew
from mtp_crewai import MTPAgent

# Use MTPAgent instead of Agent
customer_service = MTPAgent(
    role="Customer Service Representative",
    goal="Help customers with orders and refunds",
    backstory="...",
    llm="claude-sonnet-4-20250514",
    mtp_config={
        "api_key": "sk_mtp_live_abc123",
        "agent_id": "mtp_za_ecom_acme_cs_x7k2"
    }
)

# Every agent action is audited
task = Task(
    description="Help the customer return order #12345",
    agent=customer_service
)

crew = Crew(agents=[customer_service], tasks=[task])
result = crew.kickoff()
```

---

## Model 6: Native AI Provider Integration (Future)

### The Dream State

```python
# Future: Native Anthropic integration
from anthropic import Anthropic

client = Anthropic(
    # Native MTP support built into Anthropic SDK
    mtp_enabled=True,
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2"
)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[...]
)

# Anthropic handles MTP integration natively
```

### Partnership Pathway

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NATIVE INTEGRATION ROADMAP                                │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1 (Now)           Phase 2 (6-12mo)         Phase 3 (12-24mo)
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   MTP SDK       │────►│   API Partner   │────►│   Native SDK    │
│   Wrappers      │     │   Integration   │     │   Support       │
│                 │     │                 │     │                 │
│   We wrap their │     │   Anthropic/    │     │   Built into    │
│   SDKs          │     │   OpenAI expose │     │   their SDKs    │
│                 │     │   MTP hooks     │     │   directly      │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Complete Integration Examples

### Example 1: E-Commerce Customer Service Bot

```python
"""
Complete example: E-commerce customer service with MTP
"""

from mtp import MTPAnthropic
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize MTP client
mtp_client = MTPAnthropic(
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_ecom_acme_cs_x7k2"
)

# Define tools the agent can use
TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up order details by order ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for an order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"}
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "update_shipping",
        "description": "Update shipping address for an order",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "new_address": {"type": "object"}
            },
            "required": ["order_id", "new_address"]
        }
    }
]

SYSTEM_PROMPT = """You are a helpful customer service agent for TechRetail. 
You can help customers with:
- Order lookups
- Refunds (up to R1000)
- Shipping updates

Always be polite and helpful. If you can't help with something, 
explain why and offer alternatives."""


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    messages = data.get('messages', [])
    
    # Add system prompt
    full_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + messages
    
    try:
        # Make the AI call with MTP tracking
        response = mtp_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=TOOLS,
            messages=full_messages,
            
            # MTP context for enhanced audit trail
            mtp_context={
                "user_id": user_id,
                "session_id": session_id,
                "metadata": {
                    "channel": "web_chat",
                    "platform": "ecommerce_site"
                }
            }
        )
        
        # Handle tool use if needed
        if response.stop_reason == "tool_use":
            tool_results = execute_tools(response.content)
            
            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # Second call (also tracked by MTP)
            response = mtp_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=TOOLS,
                messages=full_messages + messages,
                mtp_context={
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
        
        return jsonify({
            "response": response.content[0].text,
            "session_id": session_id
        })
        
    except mtp.MandateViolationError as e:
        # MTP blocked the action (e.g., refund too large)
        return jsonify({
            "error": "I'm not authorized to perform that action",
            "details": str(e)
        }), 403
        
    except mtp.AgentSuspendedError:
        # Agent has been suspended
        return jsonify({
            "error": "Service temporarily unavailable"
        }), 503


def execute_tools(content):
    """Execute tool calls and return results"""
    results = []
    
    for block in content:
        if block.type == "tool_use":
            if block.name == "lookup_order":
                result = order_service.lookup(block.input["order_id"])
            elif block.name == "process_refund":
                result = payment_service.refund(
                    block.input["order_id"],
                    block.input["amount"]
                )
            elif block.name == "update_shipping":
                result = shipping_service.update(
                    block.input["order_id"],
                    block.input["new_address"]
                )
            
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result)
            })
    
    return results


if __name__ == '__main__':
    app.run(port=5000)
```

### Example 2: Financial Advisory Agent

```python
"""
Financial advisory agent with strict compliance
"""

from mtp import MTPAnthropic
import mtp

# Financial services agent with stricter controls
client = MTPAnthropic(
    mtp_api_key="sk_mtp_live_abc123",
    mtp_agent_id="mtp_za_fin_wealth_advisor_x7k2",
    
    # Financial services specific options
    mtp_options={
        "require_human_approval_above": 50000,  # ZAR
        "compliance_mode": "strict",
        "record_full_transcript": True,  # For regulatory compliance
        "fsca_compliant": True
    }
)

async def provide_advice(user_id: str, query: str, portfolio: dict):
    """Provide financial advice with full compliance tracking"""
    
    system_prompt = """You are a registered financial advisor assistant.
    
    IMPORTANT COMPLIANCE REQUIREMENTS:
    - Always disclose that you are an AI assistant
    - Never guarantee investment returns
    - Always recommend consulting a human advisor for major decisions
    - Log all recommendations for FSCA compliance
    """
    
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Client Portfolio: {portfolio}
                    
                    Client Question: {query}
                    
                    Please provide advice while maintaining regulatory compliance.
                    """
                }
            ],
            mtp_context={
                "user_id": user_id,
                "transaction_type": "financial_advice",
                "compliance_category": "FSCA_FAIS",
                "metadata": {
                    "portfolio_value": portfolio.get("total_value"),
                    "risk_profile": portfolio.get("risk_profile"),
                    "advice_category": categorize_query(query)
                }
            }
        )
        
        return {
            "advice": response.content[0].text,
            "compliance_id": response.mtp_event_id,  # For audit reference
            "disclaimer": "This advice is provided by an AI assistant..."
        }
        
    except mtp.ComplianceError as e:
        # MTP blocked due to compliance rules
        return {
            "error": "This query requires human advisor review",
            "escalation_reason": str(e),
            "human_advisor_contact": "advisor@wealth.co.za"
        }
```

---

## Dashboard & Management

### Developer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MTP DEVELOPER DASHBOARD                                    [Acme Corp]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QUICK START                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  # Install the SDK                                                   │   │
│  │  pip install mtp-sdk                                                 │   │
│  │                                                                      │   │
│  │  # Your API credentials                                              │   │
│  │  MTP_API_KEY=sk_mtp_live_abc123                                     │   │
│  │  MTP_AGENT_ID=mtp_za_ecom_acme_cs_x7k2                              │   │
│  │                                                                      │   │
│  │  [Copy to Clipboard]                                                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  YOUR AGENTS                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Name                    │ Status  │ Trust  │ Events (24h) │ Actions  │ │
│  │─────────────────────────┼─────────┼────────┼──────────────┼──────────│ │
│  │ Customer Service Agent  │ ● Active│ 847    │ 1,234        │ [Manage] │ │
│  │ Returns Agent           │ ● Active│ 791    │ 567          │ [Manage] │ │
│  │ Upsell Agent            │ ○ Paused│ 723    │ 0            │ [Manage] │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [+ Register New Agent]                                                     │
│                                                                             │
│  INTEGRATION STATUS                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ ✓ SDK Integration     Working    Last event: 2 seconds ago           │ │
│  │ ✓ Webhook Endpoint    Healthy    Response time: 45ms                 │ │
│  │ ✓ Blockchain Anchor   Synced     Last anchor: 5 minutes ago          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  RECENT EVENTS                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ 14:32:01 │ cs_agent │ TOOL_CALL  │ process_refund │ R450   │ SUCCESS │ │
│  │ 14:31:45 │ cs_agent │ MESSAGE    │ response       │ -      │ SUCCESS │ │
│  │ 14:31:42 │ cs_agent │ MESSAGE    │ request        │ -      │ SUCCESS │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [View All Events] [Export Audit Log] [API Documentation]                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pricing Model (Like Stripe)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MTP PRICING                                          │
│                                                                             │
│   Simple, usage-based pricing. No upfront costs.                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   PAY AS YOU GO                                                             │
│                                                                             │
│   Agent Registration          R500/agent/year      (~$27)                   │
│   Audit Events                R0.01/event          (~$0.0005)               │
│   Trust Score Queries         R0.05/query          (~$0.003)                │
│   Verification Queries        R0.10/query          (~$0.005)                │
│                                                                             │
│   Example: 1 agent, 10,000 events/month = ~R600/month                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   VOLUME DISCOUNTS                                                          │
│                                                                             │
│   100K+ events/month          20% discount                                  │
│   1M+ events/month            35% discount                                  │
│   10M+ events/month           50% discount                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ENTERPRISE                                                                │
│                                                                             │
│   Custom pricing for:                                                       │
│   • Unlimited events                                                        │
│   • Dedicated support                                                       │
│   • Custom SLAs                                                             │
│   • On-premise deployment                                                   │
│   • Compliance certifications                                               │
│                                                                             │
│   [Contact Sales]                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Integration Comparison

| Model | Code Changes | Best For | Effort | Features |
|-------|--------------|----------|--------|----------|
| **SDK Wrapper** | 3 lines | New projects | ⭐ | Full |
| **Proxy** | 0 lines | Existing apps | ⭐ | Full |
| **Webhook** | Medium | Legacy systems | ⭐⭐ | Logging only |
| **Sidecar** | Config only | Kubernetes | ⭐ | Full |
| **Framework Plugin** | 1-2 lines | LangChain/etc | ⭐ | Full |
| **Native** | 0 lines | Future | - | Full |

**Recommendation:** Start with **SDK Wrapper** for new projects, **Proxy** for existing applications. Both give full MTP benefits with minimal effort.

---

*"Stripe for AI Trust" - Add identity, audit, and accountability to any AI agent in minutes.*
