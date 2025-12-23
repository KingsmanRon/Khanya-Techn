"""Machine Trust Protocol - FastAPI Server"""
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# MTP Imports
from mtp_core.api import gateway, identity, audit
from mtp_core.api import disputes, insurance, api_keys
from mtp_core.db.postgres import init_db, db_pool
from mtp_core.core.config import settings
from mtp_core.services.batch_processor import batch_processor

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("="*60)
    logger.info("MACHINE TRUST PROTOCOL - INITIALIZING")
    logger.info("="*60)

    # Initialize database
    try:
        await init_db()
        logger.info("PostgreSQL + TimescaleDB initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database (some features will not work)")

    # Start batch processor for blockchain anchoring
    try:
        await batch_processor.start()
        logger.info("Batch processor started")
    except Exception as e:
        logger.error(f"Batch processor failed to start: {e}")

    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Base L2 RPC: {settings.base_l2_rpc_url}")
    logger.info("="*60)
    logger.info("MTP CORE SYSTEM OPERATIONAL")
    logger.info("="*60)

    yield

    # Shutdown
    logger.info("Shutting down MTP...")
    await batch_processor.stop()
    await db_pool.disconnect()


# Create the main app
app = FastAPI(
    title="Machine Trust Protocol",
    description="Basel III for AI Agents - Core Enforcement System",
    version="0.1.0",
    lifespan=lifespan
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Root endpoint
@api_router.get("/")
async def root():
    return {
        "protocol": "Machine Trust Protocol",
        "version": "0.1.0",
        "tagline": "The Kill Switch for AI Agents",
        "status": "operational",
        "environment": settings.environment
    }

# Health check
@api_router.get("/health")
async def health():
    pending_events = await batch_processor.get_pending_count()
    return {
        "status": "healthy",
        "database": "connected",
        "blockchain": "connected" if settings.base_l2_private_key else "not_configured",
        "batch_processor": {
            "running": batch_processor._running,
            "pending_events": pending_events
        }
    }

# Include MTP routers
api_router.include_router(gateway.router)
api_router.include_router(identity.router)
api_router.include_router(audit.router)
api_router.include_router(disputes.router)
api_router.include_router(insurance.router)
api_router.include_router(api_keys.router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("FastAPI server configured successfully")
