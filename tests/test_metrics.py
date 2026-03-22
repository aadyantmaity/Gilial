from gilial.metrics import compute_ndcg, compute_mrr


class TestComputeNDCG:
    def test_perfect_match(self):
        relevant = ["a", "b", "c"]
        retrieved = ["a", "b", "c"]
        assert compute_ndcg(relevant, retrieved, k=3) == 1.0

    def test_no_overlap(self):
        relevant = ["a", "b", "c"]
        retrieved = ["x", "y", "z"]
        assert compute_ndcg(relevant, retrieved, k=3) == 0.0

    def test_partial_overlap(self):
        relevant = ["a", "b", "c"]
        retrieved = ["a", "x", "b", "y", "z"]
        score = compute_ndcg(relevant, retrieved, k=5)
        assert 0.0 < score < 1.0


class TestComputeMRR:
    def test_first_is_relevant(self):
        assert compute_mrr(["a", "b"], ["a", "x", "y"]) == 1.0

    def test_second_is_relevant(self):
        assert compute_mrr(["a"], ["x", "a", "y"]) == 0.5

    def test_none_relevant(self):
        assert compute_mrr(["a"], ["x", "y", "z"]) == 0.0
