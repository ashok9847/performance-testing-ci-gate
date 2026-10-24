import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any


class PerformanceQualityGate:
    """Evaluates load test output CSV against defined SLA latency and error thresholds."""

    def __init__(self, thresholds_path: str):
        with open(thresholds_path, "r", encoding="utf-8") as f:
            self.thresholds = json.load(f)

    def parse_locust_stats_csv(self, stats_csv_path: str) -> List[Dict[str, Any]]:
        rows = []
        if not os.path.exists(stats_csv_path):
            raise FileNotFoundError(f"Stats CSV not found at: {stats_csv_path}")

        with open(stats_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def evaluate(self, stats_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        summary_results = []
        global_thresholds = self.thresholds.get("global", {})
        endpoint_thresholds = self.thresholds.get("endpoints", {})

        for row in stats_rows:
            name = row.get("Name", "").strip()
            method = row.get("Type", "").strip()
            req_count = int(row.get("Request Count", 0))
            fail_count = int(row.get("Failure Count", 0))

            if req_count == 0:
                continue

            fail_rate = (fail_count / req_count) * 100.0
            median_ms = float(row.get("50%", row.get("Median Response Time", 0)))
            p95_ms = float(row.get("95%", 0))
            p99_ms = float(row.get("99%", 0))

            is_aggregated = (name == "Aggregated")

            # Check rules
            passed = True
            reasons = []

            if is_aggregated:
                max_fail = global_thresholds.get("max_failure_rate_percent", 1.0)
                if fail_rate > max_fail:
                    passed = False
                    reasons.append(f"Global failure rate {fail_rate:.2f}% exceeded limit {max_fail}%")

                max_p95 = global_thresholds.get("p95_response_time_ms", 300.0)
                if p95_ms > max_p95:
                    passed = False
                    reasons.append(f"Global p95 latency {p95_ms}ms exceeded SLA limit {max_p95}ms")

            else:
                target_p95 = endpoint_thresholds.get(name, {}).get("p95_response_time_ms")
                if target_p95 and p95_ms > target_p95:
                    passed = False
                    reasons.append(f"Endpoint p95 {p95_ms}ms breached threshold {target_p95}ms")

            if not passed:
                violations.extend(reasons)

            summary_results.append({
                "name": name,
                "method": method,
                "requests": req_count,
                "failures": fail_count,
                "fail_rate": f"{fail_rate:.2f}%",
                "median_ms": median_ms,
                "p95_ms": p95_ms,
                "p99_ms": p99_ms,
                "status": "PASS" if passed else "FAIL",
                "reasons": "; ".join(reasons) if reasons else "OK",
            })

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "summary": summary_results,
        }

    def print_report(self, evaluation: Dict[str, Any]):
        print("\n" + "=" * 90)
        print("          PERFORMANCE CI QUALITY GATE EVALUATION REPORT")
        print("=" * 90)
        header = f"{'ENDPOINT':<32} | {'REQS':<8} | {'FAIL%':<8} | {'p50(ms)':<8} | {'p95(ms)':<8} | {'STATUS':<6}"
        print(header)
        print("-" * 90)

        for s in evaluation["summary"]:
            status_color = "\033[92mPASS\033[0m" if s["status"] == "PASS" else "\033[91mFAIL\033[0m"
            print(f"{s['name'][:32]:<32} | {s['requests']:<8} | {s['fail_rate']:<8} | {s['median_ms']:<8.1f} | {s['p95_ms']:<8.1f} | {status_color}")

        print("=" * 90)
        if evaluation["passed"]:
            print("\033[92m>>> [GATE PASSED] All latency and error rate SLAs successfully met.\033[0m\n")
        else:
            print("\033[91m>>> [GATE FAILED] SLA Threshold Breaches Detected:\033[0m")
            for v in evaluation["violations"]:
                print(f"    - {v}")
            print()


def main():
    if len(sys.argv) < 3:
        print("Usage: python gate_runner.py <thresholds.json> <stats_csv_path>")
        sys.exit(2)

    thresholds_file = sys.argv[1]
    stats_file = sys.argv[2]

    gate = PerformanceQualityGate(thresholds_file)
    rows = gate.parse_locust_stats_csv(stats_file)
    evaluation = gate.evaluate(rows)
    gate.print_report(evaluation)

    # Optional: Write GitHub Actions Step Summary
    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as f:
            f.write("## 🚀 Performance Testing Quality Gate Results\n\n")
            status_badge = "✅ **PASSED**" if evaluation["passed"] else "❌ **FAILED**"
            f.write(f"**Overall Status**: {status_badge}\n\n")
            f.write("| Endpoint | Requests | Failure Rate | p50 (ms) | p95 (ms) | Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for s in evaluation["summary"]:
                f.write(f"| `{s['name']}` | {s['requests']} | {s['fail_rate']} | {s['median_ms']:.1f} | {s['p95_ms']:.1f} | {s['status']} |\n")
            f.write("\n")

    sys.exit(0 if evaluation["passed"] else 1)


if __name__ == "__main__":
    main()
