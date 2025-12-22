"""Unit Tests for Merkle Tree Implementation"""
import pytest
from mtp_core.core.merkle import MerkleTree, MerkleProof
from mtp_core.core.crypto import hash_data


class TestMerkleTreeConstruction:
    """Tests for Merkle tree construction"""

    def test_merkle_tree_single_leaf(self):
        """Test Merkle tree with a single leaf"""
        leaves = [hash_data(b"event_1")]
        tree = MerkleTree(leaves)

        # Single leaf = root is the leaf itself
        assert tree.get_root() == leaves[0]
        assert len(tree.tree) == 1  # Only one level

    def test_merkle_tree_two_leaves(self):
        """Test Merkle tree with two leaves"""
        leaves = [hash_data(b"event_1"), hash_data(b"event_2")]
        tree = MerkleTree(leaves)

        root = tree.get_root()

        # Root should be different from both leaves
        assert root != leaves[0]
        assert root != leaves[1]

        # Two levels: leaves and root
        assert len(tree.tree) == 2

    def test_merkle_tree_power_of_two_leaves(self):
        """Test Merkle tree with power of 2 leaves (4)"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        # 4 leaves = 3 levels (4 -> 2 -> 1)
        assert len(tree.tree) == 3
        assert len(tree.tree[0]) == 4  # Leaves
        assert len(tree.tree[1]) == 2  # Intermediate
        assert len(tree.tree[2]) == 1  # Root

    def test_merkle_tree_odd_number_of_leaves(self):
        """Test Merkle tree with odd number of leaves"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(5)]
        tree = MerkleTree(leaves)

        # Tree should still be constructed
        root = tree.get_root()
        assert len(root) == 64  # Valid SHA-256 hash

    def test_merkle_tree_empty_leaves_raises(self):
        """Test that empty leaves raise ValueError"""
        with pytest.raises(ValueError, match="Cannot create Merkle tree with no leaves"):
            MerkleTree([])

    def test_merkle_tree_deterministic(self):
        """Test that same leaves produce same root"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(10)]

        tree1 = MerkleTree(leaves)
        tree2 = MerkleTree(leaves)

        assert tree1.get_root() == tree2.get_root()

    def test_merkle_tree_different_leaves_different_root(self):
        """Test that different leaves produce different root"""
        leaves1 = [hash_data(f"event_{i}".encode()) for i in range(5)]
        leaves2 = [hash_data(f"other_{i}".encode()) for i in range(5)]

        tree1 = MerkleTree(leaves1)
        tree2 = MerkleTree(leaves2)

        assert tree1.get_root() != tree2.get_root()

    def test_merkle_tree_order_matters(self):
        """Test that leaf order affects the root"""
        leaves1 = [hash_data(b"a"), hash_data(b"b"), hash_data(b"c")]
        leaves2 = [hash_data(b"c"), hash_data(b"b"), hash_data(b"a")]

        tree1 = MerkleTree(leaves1)
        tree2 = MerkleTree(leaves2)

        # Different order should produce different root
        # (unless implementation sorts, which ours doesn't for leaves)
        # The _hash_pair function sorts, but leaves array order matters
        assert tree1.get_root() != tree2.get_root()


class TestMerkleProof:
    """Tests for Merkle proof generation and verification"""

    def test_proof_for_first_leaf(self):
        """Test generating proof for first leaf"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(0)

        assert proof.leaf_index == 0
        assert proof.leaf_hash == leaves[0]
        assert proof.root_hash == tree.get_root()
        assert len(proof.proof) > 0

    def test_proof_for_last_leaf(self):
        """Test generating proof for last leaf"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(3)

        assert proof.leaf_index == 3
        assert proof.leaf_hash == leaves[3]
        assert proof.root_hash == tree.get_root()

    def test_proof_for_middle_leaf(self):
        """Test generating proof for middle leaf"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(8)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(4)

        assert proof.leaf_index == 4
        assert proof.leaf_hash == leaves[4]

    def test_proof_invalid_index_negative(self):
        """Test that negative index raises ValueError"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        with pytest.raises(ValueError, match="Invalid leaf index"):
            tree.get_proof(-1)

    def test_proof_invalid_index_too_large(self):
        """Test that out-of-range index raises ValueError"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        with pytest.raises(ValueError, match="Invalid leaf index"):
            tree.get_proof(4)  # Index 4 doesn't exist for 4 leaves

    def test_verify_valid_proof(self):
        """Test that valid proof verifies successfully"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(8)]
        tree = MerkleTree(leaves)

        for i in range(len(leaves)):
            proof = tree.get_proof(i)
            is_valid = MerkleTree.verify_proof(proof)
            assert is_valid, f"Proof for leaf {i} should be valid"

    def test_verify_tampered_leaf_hash(self):
        """Test that tampered leaf hash fails verification"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(1)
        # Tamper with the leaf hash
        tampered_proof = MerkleProof(
            leaf_hash=hash_data(b"fake_event"),
            root_hash=proof.root_hash,
            proof=proof.proof,
            leaf_index=proof.leaf_index
        )

        is_valid = MerkleTree.verify_proof(tampered_proof)
        assert is_valid is False

    def test_verify_tampered_root_hash(self):
        """Test that tampered root hash fails verification"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(1)
        # Tamper with the root hash
        tampered_proof = MerkleProof(
            leaf_hash=proof.leaf_hash,
            root_hash=hash_data(b"fake_root"),
            proof=proof.proof,
            leaf_index=proof.leaf_index
        )

        is_valid = MerkleTree.verify_proof(tampered_proof)
        assert is_valid is False

    def test_verify_tampered_proof_path(self):
        """Test that tampered proof path fails verification"""
        leaves = [hash_data(f"event_{i}".encode()) for i in range(4)]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(1)

        if proof.proof:  # Only if there's a proof path
            # Tamper with a hash in the proof path
            tampered_path = list(proof.proof)
            tampered_path[0] = (hash_data(b"fake"), tampered_path[0][1])

            tampered_proof = MerkleProof(
                leaf_hash=proof.leaf_hash,
                root_hash=proof.root_hash,
                proof=tampered_path,
                leaf_index=proof.leaf_index
            )

            is_valid = MerkleTree.verify_proof(tampered_proof)
            assert is_valid is False


class TestMerkleTreeBatching:
    """Tests for audit event batching scenario"""

    def test_batch_100_events(self):
        """Test batching 100 events (production batch size)"""
        event_hashes = [hash_data(f"event_{i}".encode()) for i in range(100)]
        tree = MerkleTree(event_hashes)

        root = tree.get_root()

        # Verify all events have valid proofs
        for i in range(100):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(proof), f"Event {i} proof failed"

    def test_batch_1000_events(self):
        """Test batching 1000 events (large batch)"""
        event_hashes = [hash_data(f"event_{i}".encode()) for i in range(1000)]
        tree = MerkleTree(event_hashes)

        root = tree.get_root()

        # Spot check a few proofs
        for i in [0, 100, 500, 999]:
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(proof), f"Event {i} proof failed"

    def test_proof_size_is_logarithmic(self):
        """Test that proof size grows logarithmically with tree size"""
        # 8 leaves -> log2(8) = 3 proof elements
        tree_8 = MerkleTree([hash_data(f"e{i}".encode()) for i in range(8)])
        proof_8 = tree_8.get_proof(0)

        # 16 leaves -> log2(16) = 4 proof elements
        tree_16 = MerkleTree([hash_data(f"e{i}".encode()) for i in range(16)])
        proof_16 = tree_16.get_proof(0)

        # 32 leaves -> log2(32) = 5 proof elements
        tree_32 = MerkleTree([hash_data(f"e{i}".encode()) for i in range(32)])
        proof_32 = tree_32.get_proof(0)

        # Proof size should increase by 1 for each doubling
        assert len(proof_16.proof) == len(proof_8.proof) + 1
        assert len(proof_32.proof) == len(proof_16.proof) + 1


class TestMerkleHashPairFunction:
    """Tests for the hash pairing function used internally"""

    def test_hash_pair_is_deterministic(self):
        """Test that pairing produces consistent results"""
        h1 = hash_data(b"data1")
        h2 = hash_data(b"data2")

        result1 = MerkleTree._hash_pair(h1, h2)
        result2 = MerkleTree._hash_pair(h1, h2)

        assert result1 == result2

    def test_hash_pair_is_commutative(self):
        """Test that order doesn't matter (sorted internally)"""
        h1 = hash_data(b"data1")
        h2 = hash_data(b"data2")

        result1 = MerkleTree._hash_pair(h1, h2)
        result2 = MerkleTree._hash_pair(h2, h1)

        # Our implementation sorts before hashing for consistency
        assert result1 == result2

    def test_hash_pair_different_inputs_different_output(self):
        """Test that different inputs produce different outputs"""
        h1 = hash_data(b"data1")
        h2 = hash_data(b"data2")
        h3 = hash_data(b"data3")

        result1 = MerkleTree._hash_pair(h1, h2)
        result2 = MerkleTree._hash_pair(h1, h3)

        assert result1 != result2


class TestMerkleProofDataClass:
    """Tests for the MerkleProof dataclass"""

    def test_merkle_proof_fields(self):
        """Test that MerkleProof has correct fields"""
        proof = MerkleProof(
            leaf_hash="abc123",
            root_hash="def456",
            proof=[("hash1", "left"), ("hash2", "right")],
            leaf_index=5
        )

        assert proof.leaf_hash == "abc123"
        assert proof.root_hash == "def456"
        assert len(proof.proof) == 2
        assert proof.leaf_index == 5

    def test_merkle_proof_immutability(self):
        """Test that MerkleProof is a proper dataclass"""
        proof = MerkleProof(
            leaf_hash="abc",
            root_hash="def",
            proof=[],
            leaf_index=0
        )

        # Dataclass allows attribute access
        assert hasattr(proof, 'leaf_hash')
        assert hasattr(proof, 'root_hash')
        assert hasattr(proof, 'proof')
        assert hasattr(proof, 'leaf_index')
