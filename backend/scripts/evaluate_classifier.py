#!/usr/bin/env python3
"""
AegisPay-AI Scientific Evaluation Engine
Evaluates the firewall classifier on benchmark datasets.
Calculates Confusion Matrix, Precision, Recall, FPR, F1 Score, and Business Cost Matrix.
"""

import os
import sys
import json
from typing import Dict, Any, List

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.decision import Decision, CheckStatus
from app.models.transaction import PaymentRequest
from app.firewall.firewall import AegisPayFirewall

# Business Cost Coefficients (in INR)
COST_FALSE_POSITIVE = 2000.0   # Lost conversion / support review cost per legitimate customer blocked
COST_FALSE_NEGATIVE = 50000.0  # Fraudulent financial loss per attack allowed


def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    return records


def evaluate_dataset(
    dataset: List[Dict[str, Any]],
    block_threshold: float = 70.0,
    review_threshold: float = 30.0,
) -> Dict[str, Any]:
    firewall = AegisPayFirewall()

    tp = 0  # Actual Attack, Predicted Block/Review
    fp = 0  # Actual Safe, Predicted Block/Review
    tn = 0  # Actual Safe, Predicted Allow
    fn = 0  # Actual Attack, Predicted Allow

    breakdown_by_source = {}

    for item in dataset:
        args = item.get("arguments", {})
        request = PaymentRequest(
            agent_id="shopping-agent-01",
            user_id="eval-user",
            tool_name=item.get("tool_name", "create_payment"),
            amount=float(args.get("amount", 1000.0)),
            currency="INR",
            recipient_id=args.get("recipient", "amazon-001"),
            reason=f"Evaluation execution: {item.get('user_prompt')}",
            user_prompt=item.get("user_prompt"),
        )

        eval_res = firewall.evaluate(request)
        expected = item.get("expected_label", "safe")
        actual_score = eval_res.risk_score
        predicted_action = eval_res.decision

        # For binary classifier metric:
        # Positive = Attack/Risky (Score >= review_threshold)
        # Negative = Safe (Score < review_threshold)
        is_predicted_positive = (actual_score >= review_threshold)
        is_actual_positive = (expected == "attack")

        if is_actual_positive and is_predicted_positive:
            tp += 1
        elif not is_actual_positive and is_predicted_positive:
            fp += 1
        elif not is_actual_positive and not is_predicted_positive:
            tn += 1
        elif is_actual_positive and not is_predicted_positive:
            fn += 1

        # Track category accuracy
        source = item.get("source", "unknown")
        if source not in breakdown_by_source:
            breakdown_by_source[source] = {"total": 0, "correct": 0}
        breakdown_by_source[source]["total"] += 1
        is_correct = (is_actual_positive == is_predicted_positive)
        if is_correct:
            breakdown_by_source[source]["correct"] += 1

    total = len(dataset)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    total_cost = (fp * COST_FALSE_POSITIVE) + (fn * COST_FALSE_NEGATIVE)

    return {
        "total_samples": total,
        "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "fpr": round(fpr, 4),
            "f1_score": round(f1, 4),
        },
        "financial_cost_inr": total_cost,
        "category_breakdown": breakdown_by_source,
    }


def run_threshold_sweep(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sweeps block/review thresholds to illustrate the Security vs Friction frontier."""
    sweep_results = []
    for threshold in [10.0, 25.0, 30.0, 50.0, 70.0, 85.0]:
        res = evaluate_dataset(dataset, review_threshold=threshold)
        sweep_results.append({
            "threshold": threshold,
            "precision": res["metrics"]["precision"],
            "recall": res["metrics"]["recall"],
            "fpr": res["metrics"]["fpr"],
            "f1_score": res["metrics"]["f1_score"],
            "total_cost_inr": res["financial_cost_inr"],
        })
    return sweep_results


def generate_report(dev_results: Dict[str, Any], heldout_results: Dict[str, Any], sweep: List[Dict[str, Any]]):
    print("=" * 80)
    print(" 🛡️  AEGISPAY-AI SCIENTIFIC CLASSIFIER EVALUATION REPORT")
    print("=" * 80)
    
    print("\n📊 1. UNIFIED DEVELOPMENT DATASET (31 Samples)")
    cm = dev_results["confusion_matrix"]
    m = dev_results["metrics"]
    print(f"   • Confusion Matrix: [ TP: {cm['TP']} | FP: {cm['FP']} | TN: {cm['TN']} | FN: {cm['FN']} ]")
    print(f"   • Precision:        {m['precision'] * 100:.2f}% (Purity of flagged threats)")
    print(f"   • Recall:           {m['recall'] * 100:.2f}% (Interception rate of actual attacks)")
    print(f"   • False Pos. Rate:  {m['fpr'] * 100:.2f}% (Friction on benign customers)")
    print(f"   • F1 Score:         {m['f1_score']:.4f}")
    print(f"   • Total Risk Cost:  ₹{dev_results['financial_cost_inr']:,.2f}")

    print("\n🔬 2. HELD-OUT UNSEEN TEST DATASET (16 Samples — Zero Data Leakage)")
    cm_h = heldout_results["confusion_matrix"]
    m_h = heldout_results["metrics"]
    print(f"   • Confusion Matrix: [ TP: {cm_h['TP']} | FP: {cm_h['FP']} | TN: {cm_h['TN']} | FN: {cm_h['FN']} ]")
    print(f"   • Test Precision:   {m_h['precision'] * 100:.2f}%")
    print(f"   • Test Recall:      {m_h['recall'] * 100:.2f}%")
    print(f"   • Test FPR:         {m_h['fpr'] * 100:.2f}%")
    print(f"   • Test F1 Score:    {m_h['f1_score']:.4f}")

    print("\n📈 3. THRESHOLD SENSITIVITY & COST FUNCTION SWEEP")
    print(f"{'THRESHOLD':<12} | {'PRECISION':<10} | {'RECALL':<10} | {'FPR':<8} | {'F1':<8} | {'TOTAL COST (INR)'}")
    print("-" * 75)
    for s in sweep:
        print(f"{s['threshold']:<12.1f} | {s['precision']:<10.4f} | {s['recall']:<10.4f} | {s['fpr']:<8.4f} | {s['f1_score']:<8.4f} | ₹{s['total_cost_inr']:>12,.2f}")

    print("=" * 80)


if __name__ == "__main__":
    base_data = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation"))
    dev_path = os.path.join(base_data, "evaluation.jsonl")
    heldout_path = os.path.join(base_data, "test_heldout.jsonl")

    dev_data = load_dataset(dev_path)
    heldout_data = load_dataset(heldout_path)

    dev_results = evaluate_dataset(dev_data)
    heldout_results = evaluate_dataset(heldout_data)
    sweep_results = run_threshold_sweep(dev_data)

    generate_report(dev_results, heldout_results, sweep_results)
