"""Opportunity identification for SEO CTR optimization."""

import pandas as pd


def get_baseline_ctr(position: float) -> float:
    """Return industry baseline CTR for a given position.

    Based on 2024 CTR curve research:
    Position 1: 39.8%, Position 2: 18.7%, Position 3: 10.2%, etc.
    """
    # CTR curve (position -> baseline CTR)
    baseline_map = {
        1: 0.398,
        2: 0.187,
        3: 0.102,
        4: 0.074,
        5: 0.058,
        6: 0.048,
        7: 0.041,
        8: 0.035,
        9: 0.031,
        10: 0.027,
        11: 0.024,
        12: 0.021,
        13: 0.019,
        14: 0.017,
        15: 0.015,
    }

    # Round position to nearest integer
    pos_int = round(position)

    # Clamp to range
    if pos_int < 1:
        pos_int = 1
    elif pos_int > 15:
        pos_int = 15

    return baseline_map[pos_int]


def calculate_opportunity_score(
    impressions: int, actual_ctr: float, expected_ctr: float
) -> float:
    """Calculate opportunity score.

    Score = impressions * (expected_ctr - actual_ctr)

    Higher score = more traffic potential from CTR improvement.
    """
    ctr_gap = max(0, expected_ctr - actual_ctr)
    return impressions * ctr_gap


def identify_opportunities(
    df: pd.DataFrame,
    min_impressions: int = 200,
    ctr_threshold: float = 0.8,
    position_range: tuple[int, int] = (4, 15),
    top_n: int = 20,
) -> list[dict]:
    """Identify top opportunities from GSC data.

    Args:
        df: GSC DataFrame with columns: query, page, position, clicks, impressions, ctr
        min_impressions: Minimum impressions to consider
        ctr_threshold: CTR must be < baseline * threshold (e.g., 0.8 = 80% of baseline)
        position_range: (min_pos, max_pos) to consider
        top_n: Number of top opportunities to return

    Returns:
        List of opportunity dicts sorted by opportunity_score descending
    """
    if df.empty:
        return []

    # Aggregate by (page, query) — sum impressions/clicks, avg position
    agg = (
        df.groupby(["page", "query"])
        .agg({"impressions": "sum", "clicks": "sum", "position": "mean"})
        .reset_index()
    )

    # Filter out garbage queries (operator queries, URLs-as-queries)
    agg = agg[~agg["query"].str.startswith("site:")]
    agg = agg[~agg["query"].str.contains(r"https?\s*[:：/]", regex=True)]

    # Calculate CTR
    agg["ctr"] = agg["clicks"] / agg["impressions"]

    # Filter by position range
    min_pos, max_pos = position_range
    agg = agg[(agg["position"] >= min_pos) & (agg["position"] <= max_pos)]

    # Filter by min impressions
    agg = agg[agg["impressions"] >= min_impressions]

    # Calculate baseline CTR
    agg["baseline_ctr"] = agg["position"].apply(get_baseline_ctr)

    # Filter by CTR threshold
    agg = agg[agg["ctr"] < agg["baseline_ctr"] * ctr_threshold]

    # Calculate opportunity score
    agg["opportunity_score"] = agg.apply(
        lambda row: calculate_opportunity_score(
            row["impressions"], row["ctr"], row["baseline_ctr"]
        ),
        axis=1,
    )

    # Sort by opportunity score descending
    agg = agg.sort_values("opportunity_score", ascending=False)

    # Return top N as list of dicts
    opportunities = []
    for _, row in agg.head(top_n).iterrows():
        opportunities.append(
            {
                "page": row["page"],
                "query": row["query"],
                "position": row["position"],
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "ctr": row["ctr"],
                "baseline_ctr": row["baseline_ctr"],
                "opportunity_score": row["opportunity_score"],
            }
        )

    return opportunities
