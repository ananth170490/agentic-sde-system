from __future__ import annotations


def classify_latency(latencies_ms: list[int], target_p95_ms: int) -> dict[str, int | bool]:
    if not latencies_ms:
        return {"sample_size": 0, "p95_ms": 0, "meets_target": True}

    ordered = sorted(latencies_ms)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    p95_value = ordered[index]
    return {"sample_size": len(ordered), "p95_ms": p95_value, "meets_target": p95_value <= target_p95_ms}
