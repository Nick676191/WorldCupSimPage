"""
Interactive World Cup 2026 probability explorer.

Loads the pre-computed simulation results and derives every probability on the
fly from light dataframe filtering. All the expensive Monte Carlo work happens
in simulate.py beforehand, so this app stays fast on Streamlit Community Cloud.

Run locally with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st
import altair as alt

import re
from pathlib import Path

STAGE_LABELS = {
    1: "Round of 32",
    2: "Round of 16",
    3: "Quarterfinal",
    4: "Semifinal",
    5: "Final",
    6: "Champion",
}

st.set_page_config(
    page_title="World Cup 2026 Probabilities", page_icon="⚽", layout="wide"
)


DATA_DIR = Path(__file__).parent / "data" / "results_01_pre-tournament.parquet"


@st.cache_data
def load_results(path: str = DATA_DIR) -> pd.DataFrame:
    # If you saved JSON instead: return pd.read_json(path, orient="records")
    return pd.read_parquet(path)


df = load_results()
n_sims = df["sim"].nunique()
teams = sorted(df["team"].cat.categories.tolist())

st.title("⚽ World Cup 2026 — Win Probabilities")
st.caption(f"Based on {n_sims:,} simulated tournaments.")

# ---- Sidebar: pick a team -------------------------------------------------
team = st.sidebar.selectbox("Choose a team", teams)
team_df = df[df["team"] == team]

# ---- Single-team headline numbers ----------------------------------------
win_wc = (team_df["furthest_stage"] == 6).mean()
win_group = (team_df["group_pos"] == 1).mean()
second_group = (team_df["group_pos"] == 2).mean()

c1, c2, c3 = st.columns(3)
c1.metric(f"{team} win the World Cup", f"{win_wc:.1%}")
c2.metric("Win their group", f"{win_group:.1%}")
c3.metric("Finish 2nd in group", f"{second_group:.1%}")

# ---- How far does this team go? ------------------------------------------
st.subheader(f"How far does {team} go?")
reach = {
    label: (team_df["furthest_stage"] >= stage).mean()
    for stage, label in STAGE_LABELS.items()
}
reach_df = pd.DataFrame({"stage": list(reach.keys()), "prob": list(reach.values())})
reach_df["prob"] = reach_df["prob"].astype(float)
reach_chart = (
    alt.Chart(reach_df)
    .mark_bar()
    .encode(
        x=alt.X("stage:N", sort="-y", title="Stage"),
        y=alt.Y("prob:Q", title="Chance of reaching", axis=alt.Axis(format="%")),
        tooltip=[
            alt.Tooltip("stage:N", title="Stage"),
            alt.Tooltip("prob:Q", title="Chance", format=".1%"),
        ],
    )
)
st.altair_chart(reach_chart, width="stretch")

# ---- A conditional probability example -----------------------------------
won_group = team_df[team_df["group_pos"] == 1]
if len(won_group):
    cond = (won_group["furthest_stage"] == 6).mean()
    st.info(
        f"If {team} win their group, their chance of winning the World Cup "
        f"becomes **{cond:.1%}** (vs **{win_wc:.1%}** overall)."
    )

st.divider()

# ---- Top 10 most likely champions ----------------------------------------
st.subheader("Top 10 most likely champions")
champ_df = (
    (df[df["furthest_stage"] == 6]["team"].value_counts().head(10) / n_sims)
    .rename_axis("team")
    .reset_index(name="prob")
)
champ_df["team"] = champ_df["team"].astype(str)
champ_df["prob"] = champ_df["prob"].astype(float)
champ_chart = (
    alt.Chart(champ_df)
    .mark_bar()
    .encode(
        x=alt.X("team:N", sort="-y", title="Team"),
        y=alt.Y("prob:Q", title="Win probability", axis=alt.Axis(format="%")),
        tooltip=[
            alt.Tooltip("team:N", title="Team"),
            alt.Tooltip("prob:Q", title="Win probability", format=".1%"),
        ],
    )
)
st.altair_chart(champ_chart, width="stretch")

# ---- Who reaches a chosen stage most often? ------------------------------
st.subheader("Who reaches each stage most often?")
stage_choice = st.selectbox(
    "Stage", list(STAGE_LABELS.values()), index=3  # default: Semifinal
)
stage_value = {v: k for k, v in STAGE_LABELS.items()}[stage_choice]
reach_tbl = (
    (df[df["furthest_stage"] >= stage_value]["team"].value_counts().head(15) / n_sims)
    .rename_axis("team")
    .reset_index(name="prob")
)
reach_tbl["team"] = reach_tbl["team"].astype(str)
reach_tbl["prob"] = reach_tbl["prob"].astype(float)
stage_chart = (
    alt.Chart(reach_tbl)
    .mark_bar()
    .encode(
        x=alt.X("team:N", sort="-y", title="Team"),
        y=alt.Y(
            "prob:Q",
            title=f"Chance of reaching the {stage_choice}",
            axis=alt.Axis(format="%"),
        ),
        tooltip=[
            alt.Tooltip("team:N", title="Team"),
            alt.Tooltip("prob:Q", title="Chance", format=".1%"),
        ],
    )
)
st.altair_chart(stage_chart, width="stretch")
