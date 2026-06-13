"""Unit tests for the returns loader / discovery boundary module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agent_graph_system.analysis import returns as rl


def _write_csv(path, *, level_col=False):
    idx = pd.bdate_range("2020-01-01", periods=10)
    if level_col:
        df = pd.DataFrame({"date": idx, "close": np.linspace(100, 110, 10)})
    else:
        df = pd.DataFrame({"date": idx, "return": np.full(10, 0.001)})
    path.write_text(df.to_csv(index=False))


def test_load_returns_from_return_column(tmp_path):
    p = tmp_path / "r.csv"
    _write_csv(p)
    s = rl.load_returns(p)
    assert isinstance(s, pd.Series)
    assert len(s) == 10
    assert np.allclose(s.values, 0.001)


def test_load_returns_derives_from_level_column(tmp_path):
    p = tmp_path / "r.csv"
    _write_csv(p, level_col=True)
    s = rl.load_returns(p)
    # pct_change drops the first row.
    assert len(s) == 9
    assert (s > 0).all()


def test_load_returns_rejects_columnless_csv(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError):
        rl.load_returns(p)


def test_discover_returns_finds_project_csv(tmp_path):
    proj = tmp_path / "MyStrat" / "data"
    proj.mkdir(parents=True)
    _write_csv(proj / "returns.csv")
    s = rl.discover_returns("MyStrat", roots=[tmp_path])
    assert s is not None and len(s) == 10


def test_discover_returns_none_when_absent(tmp_path):
    assert rl.discover_returns("Ghost", roots=[tmp_path]) is None


def test_discover_returns_swallows_bad_file(tmp_path):
    proj = tmp_path / "Broken"
    proj.mkdir()
    (proj / "returns.csv").write_text("a,b\n1,2\n")
    # A malformed artifact is treated as "unavailable", not an exception.
    assert rl.discover_returns("Broken", roots=[tmp_path]) is None


def test_default_search_roots_honours_env(tmp_path, monkeypatch):
    monkeypatch.setenv("WALKFORWARD_RETURNS_ROOT", str(tmp_path))
    assert rl.default_search_roots() == [tmp_path]
