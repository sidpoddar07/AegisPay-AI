import time
from app.firewall.firewall import RazorGuardFirewall
from app.models.transaction import PaymentRequest


def test_latency_sla_under_25ms():
    """
    Stress test verifying that RazorGuard evaluates requests
    strictly under the 25ms SLA required for high-throughput payment gateways.
    """
    firewall = RazorGuardFirewall()
    latencies = []

    for i in range(50):
        request = PaymentRequest(
            agent_id="shopping-agent-01",
            user_id=f"user-{i:03d}",
            tool_name="create_payment",
            amount=1000.0 + (i * 50),
            currency="INR",
            recipient_id="amazon-001",
            reason=f"Batch benchmark payment request #{i}",
            user_prompt="Buy supplies",
        )

        t0 = time.perf_counter()
        eval_res = firewall.evaluate(request)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

    avg_latency = sum(latencies) / len(latencies)
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

    print(f"\n[BENCHMARK] Mean Latency: {avg_latency:.3f}ms | P99: {p99_latency:.3f}ms")

    assert avg_latency < 25.0, f"Average latency {avg_latency}ms exceeded 25ms SLA"
    assert p99_latency < 50.0, f"P99 latency {p99_latency}ms exceeded 50ms threshold"
