import json
import pytest
from perf_suite.gate_runner import PerformanceQualityGate


@pytest.fixture
def sample_thresholds_file(tmp_path):
    thresholds_data = {
        "global": {
            "max_failure_rate_percent": 1.0,
            "p95_response_time_ms": 200.0,
        },
        "endpoints": {
            "/api/v1/payments/transfer": {
                "p95_response_time_ms": 150.0,
            }
        },
    }
    file_path = tmp_path / "thresholds.json"
    file_path.write_text(json.dumps(thresholds_data), encoding="utf-8")
    return str(file_path)


class TestPerformanceQualityGate:

    def test_gate_passes_healthy_metrics(self, sample_thresholds_file):
        gate = PerformanceQualityGate(sample_thresholds_file)
        rows = [
            {
                "Type": "POST",
                "Name": "/api/v1/payments/transfer",
                "Request Count": "500",
                "Failure Count": "1",
                "50%": "35",
                "95%": "110",
                "99%": "140",
            },
            {
                "Type": "",
                "Name": "Aggregated",
                "Request Count": "500",
                "Failure Count": "1",
                "50%": "35",
                "95%": "110",
                "99%": "140",
            },
        ]
        result = gate.evaluate(rows)
        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_gate_fails_on_endpoint_p95_breach(self, sample_thresholds_file):
        gate = PerformanceQualityGate(sample_thresholds_file)
        rows = [
            {
                "Type": "POST",
                "Name": "/api/v1/payments/transfer",
                "Request Count": "1000",
                "Failure Count": "0",
                "50%": "50",
                "95%": "195",  # Exceeds 150ms endpoint threshold
                "99%": "250",
            },
            {
                "Type": "",
                "Name": "Aggregated",
                "Request Count": "1000",
                "Failure Count": "0",
                "50%": "50",
                "95%": "195",
                "99%": "250",
            },
        ]
        result = gate.evaluate(rows)
        assert result["passed"] is False
        assert any("Endpoint p95" in v for v in result["violations"])

    def test_gate_fails_on_high_error_rate(self, sample_thresholds_file):
        gate = PerformanceQualityGate(sample_thresholds_file)
        rows = [
            {
                "Type": "",
                "Name": "Aggregated",
                "Request Count": "100",
                "Failure Count": "5",  # 5% failures > 1.0% limit
                "50%": "20",
                "95%": "80",
                "99%": "100",
            }
        ]
        result = gate.evaluate(rows)
        assert result["passed"] is False
        assert any("failure rate" in v.lower() for v in result["violations"])
