import asyncio
import random
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="High-Throughput Banking API Mock", version="1.0.0")


class TransferPayload(BaseModel):
    source_account: str = Field(..., min_length=4)
    destination_account: str = Field(..., min_length=4)
    amount: float = Field(..., gt=0.0)
    currency: str = "USD"


@app.get("/health")
async def health():
    return {"status": "HEALTHY", "timestamp": time.time()}


@app.get("/api/v1/accounts/{account_id}/balance")
async def get_balance(account_id: str):
    # Simulated database fetch latency (3ms to 12ms)
    delay = random.uniform(0.003, 0.012)
    await asyncio.sleep(delay)
    return {
        "account_id": account_id,
        "available_balance": 15420.50,
        "currency": "USD",
        "latency_ms": round(delay * 1000, 2),
    }


@app.post("/api/v1/payments/transfer")
async def execute_transfer(payload: TransferPayload):
    # Simulated atomic transactional write latency (15ms to 35ms)
    # Rare p99 spike simulation (5% chance of 80ms)
    if random.random() < 0.05:
        delay = random.uniform(0.070, 0.095)
    else:
        delay = random.uniform(0.015, 0.035)

    await asyncio.sleep(delay)

    # Simulated 0.1% rate error
    if random.random() < 0.001:
        raise HTTPException(status_code=503, detail="Simulated temporary database lock contention")

    return {
        "status": "COMPLETED",
        "source_account": payload.source_account,
        "destination_account": payload.destination_account,
        "amount": payload.amount,
        "reference": f"REF-{int(time.time()*1000)}",
        "latency_ms": round(delay * 1000, 2),
    }


@app.get("/api/v1/reports/statement")
async def generate_statement(account_id: str = "ACC-DEFAULT"):
    # Simulated heavier aggregation query (30ms to 55ms)
    delay = random.uniform(0.030, 0.055)
    await asyncio.sleep(delay)
    return {
        "account_id": account_id,
        "total_transactions": 250,
        "statement_period": "30_DAYS",
        "latency_ms": round(delay * 1000, 2),
    }
