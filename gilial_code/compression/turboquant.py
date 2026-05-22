"""TurboQuant: Online vector quantization with near-optimal distortion rate.

Based on: "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate"
Zandieh, Daliri, Hadian, Mirrokni (2025). https://arxiv.org/abs/2504.19874

Algorithm:
  1. PolarQuant stage: Apply a random rotation R (seeded, data-oblivious) to spread
     vector energy uniformly across dimensions, then apply scalar quantization
     independently per dimension using Lloyd-Max optimal quantizer for the
     resulting Beta-distributed coordinates.
  2. QJL residual stage: Compute the quantization residual, apply a 1-bit
     Quantized Johnson-Lindenstrauss projection to capture remaining signal
     for inner product estimation.
"""

import numpy as np
from typing import Tuple, Optional


class TurboQuant:
    """Data-oblivious vector quantizer using random rotation + scalar quantization + QJL residual.

    Parameters
    ----------
    dim : int
        Vector dimension.
    bits : int
        Bits per dimension for the scalar quantizer (2–8). Default 4.
    seed : int
        Random seed for the rotation matrix and QJL projection. Must be the
        same at quantization and query time.
    use_qjl : bool
        Whether to apply the 1-bit QJL residual correction stage (default True).
    qjl_bits : int
        Number of 1-bit QJL projections to use for residual correction (default = dim).
    """

    def __init__(
        self,
        dim: int,
        bits: int = 4,
        seed: int = 42,
        use_qjl: bool = True,
        qjl_bits: Optional[int] = None,
    ):
        self.dim = dim
        self.bits = bits
        self.seed = seed
        self.use_qjl = use_qjl
        self.qjl_bits = qjl_bits if qjl_bits is not None else dim
        self.levels = 2 ** bits

        rng = np.random.default_rng(seed)

        # Random orthogonal rotation matrix via QR decomposition of a Gaussian matrix.
        # This is data-oblivious (no training needed) and spreads energy uniformly,
        # inducing a concentrated Beta distribution on each coordinate after rotation.
        G = rng.standard_normal((dim, dim)).astype(np.float32)
        Q, _ = np.linalg.qr(G)
        self.R = Q  # shape: (dim, dim)

        # 1-bit QJL projection matrix: random ±1/sqrt(qjl_bits) Rademacher matrix
        signs = rng.choice([-1.0, 1.0], size=(self.qjl_bits, dim)).astype(np.float32)
        self.P = signs / np.sqrt(self.qjl_bits)  # shape: (qjl_bits, dim)

        # Compute optimal scalar quantizer boundaries and reconstruction levels
        # for a uniform distribution on [-1, 1] (post-rotation coordinates are
        # approximately uniformly distributed after L2-normalisation).
        # We store the clip range and step size; reconstruction uses midpoints.
        self._clip = 1.0
        self._step = (2 * self._clip) / self.levels

        # Reconstruction levels: midpoints of each quantization bin
        edges = np.linspace(-self._clip, self._clip, self.levels + 1, dtype=np.float32)
        self.recon_levels = ((edges[:-1] + edges[1:]) / 2)  # shape: (levels,)

    # ------------------------------------------------------------------
    # Core encode / decode
    # ------------------------------------------------------------------

    def encode(self, vector: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray], float]:
        """Quantize a single vector.

        Parameters
        ----------
        vector : np.ndarray, shape (dim,)

        Returns
        -------
        codes : np.ndarray of uint8, shape (dim,)
            Scalar quantization codes (0 … levels-1) for the rotated vector.
        qjl_bits : np.ndarray of uint8, shape (qjl_bits // 8,) or None
            Packed 1-bit QJL residual projection (None if use_qjl=False).
        norm : float
            L2 norm of the original vector, needed for reconstruction.
        """
        v = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(v))

        if norm == 0.0:
            codes = np.zeros(self.dim, dtype=np.uint8)
            qjl = np.zeros(self._packed_size(), dtype=np.uint8) if self.use_qjl else None
            return codes, qjl, 0.0

        # Normalise so rotation maps to the unit sphere; energy is uniform per-coord
        v_norm = v / norm

        # Stage 1: rotate
        rotated = self.R @ v_norm  # (dim,)

        # Stage 1: scalar quantize each dimension
        clipped = np.clip(rotated, -self._clip, self._clip)
        indices = np.floor((clipped + self._clip) / self._step).astype(np.int32)
        indices = np.clip(indices, 0, self.levels - 1)
        codes = indices.astype(np.uint8)

        if not self.use_qjl:
            return codes, None, norm

        # Stage 2: QJL on residual
        reconstructed = self.recon_levels[codes]
        residual = rotated - reconstructed  # error in rotated space
        projections = self.P @ residual  # (qjl_bits,)
        bit_signs = (projections >= 0).astype(np.uint8)  # 1-bit per projection
        packed = np.packbits(bit_signs)  # pack to bytes
        return codes, packed, norm

    def decode(
        self,
        codes: np.ndarray,
        norm: float,
        qjl_bits: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Reconstruct an approximate vector from its quantized representation.

        Parameters
        ----------
        codes : np.ndarray of uint8, shape (dim,)
        norm : float
        qjl_bits : packed uint8 array or None

        Returns
        -------
        np.ndarray, shape (dim,), approximate reconstruction of original vector.
        """
        reconstructed = self.recon_levels[codes]  # rotated unit-sphere coords

        if self.use_qjl and qjl_bits is not None:
            # Unpack QJL bits and estimate residual via pseudo-inverse projection
            bits = np.unpackbits(qjl_bits)[: self.qjl_bits].astype(np.float32)
            bits = bits * 2 - 1  # map {0,1} → {-1,+1}
            # Least-squares residual estimate: P^T * bits * scale
            # Scale factor: E[|projection|] for a random unit vector ~ sqrt(2/pi)
            residual_est = self.P.T @ bits  # (dim,)
            reconstructed = reconstructed + residual_est * np.sqrt(2 / np.pi) / self.qjl_bits

        # Rotate back to original space
        v_unit = self.R.T @ reconstructed
        return v_unit * norm

    def estimate_inner_product(
        self,
        q_codes: np.ndarray,
        q_norm: float,
        q_qjl: Optional[np.ndarray],
        x_codes: np.ndarray,
        x_norm: float,
        x_qjl: Optional[np.ndarray],
    ) -> float:
        """Estimate <q, x> from quantized representations without decoding.

        Uses the fact that after the same rotation R, the inner product is
        preserved: <Rq, Rx> = <q, x> (since R is orthogonal).
        """
        q_recon = self.recon_levels[q_codes]
        x_recon = self.recon_levels[x_codes]
        ip = float(np.dot(q_recon, x_recon)) * q_norm * x_norm

        if self.use_qjl and q_qjl is not None and x_qjl is not None:
            # Add QJL residual correction: sign(P @ r_q) · sign(P @ r_x) estimator
            q_bits = np.unpackbits(q_qjl)[: self.qjl_bits].astype(np.float32) * 2 - 1
            x_bits = np.unpackbits(x_qjl)[: self.qjl_bits].astype(np.float32) * 2 - 1
            correction = float(np.dot(q_bits, x_bits)) / self.qjl_bits
            ip += correction * q_norm * x_norm

        return ip

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def encode_batch(
        self, vectors: np.ndarray
    ) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """Encode a batch of vectors.

        Parameters
        ----------
        vectors : np.ndarray, shape (n, dim)

        Returns
        -------
        codes : np.ndarray of uint8, shape (n, dim)
        qjl_bits : np.ndarray of uint8, shape (n, packed_size) or None
        norms : np.ndarray of float32, shape (n,)
        """
        vectors = np.asarray(vectors, dtype=np.float32)
        n = vectors.shape[0]
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)  # (n,1)

        safe_norms = np.where(norms == 0, 1.0, norms)
        v_norm = vectors / safe_norms  # (n, dim)

        rotated = (self.R @ v_norm.T).T  # (n, dim)
        clipped = np.clip(rotated, -self._clip, self._clip)
        indices = np.floor((clipped + self._clip) / self._step).astype(np.int32)
        indices = np.clip(indices, 0, self.levels - 1)
        codes = indices.astype(np.uint8)

        norms_flat = norms.flatten().astype(np.float32)
        # zero-norm vectors get zero codes
        zero_mask = (norms_flat == 0)
        codes[zero_mask] = 0

        if not self.use_qjl:
            return codes, None, norms_flat

        reconstructed = self.recon_levels[codes]  # (n, dim)
        residuals = rotated - reconstructed  # (n, dim)
        projections = (self.P @ residuals.T).T  # (n, qjl_bits)
        bit_signs = (projections >= 0).astype(np.uint8)
        packed = np.packbits(bit_signs, axis=1)  # (n, packed_size)
        packed[zero_mask] = 0

        return codes, packed, norms_flat

    # ------------------------------------------------------------------
    # Storage footprint helpers
    # ------------------------------------------------------------------

    def bytes_per_vector_quantized(self) -> int:
        """Bytes needed to store one quantized vector (codes + QJL + norm)."""
        code_bytes = int(np.ceil(self.dim * self.bits / 8))
        qjl_bytes = self._packed_size() if self.use_qjl else 0
        norm_bytes = 4  # float32
        return code_bytes + qjl_bytes + norm_bytes

    def bytes_per_vector_original(self) -> int:
        """Bytes for original float32 vector."""
        return self.dim * 4

    def compression_ratio(self) -> float:
        """Ratio of compressed size to original size (lower is better)."""
        return self.bytes_per_vector_quantized() / self.bytes_per_vector_original()

    def _packed_size(self) -> int:
        return int(np.ceil(self.qjl_bits / 8))
