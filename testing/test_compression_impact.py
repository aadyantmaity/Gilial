"""Test script comparing query results pre/post compression with visualization."""

import requests
import json
import os
import sys
import time

# Ensure repo root is on path so gilial_code is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any

BASE_URL = os.getenv("API_URL", "http://localhost:8000/api")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")




def test_compression_impact():
    """Test compression impact on query results."""

    if not PINECONE_API_KEY or not PINECONE_INDEX:
        print("Error: Set PINECONE_API_KEY and PINECONE_INDEX env vars")
        sys.exit(1)

    print(f"Testing compression impact on {PINECONE_INDEX}\n")

    # 1. Create connection
    print("1. Creating connection...")
    resp = requests.post(
        f"{BASE_URL}/connections",
        json={
            "api_key": PINECONE_API_KEY,
            "index_name": PINECONE_INDEX,
            "environment": "us-west",
        },
        timeout=10,
    )
    if resp.status_code != 201:
        print(f"   ERROR: {resp.status_code} - {resp.text}")
        sys.exit(1)

    conn_id = resp.json()["connection_id"]
    print(f"   ✓ Connection ID: {conn_id}\n")

    # 2. Get pre-compression status
    print("2. Getting pre-compression index status...")
    resp = requests.get(f"{BASE_URL}/connections/{conn_id}/status", timeout=10)
    if resp.status_code != 200:
        print(f"   ERROR: {resp.status_code}")
        sys.exit(1)

    status_pre = resp.json()
    print(f"   Index: {status_pre.get('index_name')}")
    print(f"   Vectors: {status_pre.get('total_vector_count')}")
    print(f"   Dimension: {status_pre.get('dimension')}\n")

    dimension = status_pre.get('dimension', 384)
    original_vectors = status_pre.get('total_vector_count', 0)

    if original_vectors == 0:
        print("   ERROR: No vectors in index")
        sys.exit(1)

    # 3. Record pre-compression stats
    print("4. Recording pre-compression metrics...")
    pre_compression_stats = {
        "vector_count": original_vectors,
        "search_space_mb": status_pre.get('total_vector_count', 0) * dimension * 4 / (1024 * 1024),
        "timestamp": time.time(),
    }
    print(f"   Vectors: {pre_compression_stats['vector_count']}")
    print(f"   Search space: {pre_compression_stats['search_space_mb']:.2f} MB\n")

    # 5. Run compression (ACTUAL - not dry run)
    print("5. Running actual compression...")
    start_time = time.time()
    resp = requests.post(
        f"{BASE_URL}/connections/{conn_id}/compress",
        json={"strategy": "balanced", "dry_run": False},
        timeout=60,
    )
    compression_time = time.time() - start_time

    if resp.status_code != 200:
        print(f"   ERROR: {resp.status_code} - {resp.text}")
        sys.exit(1)

    compression_result = resp.json()
    compressed_vectors = compression_result.get("compressed_vectors", 0)
    compression_ratio = compression_result.get("compression_ratio", 0)
    savings_pct = compression_result.get("savings_pct", 0)

    print(f"   Strategy: {compression_result.get('strategy')}")
    print(f"   Original vectors: {compression_result.get('original_vectors')}")
    print(f"   Compressed vectors: {compressed_vectors}")
    print(f"   Compression ratio: {compression_ratio:.2f}x")
    print(f"   Savings: {savings_pct:.2f}%")
    print(f"   Compression time: {compression_time:.2f}s\n")

    # 6. Get post-compression status
    print("6. Getting post-compression index status...")
    resp = requests.get(f"{BASE_URL}/connections/{conn_id}/status", timeout=10)
    if resp.status_code != 200:
        print(f"   ERROR: {resp.status_code}")
        sys.exit(1)

    status_post = resp.json()
    post_compression_stats = {
        "vector_count": status_post.get('total_vector_count', 0),
        "search_space_mb": status_post.get('total_vector_count', 0) * dimension * 4 / (1024 * 1024),
        "timestamp": time.time(),
    }
    print(f"   Vectors: {post_compression_stats['vector_count']}")
    print(f"   Search space: {post_compression_stats['search_space_mb']:.2f} MB\n")

    print(f"   Pre-compression:")
    print(f"     Vectors: {pre_compression_stats['vector_count']}")
    print(f"     Search space: {pre_compression_stats['search_space_mb']:.2f} MB")
    print(f"\n   Post-compression:")
    print(f"     Vectors: {post_compression_stats['vector_count']}")
    print(f"     Search space: {post_compression_stats['search_space_mb']:.2f} MB\n")

    # 7. Create visualizations
    print("7. Creating visualizations...\n")

    # Compute actual local memory sizes using TurboQuant footprint helpers
    from gilial_code.compression.turboquant import TurboQuant
    tq_balanced = TurboQuant(dim=dimension, bits=4, use_qjl=True)
    original_mb = original_vectors * tq_balanced.bytes_per_vector_original() / (1024 * 1024)
    compressed_mb = original_vectors * tq_balanced.bytes_per_vector_quantized() / (1024 * 1024)
    actual_savings_pct = (1 - tq_balanced.compression_ratio()) * 100

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        f"Compression Impact Analysis - {PINECONE_INDEX}",
        fontsize=16,
        fontweight="bold",
    )

    colors = ["#3498db", "#e74c3c"]
    states = ["Original\n(float32)", "Compressed\n(TurboQuant 4-bit)"]

    # Plot 1: Memory footprint
    ax = axes[0]
    spaces = [original_mb, compressed_mb]
    bars = ax.bar(states, spaces, color=colors, alpha=0.7, edgecolor="black", linewidth=2)
    ax.set_ylabel("Memory (MB)", fontsize=11, fontweight="bold")
    ax.set_title("Local Memory Footprint", fontsize=12, fontweight="bold")
    ax.set_ylim(0, original_mb * 1.2)
    for bar, val in zip(bars, spaces):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val:.2f} MB",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    # Plot 2: Bytes per vector
    ax = axes[1]
    bpv = [tq_balanced.bytes_per_vector_original(), tq_balanced.bytes_per_vector_quantized()]
    bars = ax.bar(states, bpv, color=colors, alpha=0.7, edgecolor="black", linewidth=2)
    ax.set_ylabel("Bytes / Vector", fontsize=11, fontweight="bold")
    ax.set_title("Storage per Vector", fontsize=12, fontweight="bold")
    ax.set_ylim(0, max(bpv) * 1.2)
    for bar, val in zip(bars, bpv):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val} B",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    # Plot 3: Summary Metrics
    ax = axes[2]
    ax.axis("off")

    summary_text = f"""
TURBOQUANT COMPRESSION SUMMARY
{'─' * 50}

Index Name:           {PINECONE_INDEX}
Vector Dimension:     {dimension}
Algorithm:            TurboQuant (4-bit + QJL)

Vectors:              {original_vectors:,}
Original size:        {original_mb:.2f} MB
Compressed size:      {compressed_mb:.2f} MB

Compression Ratio:    {1/tq_balanced.compression_ratio():.2f}x
Space Savings:        {actual_savings_pct:.1f}%

Strategy:             Balanced
Compression Time:     {compression_time:.2f}s
    """

    ax.text(
        0.05,
        0.95,
        summary_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig("compression_impact_analysis.png", dpi=300, bbox_inches="tight")
    print("   ✓ Saved: compression_impact_analysis.png")

    # Create a second figure: TurboQuant strategy comparison
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    fig2.suptitle("TurboQuant Strategy Comparison", fontsize=16, fontweight="bold")

    strategies = ["High Quality\n(6-bit)", "Balanced\n(4-bit)", "Aggressive\n(2-bit)"]
    bits_list = [6, 4, 2]
    colors_strat = ["#2ecc71", "#3498db", "#e74c3c"]

    savings_pcts = []
    ratios = []
    for b in bits_list:
        tq = TurboQuant(dim=dimension, bits=b, use_qjl=True)
        savings_pcts.append((1 - tq.compression_ratio()) * 100)
        ratios.append(1 / tq.compression_ratio())

    x = np.arange(len(strategies))

    # Plot 1: Savings %
    ax = axes2[0]
    bars = ax.bar(x, savings_pcts, color=colors_strat, alpha=0.8, edgecolor="black", linewidth=1.5)
    ax.set_ylabel("Storage Savings (%)", fontsize=11, fontweight="bold")
    ax.set_title("Storage Savings by Strategy", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(strategies)
    ax.set_ylim(0, 100)
    for bar, val in zip(bars, savings_pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val:.1f}%",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    # Plot 2: Compression ratio (Xx)
    ax = axes2[1]
    bars = ax.bar(x, ratios, color=colors_strat, alpha=0.8, edgecolor="black", linewidth=1.5)
    ax.set_ylabel("Compression Ratio (x)", fontsize=11, fontweight="bold")
    ax.set_title("Compression Ratio by Strategy", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(strategies)
    ax.set_ylim(0, max(ratios) * 1.2)
    for bar, val in zip(bars, ratios):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val:.1f}x",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig("strategy_comparison.png", dpi=300, bbox_inches="tight")
    print("   ✓ Saved: strategy_comparison.png")

    print("\n✓ Analysis complete!")
    print("\nGenerated plots:")
    print("  - compression_impact_analysis.png")
    print("  - strategy_comparison.png")


if __name__ == "__main__":
    test_compression_impact()
