"""
Shared helpers for the comparison feature.

Loads every snapshot parquet from the `data/` folder, stacks them into one
dataframe with a `snapshot` column, and derives each team's probabilities per
snapshot. Both the home page and the comparison page can import from here.

Snapshot files must be named:  data/results_<order>_<label>.parquet
e.g.  data/results_01_pre-tournament.parquet
      data/results_02_after-matchday-1.parquet
"""

import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
_FILENAME_RE = re.compile(r"results_(\d+)_(.+)\.parquet$")

# Boolean/threshold definitions for each metric, computed from the stored schema.
METRIC_LABELS = {
    "win_group": "Win group",
    "second": "Finish 2nd in group",
    "reach_r32": "Reach Round of 32",
    "reach_r16": "Reach Round of 16",
    "reach_qf": "Reach Quarterfinal",
    "reach_sf": "Reach Semifinal",
    "reach_final": "Reach Final",
    "champion": "Win World Cup",
}


def _parse_snapshot(path: Path):
    match = _FILENAME_RE.search(path.name)
    if match is None:
        return None
    order = int(match.group(1))
    label = match.group(2).replace("-", " ").replace("_", " ").strip().title()
    return order, label


@st.cache_data
def load_snapshots() -> pd.DataFrame:
    """Stack every snapshot into one long dataframe with a `snapshot` column."""
    frames = []
    for path in sorted(DATA_DIR.glob("results_*.parquet")):
        parsed = _parse_snapshot(path)
        if parsed is None:
            continue
        order, label = parsed
        df = pd.read_parquet(path)
        df["order"] = order
        df["snapshot"] = label
        frames.append(df)

    if not frames:
        raise FileNotFoundError(
            f"No snapshot files found in {DATA_DIR}. Expected files like "
            "data/results_01_pre-tournament.parquet"
        )

    combined = pd.concat(frames, ignore_index=True)

    # Make `snapshot` an ordered category so charts read left-to-right in time.
    ordered_labels = (
        combined[["order", "snapshot"]]
        .drop_duplicates()
        .sort_values("order")["snapshot"]
        .tolist()
    )
    combined["snapshot"] = pd.Categorical(
        combined["snapshot"], categories=ordered_labels, ordered=True
    )
    return combined


@st.cache_data
def team_probabilities(combined: pd.DataFrame) -> pd.DataFrame:
    """One row per (snapshot, team); one column per metric in METRIC_LABELS."""
    flags = combined.assign(
        win_group=combined["group_pos"].eq(1),
        second=combined["group_pos"].eq(2),
        reach_r32=combined["furthest_stage"].ge(1),
        reach_r16=combined["furthest_stage"].ge(2),
        reach_qf=combined["furthest_stage"].ge(3),
        reach_sf=combined["furthest_stage"].ge(4),
        reach_final=combined["furthest_stage"].ge(5),
        champion=combined["furthest_stage"].eq(6),
    )
    metric_cols = list(METRIC_LABELS.keys())
    probs = (
        flags.groupby(["order", "snapshot", "team"], observed=True)[metric_cols]
        .mean()
        .reset_index()
    )
    return probs
