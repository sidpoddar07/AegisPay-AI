import os
import pytest
from scripts.evaluate_classifier import load_dataset, evaluate_dataset

def test_heldout_dataset_metrics():
    """
    Evaluates AegisPay-AI against the strictly held-out unseen test dataset.
    Enforces minimum production standards:
    - Precision >= 90%
    - Recall >= 95%
    - FPR <= 5%
    - F1 Score >= 0.90
    """
    base_data = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation"))
    heldout_path = os.path.join(base_data, "test_heldout.jsonl")
    
    assert os.path.exists(heldout_path), "Held-out test dataset file missing!"
    
    heldout_data = load_dataset(heldout_path)
    assert len(heldout_data) >= 15, "Held-out dataset must contain at least 15 unseen samples."
    
    results = evaluate_dataset(heldout_data, review_threshold=30.0)
    metrics = results["metrics"]
    
    assert metrics["precision"] >= 0.90, f"Precision fell below 90%: {metrics['precision']}"
    assert metrics["recall"] >= 0.95, f"Recall fell below 95%: {metrics['recall']}"
    assert metrics["fpr"] <= 0.05, f"False Positive Rate exceeded 5%: {metrics['fpr']}"
    assert metrics["f1_score"] >= 0.90, f"F1 Score fell below 0.90: {metrics['f1_score']}"
    assert results["financial_cost_inr"] == 0.0, "Held-out dataset incurred financial losses!"
