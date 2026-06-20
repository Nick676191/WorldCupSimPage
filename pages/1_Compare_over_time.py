"""
Comparison page: how the probabilities shift across the tournament.

Place this file at  pages/1_Compare_over_time.py  in your repo. Streamlit
automatically adds anything in `pages/` to the sidebar navigation, so this
shows up next to your existing home page with no extra wiring.

Two views:
  1. One team tracked across snapshots, on whichever metrics you choose.
  2. Several teams compared across snapshots, on a single metric.
"""

import streamlit as st
import altair as alt

from data_loader import METRIC_LABELS, load_snapshots, team_probabilities

st.set_page_config(page_title="Compare over time", page_icon="📈", layout="wide")
st.title("📈 How chances have shifted")

combined = load_snapshots()
probs = team_probabilities(combined)

teams = sorted(probs["team"].astype(str).unique().tolist())
snapshots_in_order = (
    probs[["order", "snapshot"]]
    .drop_duplicates()
    .sort_values("order")["snapshot"]
    .astype(str)
    .tolist()
)
st.caption(f"{len(snapshots_in_order)} snapshots: " + "  →  ".join(snapshots_in_order))

if len(snapshots_in_order) < 2:
    st.warning(
        "Only one snapshot so far. Add a second simulation file to `data/` "
        "to see how the numbers move over time."
    )

# --------------------------------------------------------------------------
# View 1: one team, several metrics
# --------------------------------------------------------------------------
st.subheader("One team across the tournament")

team = st.selectbox("Team", teams)
chosen = st.multiselect(
    "Metrics to track",
    options=list(METRIC_LABELS.keys()),
    default=["win_group", "reach_sf", "champion"],
    format_func=lambda key: METRIC_LABELS[key],
)

if chosen:
    one = probs[probs["team"].astype(str) == team].sort_values("order").copy()
    one["Snapshot"] = one["snapshot"].astype(str)
    snapshot_order = one["Snapshot"].tolist()  # chronological

    long = one.melt(
        id_vars=["Snapshot"],
        value_vars=chosen,
        var_name="metric_key",
        value_name="prob",
    )
    long["Metric"] = long["metric_key"].map(METRIC_LABELS)
 
    line = (
        alt.Chart(long)
        .mark_line(point=True)
        .encode(
            x=alt.X("Snapshot:N", sort=snapshot_order, title="Snapshot"),
            y=alt.Y("prob:Q", title="Probability", axis=alt.Axis(format="%")),
            color=alt.Color("Metric:N", title="Metric"),
            tooltip=["Snapshot", "Metric", alt.Tooltip("prob:Q", format=".1%")],
        )
    )
    st.altair_chart(line, use_container_width=True)
 
    # Same numbers as a percentage table.
    table = one.set_index("Snapshot")[chosen].rename(columns=METRIC_LABELS)
    for col in table.columns:
        table[col] = (table[col] * 100).round(1).astype(str) + "%"
    st.dataframe(table, use_container_width=True)
else:
    st.info("Pick at least one metric to plot.")
 
st.divider()

    # chart_df = one.set_index("Snapshot")[chosen].rename(columns=METRIC_LABELS)

    # st.line_chart(chart_df)

    # # Show the same numbers as a percentage table.
    # table = chart_df.copy()
    # for col in table.columns:
    #     table[col] = (table[col] * 100).round(1).astype(str) + "%"
    # st.dataframe(table, use_container_width=True)
# else:
#     st.info("Pick at least one metric to plot.")

# st.divider()

# --------------------------------------------------------------------------
# View 2: several teams, one metric
# --------------------------------------------------------------------------
st.subheader("Compare teams on one metric")

metric = st.selectbox(
    "Metric",
    options=list(METRIC_LABELS.keys()),
    index=list(METRIC_LABELS.keys()).index("champion"),
    format_func=lambda key: METRIC_LABELS[key],
    key="multi_metric",
)

# Default to the current front-runners on this metric (latest snapshot).
latest_order = probs["order"].max()
default_teams = (
    probs[probs["order"] == latest_order]
    .nlargest(5, metric)["team"]
    .astype(str)
    .tolist()
)
picked = st.multiselect("Teams", teams, default=default_teams, key="multi_teams")

if picked:
    sub = probs[probs["team"].astype(str).isin(picked)].sort_values("order").copy()
    sub["Snapshot"] = sub["snapshot"].astype(str)
    sub["team"] = sub["team"].astype(str)

    line = (
        alt.Chart(sub)
        .mark_line(point=True)
        .encode(
            x=alt.X("Snapshot:N", sort=snapshots_in_order, title="Snapshot"),
            y=alt.Y(f"{metric}:Q", title=METRIC_LABELS[metric], axis=alt.Axis(format="%")),
            color=alt.Color("Team:N", title="Team"),
            tooltip=["Snapshot", "Team", alt.Tooltip(f"{metric}:Q", format=".1%")],
        )
    )
    st.altair_chart(line, use_container_width=True)
    st.caption(f"Showing: {METRIC_LABELS[metric]}")

    # wide = sub.pivot_table(
    #     index="Snapshot", columns="team", values=metric, observed=True
    # ).reindex(snapshots_in_order)

    # st.line_chart(wide)
    # st.caption(f"Showing: {METRIC_LABELS[metric]}")
else:
    st.info("Pick at least one team to compare.")
