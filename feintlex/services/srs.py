from __future__ import annotations

from datetime import timedelta

from feintlex.models import utc_now


REVIEW_INTERVAL_DAYS = [1, 3, 7, 14, 30]


def next_review_due(review_count: int):
    index = min(max(review_count - 1, 0), len(REVIEW_INTERVAL_DAYS) - 1)
    return utc_now() + timedelta(days=REVIEW_INTERVAL_DAYS[index])
