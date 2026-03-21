"""
Demo for the Agent Memory Compression System - Phase 1 & 2
"""
from memcomp.writer import MemoryWriter

def main():
    print("Initializing MemoryWriter...")
    writer = MemoryWriter()

    # ── Phase 1: Store & Retrieve ─────────────────────────────────────────────
    print("\n── Phase 1: Storing memories ────────────────────────────────────────")
    memories = [
        ("The capital of France is Paris", ["geography", "europe"]),
        ("Python was created by Guido van Rossum in 1991", ["programming", "history"]),
        ("Photosynthesis converts light energy into chemical energy", ["biology", "science"]),
        ("The Eiffel Tower is located in Paris, France", ["geography", "landmarks"]),
        ("Machine learning is a subset of artificial intelligence", ["ai", "technology"]),
    ]
    stored = []
    for content, tags in memories:
        m = writer.store(content, tags=tags)
        stored.append(m)
        print(f"  Stored [{m.id[:8]}...]: {content[:50]}")

    print("\nRetrieving similar to 'European capitals and landmarks'...")
    results = writer.retrieve("European capitals and landmarks", n_results=3)
    for memory, distance in results:
        print(f"  dist={distance:.4f} | {memory.content}")

    print("\nRetrieving similar to 'artificial intelligence and coding'...")
    results = writer.retrieve("artificial intelligence and coding", n_results=3)
    for memory, distance in results:
        print(f"  dist={distance:.4f} | {memory.content}")

    # retrieve the same geography query again to build up access counts
    writer.retrieve("European capitals and landmarks", n_results=3)
    writer.retrieve("European capitals and landmarks", n_results=3)

    # ── Phase 2: Importance Scoring ───────────────────────────────────────────
    print("\n── Phase 2: Importance scores ───────────────────────────────────────")
    print("  (recency 25% | access freq 30% | retrieval rank 20% | uniqueness 25%)\n")

    scores = writer.rescore_all()
    all_memories = writer.db.get_all()

    # sort by importance descending
    ranked = sorted(all_memories, key=lambda m: scores[m.id], reverse=True)

    for m in ranked:
        score = scores[m.id]
        bar = "█" * int(score * 20)
        print(f"  {score:.3f} {bar:<20} | acc={m.access_count} | {m.content[:50]}")

    print(f"\n  Most important : {ranked[0].content}")
    print(f"  Least important: {ranked[-1].content}")
    print("\nDone! Telemetry written to telemetry.jsonl")

if __name__ == "__main__":
    main()
