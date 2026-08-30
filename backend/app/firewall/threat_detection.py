import math
import re
from typing import List, Tuple
from app.models.decision import CheckStatus
from app.models.transaction import PaymentRequest

# Pre-compiled Regex Automata for ultra-low latency (< 0.01ms)
COMPILED_INJECTION_PATTERNS = [
    re.compile(r"(?i)(ignore\s+(all\s+)?(prior|previous|above)\s+instructions)"),
    re.compile(r"(?i)(system\s+override|admin\s+mode|developer\s+mode|root\s+bypass)"),
    re.compile(r"(?i)(transfer\s+all\s+(funds|balance|money|credits))"),
    re.compile(r"(?i)(do\s+not\s+(ask|notify|confirm|log|alert))"),
    re.compile(r"(?i)(urgent\s+(transfer|payment|wire)|emergency\s+payout)"),
    re.compile(r"(?i)(jailbreak|dan\s+mode|unrestricted\s+mode)"),
    re.compile(r"(?i)(bypass\s+security|disable\s+guardrails|skip\s+verification)"),
]

NUMBERS_REGEX = re.compile(r"[\d,]+(?:\.\d+)?")
WHITESPACE_REGEX = re.compile(r"\s+")


def calculate_shannon_entropy(data: str) -> float:
    """
    Calculates Shannon Entropy to detect Base64/Hex obfuscated payloads.
    Normal English sentences usually have entropy < 4.0. Obfuscated ciphertext > 4.5.
    """
    if not data or len(data) < 20:
        return 0.0
    
    cleaned = WHITESPACE_REGEX.sub("", data)
    if not cleaned:
        return 0.0

    length = len(cleaned)
    freq = {}
    for char in cleaned:
        freq[char] = freq.get(char, 0) + 1

    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)

    return entropy


def detect_intent_divergence(request: PaymentRequest) -> Tuple[bool, str]:
    """
    Detects if the agent's payment amount or recipient diverges drastically
    from the original human user's prompt.
    """
    if not request.user_prompt:
        return False, ""

    prompt = request.user_prompt.lower()
    
    numbers = NUMBERS_REGEX.findall(prompt)
    if numbers:
        try:
            user_expected_amount = float(numbers[0].replace(",", ""))
            if user_expected_amount > 0 and request.amount > (user_expected_amount * 1.25) and (request.amount - user_expected_amount) >= 100:
                return True, f"Intent Discrepancy: User authorized ~₹{user_expected_amount:.2f}, but agent requested ₹{request.amount:.2f}."
        except ValueError:
            pass

    return False, ""


def check_threat(request: PaymentRequest) -> Tuple[CheckStatus, float, List[str]]:
    """
    Evaluates adversarial threats: Prompt Injections, Payload Obfuscation, and Intent Divergence.
    Returns (CheckStatus, threat_score [0-100], list of reason signals).
    """
    reasons = []
    threat_score = 0.0

    combined_text = f"{request.reason} {request.user_prompt or ''}"

    # 1. Pre-compiled Prompt Injection Pattern Scan
    for pattern in COMPILED_INJECTION_PATTERNS:
        match = pattern.search(combined_text)
        if match:
            threat_score += 85.0
            reasons.append(f"Prompt Injection Detected: Matched adversarial pattern '{match.group(0)}'.")

    # 2. Shannon Entropy / Obfuscation Scan
    if len(request.reason) >= 30:
        entropy = calculate_shannon_entropy(request.reason)
        if entropy > 4.6:
            threat_score += 40.0
            reasons.append(f"High Entropy Payload (Entropy: {entropy:.2f}): Suspected Base64/Hex obfuscated attack payload.")

    # 3. Intent Divergence Scan
    divergence_found, div_msg = detect_intent_divergence(request)
    if divergence_found:
        threat_score += 60.0
        reasons.append(div_msg)

    # Normalize threat score
    threat_score = min(100.0, threat_score)

    if threat_score >= 70.0:
        return CheckStatus.FAIL, threat_score, reasons
    elif threat_score >= 25.0:
        return CheckStatus.WARNING, threat_score, reasons
    else:
        return CheckStatus.PASS, threat_score, ["No active threat or injection signatures detected."]
