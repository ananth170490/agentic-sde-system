from app.cache import ReportCache


def test_report_cache_evicts_oldest_entry() -> None:
    cache = ReportCache(max_entries=2)
    cache.put("r1", "first")
    cache.put("r2", "second")
    cache.put("r3", "third")

    assert cache.get("r1") is None
    assert cache.get("r2") == "second"
    assert cache.get("r3") == "third"
