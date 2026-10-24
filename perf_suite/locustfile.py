import random
from locust import HttpUser, task, between


class BankingWorkloadUser(HttpUser):
    """Simulates realistic concurrent banking customer traffic patterns."""

    wait_time = between(0.05, 0.25)  # High frequency pacing

    @task(6)
    def check_account_balance(self):
        acc_id = f"ACC-{random.randint(1000, 1050)}"
        self.client.get(f"/api/v1/accounts/{acc_id}/balance", name="/api/v1/accounts/[id]/balance")

    @task(3)
    def make_payment_transfer(self):
        payload = {
            "source_account": f"ACC-{random.randint(1000, 1050)}",
            "destination_account": f"ACC-{random.randint(2000, 2050)}",
            "amount": round(random.uniform(10.0, 500.0), 2),
            "currency": "USD",
        }
        self.client.post("/api/v1/payments/transfer", json=payload, name="/api/v1/payments/transfer")

    @task(1)
    def get_statement(self):
        self.client.get("/api/v1/reports/statement", name="/api/v1/reports/statement")

    @task(1)
    def health_probe(self):
        self.client.get("/health", name="/health")
