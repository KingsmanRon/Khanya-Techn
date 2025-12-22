"""Merkle Tree Implementation for Audit Trail Anchoring"""
import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MerkleProof:
    """Proof of inclusion in a Merkle tree"""
    leaf_hash: str
    root_hash: str
    proof: List[Tuple[str, str]]  # List of (hash, position: 'left'|'right')
    leaf_index: int


class MerkleTree:
    """
    Merkle Tree for batching audit events.
    
    Used to anchor audit trails to the blockchain efficiently.
    Instead of submitting every event to the blockchain (expensive),
    we batch events into a Merkle tree and submit only the root hash.
    """
    
    def __init__(self, leaves: List[str]):
        """
        Initialize Merkle tree from leaf hashes.
        
        Args:
            leaves: List of hex-encoded SHA-256 hashes (event IDs or content hashes)
        """
        if not leaves:
            raise ValueError("Cannot create Merkle tree with no leaves")
        
        self.leaves = leaves
        self.tree = self._build_tree(leaves)
    
    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """Hash two nodes together (sorted to ensure consistency)."""
        if left > right:
            left, right = right, left
        combined = left + right
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _build_tree(self, leaves: List[str]) -> List[List[str]]:
        """Build the Merkle tree from leaves up to root."""
        tree = [leaves]
        
        while len(tree[-1]) > 1:
            current_level = tree[-1]
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate the last one
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = self._hash_pair(left, right)
                next_level.append(parent)
            
            tree.append(next_level)
        
        return tree
    
    def get_root(self) -> str:
        """Get the Merkle root hash."""
        return self.tree[-1][0]
    
    def get_proof(self, leaf_index: int) -> MerkleProof:
        """
        Generate inclusion proof for a specific leaf.
        
        Args:
            leaf_index: Index of the leaf in the original list
        
        Returns:
            MerkleProof object containing the proof path
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise ValueError(f"Invalid leaf index: {leaf_index}")
        
        proof_path = []
        index = leaf_index
        
        for level in range(len(self.tree) - 1):
            current_level = self.tree[level]
            sibling_index = index + 1 if index % 2 == 0 else index - 1
            
            if sibling_index < len(current_level):
                sibling_hash = current_level[sibling_index]
                position = 'left' if index % 2 == 1 else 'right'
                proof_path.append((sibling_hash, position))
            
            index = index // 2
        
        return MerkleProof(
            leaf_hash=self.leaves[leaf_index],
            root_hash=self.get_root(),
            proof=proof_path,
            leaf_index=leaf_index
        )
    
    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            proof: MerkleProof object
        
        Returns:
            True if the proof is valid
        """
        current_hash = proof.leaf_hash
        
        for sibling_hash, position in proof.proof:
            if position == 'left':
                current_hash = MerkleTree._hash_pair(sibling_hash, current_hash)
            else:
                current_hash = MerkleTree._hash_pair(current_hash, sibling_hash)
        
        return current_hash == proof.root_hash
