"""
Benchmark script for the Smart Guided Troubleshooting Engine.

Measures latency, Laya calls, DB queries, and LLM calls
across three categories:
  A: Fast Path (clear, high-confidence queries)
  B: Diagnostic Path (ambiguous queries requiring follow-up)
  C: Multi-Issue (queries with 2+ detected issues)

Run with:
    cd backend
    python benchmark.py

Output: tabulated before/after metrics.
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(__file__))

# Force keyword fallback for deterministic benchmarking
os.environ["GEMINI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

from fastapi.testclient import TestClient
from main import app, aggregate_stats
from perf import RequestMetrics, _AggregateStats


# ── Benchmark categories ────────────────────────────────────

CATEGORY_A_QUERIES = [
    "My battery is draining very fast",
    "My phone has become very slow",
    "My screen keeps flickering",
    "My camera photos are blurry",
]

CATEGORY_B_QUERIES = [
    "My phone is overheating",
    "My phone behaves strangely",
    "My screen flickers only when brightness changes",
]

CATEGORY_C_QUERIES = [
    "My screen is flickering and my battery is draining very fast",
    "My phone is slow and the battery is also draining quickly",
]


def run_benchmark():
    """Run the full benchmark suite."""
    client = TestClient(app)
    results = {"A": [], "B": [], "C": []}

    print("\n" + "=" * 70)
    print("BENCHMARK: Smart Guided Troubleshooting Engine v4.1")
    print("=" * 70)

    # Category A: Fast Path
    print("\n── CATEGORY A: Fast Path (clear queries) ──")
    for query in CATEGORY_A_QUERIES:
        t0 = time.monotonic()
        resp = client.post("/v1/troubleshoot", json={"query": query})
        elapsed_ms = (time.monotonic() - t0) * 1000
        data = resp.json()
        results["A"].append({
            "query": query,
            "status": data["status"],
            "latency_ms": round(elapsed_ms, 1),
            "results_count": len(data.get("results", [])),
        })
        status_icon = "✓" if data["status"] == "success" else "?"
        print(f"  {status_icon} {elapsed_ms:7.1f}ms | {data['status']:10s} | {query}")

    # Category B: Diagnostic Path
    print("\n── CATEGORY B: Diagnostic Path (ambiguous queries) ──")
    for query in CATEGORY_B_QUERIES:
        t0 = time.monotonic()
        resp = client.post("/v1/troubleshoot", json={"query": query})
        elapsed_ms = (time.monotonic() - t0) * 1000
        data = resp.json()
        results["B"].append({
            "query": query,
            "status": data["status"],
            "latency_ms": round(elapsed_ms, 1),
            "session_id": data.get("session_id"),
        })
        status_icon = "→" if data["status"] == "follow_up" else "✓"
        print(f"  {status_icon} {elapsed_ms:7.1f}ms | {data['status']:10s} | {query}")

    # Category C: Multi-Issue
    print("\n── CATEGORY C: Multi-Issue ──")
    for query in CATEGORY_C_QUERIES:
        t0 = time.monotonic()
        resp = client.post("/v1/troubleshoot", json={"query": query})
        elapsed_ms = (time.monotonic() - t0) * 1000
        data = resp.json()
        results["C"].append({
            "query": query,
            "status": data["status"],
            "latency_ms": round(elapsed_ms, 1),
            "results_count": len(data.get("results", [])),
            "domains": [r["domain"] for r in data.get("results", [])],
        })
        status_icon = "✓" if data["status"] == "success" else "?"
        print(f"  {status_icon} {elapsed_ms:7.1f}ms | {data['status']:10s} | {len(data.get('results', []))} issues | {query}")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("AGGREGATE STATS")
    print("=" * 70)
    stats = aggregate_stats.summary()
    print(f"  Total requests:    {stats['total_requests']}")
    print(f"  Avg latency:       {stats['avg_latency_ms']:.1f} ms")
    print(f"  Total Laya calls:  {stats['total_laya_calls']}")
    print(f"  Total DB queries:  {stats['total_db_queries']}")
    print(f"  Total LLM calls:   {stats['total_llm_calls']}")
    print(f"  Path distribution: {json.dumps(stats['path_distribution'], indent=4)}")

    # ── Latency table ──
    all_latencies = []
    for cat in results.values():
        for entry in cat:
            all_latencies.append(entry["latency_ms"])
    all_latencies.sort()

    if all_latencies:
        p50_idx = max(0, int(len(all_latencies) * 0.5) - 1)
        p95_idx = max(0, int(len(all_latencies) * 0.95) - 1)
        print(f"\n  P50 latency:       {all_latencies[p50_idx]:.1f} ms")
        print(f"  P95 latency:       {all_latencies[p95_idx]:.1f} ms")
        print(f"  Min latency:       {min(all_latencies):.1f} ms")
        print(f"  Max latency:       {max(all_latencies):.1f} ms")

    # Category-specific averages
    for cat_name, cat_results in results.items():
        if cat_results:
            avg = sum(r["latency_ms"] for r in cat_results) / len(cat_results)
            print(f"  Cat {cat_name} avg:        {avg:.1f} ms")

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70 + "\n")

    return results, stats


if __name__ == "__main__":
    run_benchmark()
