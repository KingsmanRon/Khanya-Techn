"""Configuration Management for MTP"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')


class Settings(BaseSettings):
    """MTP System Configuration"""
    
    # PostgreSQL Configuration
    postgres_url: str = os.getenv(
        "POSTGRES_URL",
        "postgresql+asyncpg://mtp_user:mtp_password@localhost:5432/mtp_db"
    )
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10
    
    # Base L2 Blockchain Configuration
    base_l2_rpc_url: str = os.getenv(
        "BASE_L2_RPC_URL",
        "https://sepolia.base.org"  # Base Sepolia Testnet
    )
    base_l2_chain_id: int = 84532  # Base Sepolia
    base_l2_private_key: Optional[str] = os.getenv("BASE_L2_PRIVATE_KEY")
    mtp_registry_contract: Optional[str] = os.getenv("MTP_REGISTRY_CONTRACT")
    
    # Merkle Batching Configuration
    merkle_batch_size: int = 100  # Events per batch
    merkle_batch_interval_seconds: int = 300  # 5 minutes
    
    # Security Configuration
    api_key_header: str = "X-MTP-API-Key"
    signature_header: str = "X-MTP-Signature"
    timestamp_header: str = "X-MTP-Timestamp"
    signature_validity_seconds: int = 300  # 5 minutes
    
    # System Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
