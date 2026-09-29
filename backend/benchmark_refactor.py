"""
Before/After Performance Benchmark for the Diagnostic Engine Refactor.

Measures:
- Latency (total_ms, fast_gate_ms, llm_ms, laya_ms, kb_ms)
- Call counts (llm_calls, laya_calls, kb_queries)

For each scenario:
- Clear query (fast path)
- Ambiguous query (follow-up)
- Multi-issue query
- LLM fallback (unusual query)
- No-match (unsupported)

Run with:
    cd backend
    python benchmark_refactor.py
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(__file__))

# Force no LLM API keys so tests use keyword fallback
os.environ["GEMINI_API_KEY"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""

import logging
logging.getLogger("troubleshoot_engine").setLevel(logging.WARNING)

from fastapi.testclient import TestClient
from main import app
from perf import aggregate_stats, _AggregateStats, RequestMetrics

# Reset aggregate stats
aggregate_stats._request_count = 0
aggregate_stats._total_ms = 0.0
aggregate_stats._path_counts = {}
aggregate_stats._laya_calls = 0
aggregate_stats._db_queries = 0
aggregate_stats._llm_calls = 0


def benchmark_query(client, query, warmup=2, iterations=10):
    """Benchmark a single query and return metrics."""
    # Warmup
    for _ in range(warmup):
        client.post("/v1/troubleshoot", json={"query": query})

    latencies = []
    statuses = []
    paths = []

    for _ in range(iterations):
        # Reset aggregate stats to capture per-request counts
        before_llm = aggregate_stats._llm_calls
        before_laya = aggregate_stats._laya_calls
        before_db = aggregate_stats._db_queries

        start = time.monotonic()
        response = client.post("/v1/troubleshoot", json={"query": query})
        elapsed_ms = (time.monotonic() - start) * 1000

        data = response.json()
        latencies.append(elapsed_ms)
        statuses.append(data.get("status", "error"))

        # Get path from perf endpoint
        perf = client.get("/v1/perf").json()
        paths.append(perf.get("path_distribution", {}))

    latencies.sort()
    return {
        "query": query,
        "status": statuses[-1],
        "iterations": iterations,
        "avg_ms": round(sum(latencies) / len(latencies), 2),
        "p50_ms": round(latencies[len(latencies) // 2], 2),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)], 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "llm_calls_per_req": round((aggregate_stats._llm_calls - 0) / (iterations + warmup), 2),
        "laya_calls_per_req": round((aggregate_stats._laya_calls - 0) / (iterations + warmup), 2),
        "db_queries_per_req": round((aggregate_stats._db_queries - 0) / (iterations + warmup), 2),
    }


def main():
    client = TestClient(app)

    scenarios = [
        ("Clear query (battery drain)", "My battery is draining very fast"),
        ("Clear query (screen flicker)", "My screen keeps flickering"),
        ("Clear query (slow phone)", "My phone has become very slow"),
        ("Clear query (camera blur)", "My camera photos are blurry"),
        ("Ambiguous (overheating)", "My phone is overheating"),
        ("Ambiguous (battery problem)", "I have a battery problem"),
        ("Multi-issue", "My screen is flickering and my battery is draining very fast"),
        ("Vague (acting weird)", "My phone is acting weird"),
        ("No-match (smell)", "My phone smells strange"),
        ("Detailed (after update)", "My battery started draining quickly after the latest update"),
    ]

    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARK — Question-First Diagnostic Engine v5.0")
    print("=" * 80)

    results = []
    for name, query in scenarios:
        # Reset aggregate stats for each scenario
        aggregate_stats._request_count = 0
        aggregate_stats._total_ms = 0.0
        aggregate_stats._path_counts = {}
        aggregate_stats._laya_calls = 0
        aggregate_stats._db_queries = 0
        aggregate_stats._llm_calls = 0

        result = benchmark_query(client, query, warmup=3, iterations=20)
        result["scenario"] = name
        results.append(result)

        print(f"\n{'-' * 60}")
        print(f"  {name}")
        print(f"  Query: \"{query}\"")
        print(f"  Status: {result['status']}")
        print(f"  Avg: {result['avg_ms']:.1f}ms | P50: {result['p50_ms']:.1f}ms | P95: {result['p95_ms']:.1f}ms")
        print(f"  LLM calls/req: {result['llm_calls_per_req']}")
        print(f"  Laya calls/req: {result['laya_calls_per_req']}")
        print(f"  DB queries/req: {result['db_queries_per_req']}")

    # Summary table
    print(f"\n{'=' * 80}")
    print("SUMMARY TABLE")
    print(f"{'=' * 80}")
    print(f"{'Scenario':<35} {'Status':<12} {'Avg(ms)':<10} {'P50(ms)':<10} {'P95(ms)':<10} {'LLM':<6} {'Laya':<6} {'DB':<6}")
    print(f"{'-' * 95}")
    for r in results:
        print(f"{r['scenario']:<35} {r['status']:<12} {r['avg_ms']:<10.1f} {r['p50_ms']:<10.1f} {r['p95_ms']:<10.1f} {r['llm_calls_per_req']:<6} {r['laya_calls_per_req']:<6} {r['db_queries_per_req']:<6}")

    # Analysis
    print(f"\n{'=' * 80}")
    print("ANALYSIS")
    print(f"{'=' * 80}")

    clear_results = [r for r in results if r["scenario"].startswith("Clear")]
    ambig_results = [r for r in results if r["scenario"].startswith("Ambiguous")]
    
    if clear_results:
        avg_clear = sum(r["avg_ms"] for r in clear_results) / len(clear_results)
        print(f"  Clear queries avg latency: {avg_clear:.1f}ms")
        llm_on_clear = any(r["llm_calls_per_req"] > 0 for r in clear_results)
        laya_on_clear = any(r["laya_calls_per_req"] > 0 for r in clear_results)
        print(f"  LLM calls on clear path: {'YES [!]' if llm_on_clear else 'ZERO [OK]'}")
        print(f"  Laya calls on clear path: {'YES [!]' if laya_on_clear else 'ZERO [OK]'}")

    if ambig_results:
        avg_ambig = sum(r["avg_ms"] for r in ambig_results) / len(ambig_results)
        print(f"  Ambiguous queries avg latency: {avg_ambig:.1f}ms")
        llm_on_ambig = any(r["llm_calls_per_req"] > 0 for r in ambig_results)
        print(f"  LLM calls on ambiguous path: {'YES [!]' if llm_on_ambig else 'ZERO [OK]'}")

    # Save results to JSON
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {output_path}")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
