"""Blockchain Service - Base L2 Anchoring"""
import logging
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount

from mtp_core.core.config import settings

logger = logging.getLogger(__name__)


class BlockchainService:
    """
    Base L2 Anchoring Service.
    
    This is what makes MTP a Protocol, not just a database.
    
    The Pitch:
    "This audit trail is mathematically impossible to alter.
    Can your current IT department do that?"
    
    We anchor Merkle roots to Base L2 (Sepolia testnet for now).
    This creates immutable proof that events occurred.
    """
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.account: Optional[LocalAccount] = None
        self.contract_address: Optional[str] = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize Web3 connection and account"""
        try:
            # Connect to Base L2 RPC
            self.w3 = Web3(Web3.HTTPProvider(settings.base_l2_rpc_url))
            
            if not self.w3.is_connected():
                logger.error(f"Failed to connect to Base L2 at {settings.base_l2_rpc_url}")
                return
            
            logger.info(f"Connected to Base L2 (Chain ID: {settings.base_l2_chain_id})")
            
            # Load account from private key (if provided)
            if settings.base_l2_private_key:
                self.account = Account.from_key(settings.base_l2_private_key)
                logger.info(f"Blockchain account loaded: {self.account.address}")
            else:
                logger.warning("No BASE_L2_PRIVATE_KEY provided. Blockchain anchoring will not work.")
            
            # Load contract address (if deployed)
            if settings.mtp_registry_contract:
                self.contract_address = settings.mtp_registry_contract
                logger.info(f"MTP Registry Contract: {self.contract_address}")
            else:
                logger.warning("No MTP_REGISTRY_CONTRACT provided. Using direct transactions for now.")
        
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
    
    async def anchor_merkle_root(
        self,
        merkle_root: str,
        event_count: int
    ) -> Optional[Dict[str, Any]]:
        """
        Anchor a Merkle root to Base L2.
        
        Args:
            merkle_root: The Merkle root hash to anchor
            event_count: Number of events in the batch
        
        Returns:
            Dict with tx_hash and block_number, or None if failed
        """
        if not self.w3 or not self.account:
            logger.error("Blockchain service not initialized")
            return None
        
        try:
            # For now, we'll send a simple transaction with the Merkle root in the data field
            # In production, this would call the MTPRegistry smart contract
            
            # Encode Merkle root as hex data
            data = f"0xMTP{merkle_root}".encode().hex()
            
            # Build transaction
            tx = {
                'from': self.account.address,
                'to': self.contract_address or self.account.address,  # Self-send if no contract
                'value': 0,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': settings.base_l2_chain_id,
                'data': f"0x{data}"
            }
            
            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            block_number = tx_receipt['blockNumber']
            tx_hash_hex = tx_hash.hex()
            
            logger.info(
                f"Merkle root anchored to Base L2: "
                f"tx={tx_hash_hex}, block={block_number}, events={event_count}"
            )
            
            return {
                'tx_hash': tx_hash_hex,
                'block_number': block_number,
                'merkle_root': merkle_root,
                'event_count': event_count
            }
        
        except Exception as e:
            logger.error(f"Failed to anchor Merkle root: {e}")
            return None
    
    async def verify_anchoring(
        self,
        tx_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify that a transaction exists on Base L2.
        
        Args:
            tx_hash: Transaction hash to verify
        
        Returns:
            Transaction details or None
        """
        if not self.w3:
            return None
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'tx_hash': tx_hash,
                'block_number': tx_receipt['blockNumber'],
                'status': tx_receipt['status'],
                'from': tx['from'],
                'to': tx['to'],
                'gas_used': tx_receipt['gasUsed']
            }
        except Exception as e:
            logger.error(f"Failed to verify transaction {tx_hash}: {e}")
            return None
    
    def get_basescan_url(self, tx_hash: str) -> str:
        """
        Get the BaseScan URL for a transaction.
        
        This is what you show to the Whales:
        "Here is the proof on the blockchain. Click this link."
        
        Args:
            tx_hash: Transaction hash
        
        Returns:
            BaseScan URL
        """
        if settings.base_l2_chain_id == 84532:  # Base Sepolia
            return f"https://sepolia.basescan.org/tx/{tx_hash}"
        elif settings.base_l2_chain_id == 8453:  # Base Mainnet
            return f"https://basescan.org/tx/{tx_hash}"
        else:
            return f"https://explorer.base.org/tx/{tx_hash}"
