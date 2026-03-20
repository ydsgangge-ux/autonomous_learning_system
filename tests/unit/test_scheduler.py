import pytest
from planning.scheduler import sm2


def test_sm2_successful_recall():
    result = sm2(score=0.8, repetitions=0)
    assert result.interval_days == 1
    assert result.repetitions == 1
    assert result.ease_factor >= 2.5


def test_sm2_failed_recall():
    result = sm2(score=0.3, repetitions=5, interval_days=14)
    assert result.interval_days == 1
    assert result.repetitions == 0


def test_sm2_ease_factor_min():
    # Repeated failures should not drop ease below 1.3
    result = sm2(score=0.0, ease_factor=1.4)
    assert result.ease_factor >= 1.3


def test_sm2_growing_intervals():
    r1 = sm2(score=0.9, repetitions=1, interval_days=1)
    r2 = sm2(score=0.9, repetitions=r1.repetitions, interval_days=r1.interval_days, ease_factor=r1.ease_factor)
    assert r2.interval_days > r1.interval_days
