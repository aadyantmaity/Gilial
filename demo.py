"""
Demo for the Agent Memory Compression System - All Phases
"""
from gilial.writer import MemoryWriter
from gilial.eval.canary import CanarySet
from gilial.scoring.regression import RetrievalRegressionTest, save_snapshot, load_snapshot
from gilial.eval.coverage import SemanticCoverageChecker
from gilial.eval.audit import CompressionAudit
from gilial.eval.evaluator import CompressionEvaluator
from gilial.tuning.tuner import CompressionTuner, TuneConfig

SEP = "─" * 68

def section(title):
    print(f"\n── {title} {'─' * max(0, 65 - len(title))}")

def main():
    print("Initializing MemoryWriter...")
    writer = MemoryWriter()

    # ── Phase 1: Store & Retrieve ─────────────────────────────────────
    section("Phase 1: Store & Retrieve")
    raw_memories = [
        ("The capital of France is Paris", ["geography", "europe"]),
        ("Python was created by Guido van Rossum in 1991", ["programming", "history"]),
        ("Photosynthesis converts light energy into chemical energy", ["biology", "science"]),
        ("The Eiffel Tower is located in Paris, France", ["geography", "landmarks"]),
        ("Machine learning is a subset of artificial intelligence", ["ai", "technology"]),
        ("The Amazon river is the largest river by discharge volume", ["geography"]),
        ("Rust guarantees memory safety without a garbage collector", ["programming"]),
        ("DNA carries genetic instructions for all known organisms", ["biology", "science"]),
        ("Paris hosted the 1900 and 1924 Summer Olympics", ["geography", "history"]),
        ("Neural networks are inspired by the human brain", ["ai", "technology"]),
    ]
    stored = []
    for content, tags in raw_memories:
        m = writer.store(content, tags=tags)
        stored.append(m)
        print(f"  Stored [{m.id[:8]}]: {content[:60]}")

    print("\nRetrieve — 'European capitals and landmarks':")
    for memory, dist in writer.retrieve("European capitals and landmarks", n_results=3):
        print(f"  dist={dist:.4f} | {memory.content}")

    print("\nRetrieve — 'artificial intelligence and coding':")
    for memory, dist in writer.retrieve("artificial intelligence and coding", n_results=3):
        print(f"  dist={dist:.4f} | {memory.content}")

    # build up access counts for scoring
    for _ in range(2):
        writer.retrieve("European capitals and landmarks", n_results=3)

    # ── Phase 2: Importance Scoring ───────────────────────────────────
    section("Phase 2: Importance Scoring")
    print("  recency 25% | access freq 30% | retrieval rank 20% | uniqueness 25%\n")
    scores = writer.rescore_all()
    ranked = sorted(writer.db.get_all(), key=lambda m: scores[m.id], reverse=True)
    for m in ranked:
        score = scores[m.id]
        bar = "█" * int(score * 20)
        print(f"  {score:.3f} {bar:<20} acc={m.access_count} | {m.content[:55]}")
    print(f"\n  Most important : {ranked[0].content}")
    print(f"  Least important: {ranked[-1].content}")

    # ── Phase 3a: Deletion (dry run) ──────────────────────────────────
    section("Phase 3a: Deletion (dry run)")
    del_result = writer.compress_delete(score_floor=0.2, protect_top_pct=0.2, dry_run=True)
    print(del_result.summary())

    # ── Phase 3b: Merging (dry run) ───────────────────────────────────
    section("Phase 3b: Merging (dry run)")
    merge_result = writer.compress_merge(similarity_threshold=0.92, dry_run=True)
    print(f"  Merge groups found : {len(merge_result.merge_groups)}")
    for g in merge_result.merge_groups:
        print(f"    group: {[m.content[:40] for m in g.members]}")
    if not merge_result.merge_groups:
        print("  (no near-duplicate pairs found above threshold)")

    # ── Phase 3c: Summarization (dry run) ─────────────────────────────
    section("Phase 3c: Summarization (dry run)")
    sum_result = writer.compress_summarize(low_threshold=0.75, high_threshold=0.92, dry_run=True)
    print(f"  Summary groups found: {len(sum_result.summary_groups)}")
    for g in sum_result.summary_groups:
        print(f"    group ({len(g.members)} members): {[m.content[:35] for m in g.members]}")
    if not sum_result.summary_groups:
        print("  (no related clusters found in similarity range)")

    # ── Phase 4: Scheduler (single manual run, dry run) ───────────────
    section("Phase 4: Compression Scheduler")
    scheduler = writer.get_scheduler(size_threshold=5, dry_run=True)
    result = scheduler.run_now(reason="demo")
    print(f"  Trigger         : {result['trigger']}")
    print(f"  Memories before : {result['memories_before']}")
    print(f"  Memories after  : {result['memories_after']}")
    print(f"  Deleted         : {result['deleted']}")
    print(f"  Merged          : {result['merged']}")
    print(f"  Summarized      : {result['summarized']}")
    print(f"  Dry run         : {result['dry_run']}")
    status = scheduler.status()
    print(f"  Snapshots saved : {status['snapshots_available']}")

    # ── Phase 5a: Canary memories ─────────────────────────────────────
    section("Phase 5a: Canary Memories")
    canaries = CanarySet()
    canary_ids = canaries.inject(writer, [
        {"content": "User's name is Aadyant", "tags": ["user-fact"]},
        {"content": "User's long-term goal is to build an autonomous agent", "tags": ["user-goal"]},
    ])
    print(f"  Injected {len(canary_ids)} canary memories")
    verify = canaries.verify(writer)
    print(f"  Survival rate   : {verify.survival_rate:.0%}")
    print(f"  Passed          : {verify.passed}")

    # ── Phase 5b: Retrieval Regression ────────────────────────────────
    section("Phase 5b: Retrieval Regression Test")
    rrt = RetrievalRegressionTest()
    queries = ["geography", "programming", "biology"]
    snap = rrt.snapshot(writer, queries=queries, k=3)
    print(f"  Snapshot taken for {len(queries)} queries")
    report = rrt.compare(writer, snap, k=3)
    print(f"  Mean Jaccard    : {report.mean_score:.3f}")
    print(f"  Passed          : {report.passed}")
    for q, score in report.per_query.items():
        print(f"    [{q}] Jaccard={score:.3f}")

    # ── Phase 5c: Semantic Coverage ───────────────────────────────────
    section("Phase 5c: Semantic Coverage")
    checker = SemanticCoverageChecker()
    all_mems = writer.db.get_all()
    before_snap = checker.measure(all_mems)
    print(f"  Memory count         : {before_snap.memory_count}")
    print(f"  Coverage area (2D)   : {before_snap.coverage_area:.6f}")
    print(f"  PCA variance expl.   : {before_snap.pca_variance_explained:.3f}")
    cov_report = checker.compare(before_snap, before_snap)
    print(f"  Retention ratio      : {cov_report.retention_ratio:.3f}")
    print(f"  Passed               : {cov_report.passed}")

    # ── Phase 5d: Audit Diff ──────────────────────────────────────────
    section("Phase 5d: Compression Audit Diff")
    before_ids = [m.id for m in writer.db.get_all()]
    # simulate: delete the least important memory
    least = ranked[-1]
    writer.db.delete(least.id)
    after_ids = [m.id for m in writer.db.get_all()]
    audit = CompressionAudit()
    diff = audit.diff(before_ids, after_ids, writer)
    print(audit.format_diff(diff))

    # restore for evaluation
    writer.store(least.content, tags=least.tags, importance_score=least.importance_score)

    # ── Phase 6: Evaluation & Tuning ──────────────────────────────────
    section("Phase 6a: Compression Evaluator")
    eval_queries = [
        {"query": "geography", "relevant_ids": [m.id for m in writer.db.get_all() if "geography" in m.tags]},
        {"query": "programming", "relevant_ids": [m.id for m in writer.db.get_all() if "programming" in m.tags]},
    ]
    evaluator = CompressionEvaluator(writer, canary_set=canaries, eval_queries=eval_queries)
    report = evaluator.run(dry_run=True)
    print(f"  NDCG             : {report.retrieval.ndcg:.3f}")
    print(f"  MRR              : {report.retrieval.mrr:.3f}")
    print(f"  Storage reduction: {report.storage.reduction_ratio:.3f}")
    print(f"  False del. rate  : {report.false_deletion.false_deletion_rate:.3f}")
    print(f"  Coverage retained: {report.coverage_retention:.3f}")
    print(f"  Passed           : {report.passed}")

    section("Phase 6b: Compression Tuner")
    tuner = CompressionTuner()
    tuner.add_config("conservative", TuneConfig(score_floor=0.1, protect_top_pct=0.3))
    tuner.add_config("balanced",     TuneConfig(score_floor=0.2, protect_top_pct=0.2))
    tuner.add_config("aggressive",   TuneConfig(score_floor=0.35, protect_top_pct=0.1))
    results = tuner.run_all(writer, dry_run=True)
    print(tuner.summary_table(results))
    winner = tuner.best(results, prefer="balanced")
    print(f"  Best (balanced)  : {winner.label}")

    print(f"\n{SEP}")
    print("All phases complete. Logs written to compression_log.jsonl")

if __name__ == "__main__":
    main()
