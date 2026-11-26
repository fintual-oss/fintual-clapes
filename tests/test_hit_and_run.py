import ast
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

HIT_AND_RUN_DIR = Path(__file__).resolve().parent.parent / "02_hit_and_run"
sys.path.insert(0, str(HIT_AND_RUN_DIR))

from cvar_portfolio_sampler import CVaRPortfolioSampler  # noqa: E402


def test_default_curve_start_is_none_not_string_literal():
    """Regression: CURVE_START defaulted to 'None' (str), crashing all_curves.index('None')."""
    main_source = (HIT_AND_RUN_DIR / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(main_source)

    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("CURVE_START", "CURVE_END"):
                    assignments[target.id] = ast.literal_eval(node.value)

    assert assignments["CURVE_START"] is None
    assert assignments["CURVE_END"] is None


@pytest.mark.parametrize("method_name", ["generate_portfolios", "generate_portfolios_batch"])
def test_sampler_returns_exact_n_samples_when_some_segments_are_skipped(method_name):
    """Regression: skipped directions/segments used `continue` inside `for i in range(...)`,
    returning fewer than n_samples portfolios and leaving trailing NaN rows in weights_out."""
    rng = np.random.default_rng(123)
    returns = rng.normal(loc=0.006, scale=0.02, size=(300, 4))
    sampler = CVaRPortfolioSampler(returns=returns, confidence_level=0.10)

    original_find_segment = sampler._find_feasible_line_segment
    calls = {"count": 0}

    def flaky_find_segment(current_point, direction, target_cvar, tol=1e-8):
        calls["count"] += 1
        # Simulate every 3rd random direction producing a degenerate chord (t_max <= t_min)
        if calls["count"] % 3 == 0:
            return 0.0, 0.0
        return original_find_segment(current_point, direction, target_cvar, tol=tol)

    np.random.seed(42)
    with patch.object(sampler, "_find_feasible_line_segment", side_effect=flaky_find_segment):
        generate_fn = getattr(sampler, method_name)
        portfolios = generate_fn(target_cvar=0.10, n_samples=25, burn_in=5)

    assert portfolios.shape == (25, 4)
    assert not np.isnan(portfolios).any()
    assert np.allclose(portfolios.sum(axis=1), 1.0)
    assert (portfolios >= 0).all()
