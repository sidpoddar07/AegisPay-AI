import time
import statistics
from app.firewall.firewall import AegisPayFirewall
from app.models.transaction import PaymentRequest


def test_latency_sla_under_25ms():
    """
    Empirical benchmark verifying that AegisPay evaluates in-flight requests
    strictly under the 25ms SLA required for high-throughput payment gateways.
    """
    firewall = AegisPayFirewall()
    
    # Warm-up iterations
    for _ in range(10):
        warmup_req = PaymentRequest(
            agent_id="shopping-agent-01",
            user_id="user-warmup",
            tool_name="create_payment",
            amount=1000.0,
            currency="INR",
            recipient_id="amazon-001",
            reason="Warmup check",
            user_prompt="Warmup",
        )
        firewall.evaluate(warmup_req)

    latencies = []
    iterations = 1000

    for i in range(iterations):
        request = PaymentRequest(
            agent_id="shopping-agent-01",
            user_id=f"user-{i % 100:03d}",
            tool_name="create_payment",
            amount=1000.0 + (i % 200) * 10,
            currency="INR",
            recipient_id="amazon-001",
            reason=f"Batch benchmark transaction #{i}",
            user_prompt="Buy supplies for 1000",
        )

        t0 = time.perf_counter()
        eval_res = firewall.evaluate(request)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

    sorted_lats = sorted(latencies)
    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = sorted_lats[int(iterations * 0.95)]
    p99_lat = sorted_lats[int(iterations * 0.99)]

    print(f"\n[BENCHMARK - 1,000 Iterations]")
    print(f"   Mean:   {mean_lat:.4f} ms")
    print(f"   Median: {median_lat:.4f} ms")
    print(f"   P95:    {p95_lat:.4f} ms")
    print(f"   P99:    {p99_lat:.4f} ms")

    assert mean_lat < 1.0, f"Mean latency {mean_lat}ms exceeded 1.0ms internal target"
    assert p99_lat < 5.0, f"P99 latency {p99_lat}ms exceeded 5.0ms internal target"
    assert mean_lat < 25.0, f"Mean latency {mean_lat}ms exceeded 25ms SLA"
