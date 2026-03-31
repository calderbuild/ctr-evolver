"""QA answer evaluator -- ground truth comparison for OfficeQA.

Uses the same scoring logic as the Arena platform's reward.py.
"""

import re


def score_answer(ground_truth: str, predicted: str, tolerance: float = 0.01) -> float:
    """Score predicted answer against ground truth.

    Uses fuzzy numeric matching with tolerance.
    Returns 1.0 (correct) or 0.0 (incorrect).
    """
    is_correct, _ = fuzzy_match_answer(ground_truth, predicted, tolerance)
    return 1.0 if is_correct else 0.0


def evaluate_answer(ground_truth: str, predicted: str, tolerance: float = 0.01) -> dict:
    """Evaluate with detailed rationale.

    Returns dict with: score, is_correct, rationale
    """
    is_correct, rationale = fuzzy_match_answer(ground_truth, predicted, tolerance)
    return {
        "score": 1.0 if is_correct else 0.0,
        "is_correct": is_correct,
        "rationale": rationale,
    }


def fuzzy_match_answer(
    ground_truth: str, predicted: str, tolerance: float = 0.01
) -> tuple[bool, str]:
    """Fuzzy match predicted answer against ground truth.

    Handles: numeric values with tolerance, percentages, multi-number lists,
    text answers, and unit normalization.
    """
    if not ground_truth or not predicted:
        return False, "Empty ground truth or prediction"

    gt_numbers = _extract_numbers(ground_truth)
    pred_numbers = _extract_numbers(predicted)

    # Both have numbers -- numeric comparison
    if gt_numbers and pred_numbers:
        if len(gt_numbers) > 1:
            # Multi-number answer: all GT numbers must match
            matched = 0
            for gt_val in gt_numbers:
                for pred_val in pred_numbers:
                    if _numbers_match(gt_val, pred_val, tolerance):
                        matched += 1
                        break
            if matched == len(gt_numbers):
                return True, f"List match: all {len(gt_numbers)} numbers found"
            return False, f"List mismatch: {matched}/{len(gt_numbers)} matched"

        # Single number
        gt_val = gt_numbers[0]
        best_diff = float("inf")
        for pred_val in pred_numbers:
            if _numbers_match(gt_val, pred_val, tolerance):
                return True, f"Numeric match: GT={gt_val}, Pred={pred_val}"
            if gt_val != 0:
                diff = abs(gt_val - pred_val) / abs(gt_val)
                best_diff = min(best_diff, diff)

        return False, f"No numeric match: GT={gt_val}, closest diff={best_diff*100:.1f}%"

    # Text comparison (case-insensitive)
    gt_clean = ground_truth.strip().lower().strip("\"'")
    pred_clean = predicted.strip().lower().strip("\"'")

    if gt_clean in pred_clean or gt_clean == pred_clean:
        return True, f"Text match: '{ground_truth}' found in prediction"

    return False, f"No match: GT='{ground_truth[:80]}', Pred='{predicted[:80]}'"


def _extract_numbers(text: str) -> list[float]:
    """Extract all numbers from text, handling commas and percentages."""
    text = text.replace("\u2212", "-").replace(",", "")
    numbers = []
    for match in re.finditer(r"-?\d+\.?\d*%?", text):
        s = match.group().rstrip("%")
        if s and s != "-":
            try:
                numbers.append(float(s))
            except ValueError:
                pass
    return numbers


def _numbers_match(a: float, b: float, tolerance: float) -> bool:
    """Check if two numbers match within tolerance."""
    if a == 0:
        return b == 0
    return abs(a - b) / abs(a) <= tolerance
