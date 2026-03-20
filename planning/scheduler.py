"""
Scheduler using SM-2 spaced repetition algorithm.
Calculates next review dates based on performance scores.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class SM2Result:
    interval_days: int
    repetitions: int
    ease_factor: float
    next_review_at: datetime


def sm2(
    score: float,           # 0.0 - 1.0 (quality of recall)
    repetitions: int = 0,   # number of successful reviews
    ease_factor: float = 2.5,
    interval_days: int = 1,
) -> SM2Result:
    """
    SM-2 algorithm for spaced repetition.
    score >= 0.6 = successful recall.
    """
    q = round(score * 5)  # convert to 0-5 scale

    if q >= 3:  # successful recall
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval_days * ease_factor)
        new_ease = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ease = max(1.3, new_ease)
        new_repetitions = repetitions + 1
    else:
        # Failed — reset
        new_interval = 1
        new_repetitions = 0
        new_ease = ease_factor

    next_review = datetime.utcnow() + timedelta(days=new_interval)
    return SM2Result(
        interval_days=new_interval,
        repetitions=new_repetitions,
        ease_factor=round(new_ease, 3),
        next_review_at=next_review,
    )


def sort_by_priority(tasks: list[dict]) -> list[dict]:
    """
    Sort learning tasks by urgency:
    - Overdue reviews first
    - Then by priority score (higher = more urgent)
    """
    now = datetime.utcnow()

    def urgency(t: dict) -> float:
        score = t.get("priority", 5)
        scheduled = t.get("scheduled_at")
        if scheduled and scheduled < now:
            overdue_days = (now - scheduled).days
            score += overdue_days * 2
        return -score  # negative for descending sort

    return sorted(tasks, key=urgency)
