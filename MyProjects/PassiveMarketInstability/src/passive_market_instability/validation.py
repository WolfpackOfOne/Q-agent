"""Small validation helpers used by the notebook."""

from __future__ import annotations

import pandas as pd


def check_status(condition):
    """Return the notebook's pass/fail status string."""
    return "pass" if bool(condition) else "fail"


def make_check(check_name, condition, details):
    """Build one row for the notebook sanity-check summary table."""
    return {
        "check_name": check_name,
        "status": check_status(condition),
        "details": details,
    }


def checks_to_frame(checks):
    """Convert a list of sanity-check dictionaries to a DataFrame."""
    return pd.DataFrame(checks, columns=["check_name", "status", "details"])
