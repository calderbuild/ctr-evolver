"""Position-adjusted CTR evaluation."""

import pandas as pd
from scipy import stats

from .opportunity import get_baseline_ctr


def position_adjusted_ctr(
    actual_ctr: float, position: float, baseline_ctr: float | None = None
) -> float:
    """Normalize CTR by position to enable fair comparison.

    Returns: actual_ctr / baseline_ctr (ratio)

    A value > 1.0 means CTR is above baseline for that position.
    A value < 1.0 means CTR is below baseline.
    """
    if baseline_ctr is None:
        baseline_ctr = get_baseline_ctr(position)

    if baseline_ctr == 0:
        return 0.0

    return actual_ctr / baseline_ctr


def is_significant(
    before_ctr: float,
    after_ctr: float,
    before_impressions: int,
    after_impressions: int,
    alpha: float = 0.05,
) -> bool:
    """Test if CTR change is statistically significant (two-proportion z-test).

    Args:
        before_ctr: CTR before intervention
        after_ctr: CTR after intervention
        before_impressions: Impressions before
        after_impressions: Impressions after
        alpha: Significance level (default 0.05)

    Returns:
        True if change is significant at alpha level
    """
    # Convert CTR to click counts
    before_clicks = int(before_ctr * before_impressions)
    after_clicks = int(after_ctr * after_impressions)

    # Two-proportion z-test
    count = [after_clicks, before_clicks]
    nobs = [after_impressions, before_impressions]

    # Handle edge cases
    if before_impressions < 30 or after_impressions < 30:
        return False  # Not enough data

    try:
        z_stat, p_value = stats.proportions_ztest(count, nobs)
        return p_value < alpha
    except (ValueError, ZeroDivisionError):
        return False


def evaluate_intervention(
    intervention: dict,
    before_data: pd.DataFrame,
    after_data: pd.DataFrame,
    min_days: int = 7,
) -> dict:
    """Evaluate an intervention by comparing before/after CTR.

    Args:
        intervention: Intervention record with page_url, query, position_at_intervention
        before_data: GSC data before intervention
        after_data: GSC data after intervention (must be >= min_days)
        min_days: Minimum days of after data required

    Returns:
        dict with evaluation metrics:
        - before_ctr, after_ctr
        - before_impressions, after_impressions
        - ctr_lift (absolute change)
        - ctr_lift_pct (percentage change)
        - position_adjusted_lift
        - is_significant
        - status: 'success', 'failure', 'insufficient_data'
    """
    page_url = intervention["page_url"]
    query = intervention["query"]
    position_at_intervention = intervention["position_at_intervention"]

    # Filter data for this page + query
    before = before_data[
        (before_data["page"] == page_url) & (before_data["query"] == query)
    ]
    after = after_data[
        (after_data["page"] == page_url) & (after_data["query"] == query)
    ]

    # Check if we have enough data
    if before.empty or after.empty:
        return {"status": "insufficient_data", "reason": "No data for page+query"}

    # Aggregate metrics
    before_impressions = before["impressions"].sum()
    before_clicks = before["clicks"].sum()
    before_ctr = before_clicks / before_impressions if before_impressions > 0 else 0

    after_impressions = after["impressions"].sum()
    after_clicks = after["clicks"].sum()
    after_ctr = after_clicks / after_impressions if after_impressions > 0 else 0

    # Check minimum impressions
    if before_impressions < 10 or after_impressions < 10:
        return {"status": "insufficient_data", "reason": "Not enough impressions"}

    # Calculate lifts
    ctr_lift = after_ctr - before_ctr
    ctr_lift_pct = (ctr_lift / before_ctr) if before_ctr > 0 else 0

    # Position-adjusted lift
    baseline_ctr = get_baseline_ctr(position_at_intervention)
    before_adj = position_adjusted_ctr(
        before_ctr, position_at_intervention, baseline_ctr
    )
    after_adj = position_adjusted_ctr(after_ctr, position_at_intervention, baseline_ctr)
    position_adjusted_lift = after_adj - before_adj

    # Statistical significance
    significant = is_significant(
        before_ctr, after_ctr, before_impressions, after_impressions
    )

    # Determine status
    if significant and ctr_lift > 0:
        status = "success"
    elif significant and ctr_lift < 0:
        status = "failure"
    else:
        status = "inconclusive"

    return {
        "status": status,
        "before_ctr": before_ctr,
        "after_ctr": after_ctr,
        "before_impressions": before_impressions,
        "after_impressions": after_impressions,
        "ctr_lift": ctr_lift,
        "ctr_lift_pct": ctr_lift_pct,
        "position_adjusted_lift": position_adjusted_lift,
        "is_significant": significant,
    }
