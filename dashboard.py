import streamlit as st
import pandas as pd
from db_setup import get_db
from crud import get_events, create_event
from pipelines import (
    country_severity_stats,
    monthly_escalation_trend,
    source_reliability_ranking,
    get_actor_alliance_chain,
)

st.set_page_config(page_title="Geopolitical Events Tracker", layout="wide")
db = get_db()

st.title("Geopolitical Events Tracker")

# --- SIDEBAR: FILTERS & ADD EVENT ---
st.sidebar.header("Filters")
countries = ["All"] + sorted(db.events.distinct("location.country"))
selected_country = st.sidebar.selectbox("Country", countries)
min_sev = st.sidebar.slider("Minimum Severity", 1, 10, 1)

st.sidebar.divider()
st.sidebar.header("Add New Event")
with st.sidebar.form("add_event_form"):
    ev_date = st.date_input("Date")
    ev_country = st.text_input("Country", "India")
    ev_region = st.text_input("Region", "South Asia")
    ev_type = st.selectbox("Type", ["conflict", "sanction", "diplomacy", "protest", "election"])
    ev_sev = st.slider("Severity", 1, 10, 5)
    ev_actors = st.multiselect("Actors", db.actors.distinct("_id"), default=["IND"])
    ev_source = st.selectbox("Source", db.sources.distinct("_id"))
    ev_summary = st.text_input("Summary")
    submitted = st.form_submit_button("Add Event")

    if submitted:
        try:
            create_event(
                db,
                ev_date.strftime("%Y-%m-%d"),
                ev_country,
                ev_region,
                ev_type,
                ev_sev,
                ev_actors,
                ev_source,
                ev_summary,
                status="verified",
            )
            st.sidebar.success("Event added!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(str(e))

# --- DATA FETCHING ---
country_filter = None if selected_country == "All" else selected_country
events = get_events(db, country=country_filter, min_sev=min_sev, limit=100)

# --- TOP METRICS ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Events", len(events))
avg_sev = round(sum(e["severity"] for e in events) / len(events), 1) if events else 0
col2.metric("Avg Severity", f"{avg_sev} / 10")
col3.metric("Tracked Actors", db.actors.count_documents({}))

st.divider()

# --- CHARTS (AGGREGATION PIPELINES) ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Events by Country")
    country_data = pd.DataFrame(country_severity_stats(db))
    if not country_data.empty:
        country_data = country_data.rename(columns={"_id": "Country", "total_events": "Events"})
        st.bar_chart(country_data.set_index("Country")["Events"])

with c2:
    st.subheader("Monthly Trend")
    trend_data = pd.DataFrame(monthly_escalation_trend(db))
    if not trend_data.empty:
        trend_data = trend_data.rename(columns={"_id": "Month", "avg_severity": "Avg Severity"})
        st.line_chart(trend_data.set_index("Month")["Avg Severity"])

st.divider()

# --- SECOND ROW: SOURCE RELIABILITY & ALLIANCE NETWORK ---
c3, c4 = st.columns(2)

with c3:
    st.subheader("Source Reliability Ranking")
    src_data = pd.DataFrame(source_reliability_ranking(db))
    if not src_data.empty:
        st.dataframe(
            src_data[["source_name", "credibility", "reports_count"]],
            use_container_width=True,
            hide_index=True,
        )

with c4:
    st.subheader("Actor Alliance Chain")
    actor_choice = st.selectbox("Select Actor", sorted(db.actors.distinct("_id")))
    chain = get_actor_alliance_chain(db, actor_choice)
    if chain and chain[0].get("alliance_network"):
        net_df = pd.DataFrame(chain[0]["alliance_network"])[["_id", "name", "region", "chain_level"]]
        st.dataframe(net_df, use_container_width=True, hide_index=True)
    else:
        st.info("No alliance network found.")

st.divider()

# --- BOTTOM TABLE: RECENT EVENTS ---
st.subheader("Recent Events")
if events:
    table_rows = [
        {
            "Date": e["date"].strftime("%Y-%m-%d"),
            "Country": e["location"]["country"],
            "Type": e["type"],
            "Severity": e["severity"],
            "Actors": ", ".join(e["actors_involved"]),
            "Source": e["source_id"],
            "Summary": e["summary"],
        }
        for e in events
    ]
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
else:
    st.warning("No events match the selected filters.")













from ml_model import get_ml_conflict_clusters

st.divider()
st.subheader("Machine Learning Insights: Conflict Risk Clustering (K-Means)")
ml_data = get_ml_conflict_clusters(db)
if ml_data is not None and not ml_data.empty:
    st.dataframe(ml_data[["country", "total_severity", "event_count", "risk_level"]], use_container_width=True, hide_index=True)
else:
    st.info("Not enough data for clustering.")