"""Model inference tests."""

import pytest
from backend.ml.monitor import InferenceMonitor
from backend.services.drug_checker import drug_checker


class TestInferenceMonitor:
    """Test the monitoring system."""

    def test_empty_metrics(self):
        mon = InferenceMonitor()
        metrics = mon.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["error_rate"] == 0.0

    def test_log_and_retrieve(self):
        mon = InferenceMonitor()
        mon.log_inference("test-model", 1.5, 100, "chat", True)
        mon.log_inference("test-model", 2.0, 150, "chat", True)
        mon.log_inference("test-model", 0.5, 0, "chat", False)

        metrics = mon.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["total_errors"] == 1
        assert metrics["error_rate"] == pytest.approx(33.33, rel=0.1)
        assert len(metrics["recent_records"]) == 3

    def test_model_stats(self):
        mon = InferenceMonitor()
        mon.log_inference("model-a", 1.0, 50, "chat", True)
        mon.log_inference("model-b", 2.0, 100, "generate", True)

        stats = mon.get_model_stats()
        assert "model-a" in stats
        assert "model-b" in stats
        assert stats["model-a"]["total"] == 1
        assert stats["model-b"]["total"] == 1


class TestDrugChecker:
    """Test drug interaction checking."""

    def test_known_interaction(self):
        result = drug_checker.check("escitalopram", "phenelzine")
        assert result is not None
        assert result["severity"] == "critical"

    def test_reverse_order(self):
        result = drug_checker.check("phenelzine", "escitalopram")
        assert result is not None
        assert result["severity"] == "critical"

    def test_no_interaction(self):
        result = drug_checker.check("loratadine", "vitamin_d")
        assert result is None

    def test_multiple_check(self):
        results = drug_checker.check_multiple(["escitalopram", "ibuprofen", "phenelzine"])
        assert len(results) >= 2  # SSRI+MAOI and SSRI+NSAID

    def test_critical_flagged(self):
        results = drug_checker.check_multiple(["escitalopram", "phenelzine"])
        critical = [r for r in results if r["severity"] == "critical"]
        assert len(critical) >= 1
