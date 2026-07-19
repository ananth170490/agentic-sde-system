from app.reporting import classify_latency


def test_classify_latency_detects_slo_breach() -> None:
    result = classify_latency([120, 180, 220, 310, 450], target_p95_ms=300)
    assert result["sample_size"] == 5
    assert result["p95_ms"] >= 310
    assert result["meets_target"] is False


def test_classify_latency_handles_empty_samples() -> None:
    result = classify_latency([], target_p95_ms=300)
    assert result == {"sample_size": 0, "p95_ms": 0, "meets_target": True}
