import numpy as np

from passive_market_instability.passive_share import (
    build_passive_share_scenarios,
    logistic_passive_share,
)


def test_logistic_passive_share_returns_half_at_t0():
    assert logistic_passive_share(30.0, alpha=0.106, t0=30.0) == 0.5


def test_passive_share_is_bounded_between_zero_and_one():
    values = logistic_passive_share(np.arange(0, 61), alpha=0.106, t0=30.0)
    assert np.all(values >= 0.0)
    assert np.all(values <= 1.0)


def test_passive_share_increases_with_t():
    values = logistic_passive_share(np.array([0.0, 30.0, 60.0]), alpha=0.106, t0=30.0)
    assert values[0] < values[1] < values[2]


def test_build_passive_share_scenarios_includes_expected_scenarios():
    df = build_passive_share_scenarios(np.arange(0, 3))
    assert set(df["scenario"]) == {
        "no_passive",
        "haddad_baseline",
        "brightman_harvey",
        "conservative",
        "aggressive",
    }
