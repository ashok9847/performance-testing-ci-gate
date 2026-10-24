# Performance Testing CI Quality Gate

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Locust](https://img.shields.io/badge/Locust-Load%20Testing-green.svg)](https://locust.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com/)
[![CI Quality Gate](https://img.shields.io/badge/Quality%20Gate-Automated-orange.svg)]()
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated Performance and Load Testing framework with **Locust**, declarative **SLA Quality Gates**, and **GitHub Actions CI integration**. Designed to detect latency degradation and throughput regressions before merging code into production.

Developed by **[Ashok Aryal](https://github.com/ashok9847)**.

---

## 1. Architecture & CI Quality Gate Workflow

Traditional performance testing is often performed manually in staging environments weeks after code is merged. This framework embeds performance regression gates directly into the continuous integration (CI) pipeline.

```
+-------------------------------------------------------------------------------+
|                             GitHub Actions CI Pipeline                        |
+-------------------------------------------------------------------------------+
                                        |
                   1. Spin up target API mock in background
                                        v
                 +---------------------------------------------+
                 |          High-Throughput Banking API        |
                 |  - /health                                  |
                 |  - /api/v1/accounts/{id}/balance            |
                 |  - /api/v1/payments/transfer                |
                 |  - /api/v1/reports/statement                |
                 +----------------------+----------------------+
                                        ^
                                        | 2. Headless Locust Load Generation
                                        |    (Concurrent virtual users & pacing)
                                        |
                 +----------------------+----------------------+
                 |          Locust Headless Test Runner        |
                 |  - Generates CSV metrics & HTML reports     |
                 +----------------------+----------------------+
                                        |
                         3. Metric CSV Stream (_stats.csv)
                                        v
                 +---------------------------------------------+
                 |       Performance CI Quality Gate           |
                 |  - Compares p50, p95, p99 against SLA limits|
                 |  - Asserts max failure rate (< 1.0%)        |
                 |  - Detects endpoint regression spikes       |
                 +----------------------+----------------------+
                                        |
                     +------------------+------------------+
                     |                                     |
              SLA Met (0)                           SLA Breached (1)
                     v                                     v
             [Build Passes]                       [Block Pull Request]
```

---

## 2. Declarative SLA Configuration (`thresholds.json`)

SLA criteria are decoupled into declarative JSON definitions for global aggregates and individual endpoints:

```json
{
  "global": {
    "max_failure_rate_percent": 1.0,
    "median_response_time_ms": 100.0,
    "p95_response_time_ms": 250.0,
    "p99_response_time_ms": 500.0
  },
  "endpoints": {
    "/health": { "p95_response_time_ms": 60.0 },
    "/api/v1/accounts/[id]/balance": { "p95_response_time_ms": 150.0 },
    "/api/v1/payments/transfer": { "p95_response_time_ms": 250.0 }
  }
}
```

---

## 3. Directory Structure

```
performance-testing-ci-gate/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated headless load test & CI quality gate
├── perf_suite/
│   ├── __init__.py
│   ├── locustfile.py            # User task definitions and weight distributions
│   ├── thresholds.json          # Declarative latency SLA & error rate limits
│   └── gate_runner.py           # CLI evaluator and GitHub summary writer
├── target_api/
│   ├── __init__.py
│   └── server.py                # High-throughput mock API with latency profiles
├── tests/
│   ├── __init__.py
│   └── test_gate_evaluator.py   # Unit tests for threshold evaluation engine
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Automated orchestration for load test + gate runner
├── requirements.txt             # Dependencies
└── README.md
```

---

## 4. Quickstart & Local Execution

### Local Python Virtualenv
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

### Step 1: Start Mock Banking API
```bash
uvicorn target_api.server:app --port 8000
```

### Step 2: Run Headless Load Test & Quality Gate
```bash
# Generate metrics
locust -f perf_suite/locustfile.py --headless -u 20 -r 5 --run-time 20s --host http://localhost:8000 --csv=reports/perf --html=reports/report.html

# Evaluate Quality Gate
python perf_suite/gate_runner.py perf_suite/thresholds.json reports/perf_stats.csv
```

### Step 3: Run Interactive Locust Web UI
```bash
locust -f perf_suite/locustfile.py --host http://localhost:8000
# Open http://localhost:8089 in your browser
```

### Step 4: Run via Docker Compose
```bash
docker compose up --build --abort-on-container-exit
```

---

## 5. Interview-Ready Technical Concepts

### Q1: Why do performance engineers measure 95th and 99th percentiles instead of Average (Mean) latency?
> **Answer**: Average response times hide extreme latency spikes (outliers). For example, if 99 requests take 10ms and 1 request takes 5,000ms, the average is ~59ms, which masks the fact that customers on the tail end are experiencing severe slowdowns. The 95th and 99th percentiles represent the true worst-case experience of the top 5% and 1% of users, which is essential for meeting financial SLAs.

### Q2: How does a Quality Gate prevent performance regressions in CI/CD?
> **Answer**: By executing a deterministic load test in the PR build and asserting metrics against `thresholds.json`, any pull request that introduces an N+1 database query, CPU lock, or memory leak causes the 95th percentile or error rate to spike above threshold. The gate runner exits with status code 1, automatically blocking the merge before poor code reaches production.

---

## License
MIT License. Created by [Ashok Aryal](https://github.com/ashok9847).
