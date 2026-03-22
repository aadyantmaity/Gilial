from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from scipy.spatial import ConvexHull

from gilial.core.schema import Memory


@dataclass
class CoverageSnapshot:
    memory_count: int
    embedding_dim: int
    pca_variance_explained: float
    coverage_area: float


@dataclass
class CoverageReport:
    retention_ratio: float
    threshold: float
    passed: bool


class SemanticCoverageChecker:
    def measure(self, memories: list[Memory]) -> CoverageSnapshot:
        if len(memories) < 3:
            return CoverageSnapshot(
                memory_count=len(memories),
                embedding_dim=len(memories[0].embedding) if memories else 0,
                pca_variance_explained=0.0,
                coverage_area=0.0,
            )

        embeddings = np.array([m.embedding for m in memories])
        embedding_dim = embeddings.shape[1]

        pca = PCA(n_components=2)
        points_2d = pca.fit_transform(embeddings)
        variance_explained = float(sum(pca.explained_variance_ratio_))

        try:
            hull = ConvexHull(points_2d)
            area = float(hull.volume)  # in 2D, volume == area
        except Exception:
            area = 0.0

        return CoverageSnapshot(
            memory_count=len(memories),
            embedding_dim=embedding_dim,
            pca_variance_explained=variance_explained,
            coverage_area=area,
        )

    def compare(
        self,
        before: CoverageSnapshot,
        after: CoverageSnapshot,
        threshold: float = 0.7,
    ) -> CoverageReport:
        if before.coverage_area == 0.0:
            retention_ratio = 1.0
        else:
            retention_ratio = after.coverage_area / before.coverage_area
        return CoverageReport(
            retention_ratio=retention_ratio,
            threshold=threshold,
            passed=retention_ratio >= threshold,
        )
