import pandas as pd
import plotly.express as px
import streamlit as st

from healthreport import export_reports, get_status, load_activities, sync_activities
from healthreport.exceptions import HealthReportError
from healthreport.ui_data import clean_activity_data, load_uploaded_data


st.set_page_config(
    page_title="HealthReport Strava App",
    page_icon="🚶",
    layout="wide",
)

st.title("HealthReport Strava App")


@st.cache_data(show_spinner=False)
def load_database_data(cache_key):
    return clean_activity_data(load_activities())


if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "data_source" not in st.session_state:
    st.session_state.data_source = "database"
if "last_action_message" not in st.session_state:
    st.session_state.last_action_message = None


with st.sidebar:
    st.header("Controls")

    status = get_status()
    st.metric("Activities", status["total_rows"])
    st.caption(f"Last sync: {status['last_sync'] or 'Never'}")
    st.caption(f"Last activity: {status['last_activity_date'] or 'N/A'}")

    if not status["tokens_configured"]:
        st.warning("Strava tokens are not configured yet.")

    if st.button("Sync Now", use_container_width=True):
        try:
            with st.spinner("Syncing Strava activities..."):
                result = sync_activities()
            st.cache_data.clear()
            st.session_state.data_source = "database"
            st.session_state.last_action_message = (
                f"Sync complete: {result.fetched_count} fetched, "
                f"{result.total_count} total activities."
            )
            st.rerun()
        except Exception as exc:
            st.session_state.last_action_message = f"Sync failed: {exc}"

    if st.button("Refresh Dashboard Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.data_source = "database"
        st.rerun()

    if st.button("Export CSV/XLSX", use_container_width=True):
        try:
            exported = export_reports()
            st.session_state.last_action_message = "Exported: " + ", ".join(str(path) for path in exported.values())
        except HealthReportError as exc:
            st.session_state.last_action_message = f"Export failed: {exc}"

    if st.session_state.last_action_message:
        if "failed" in st.session_state.last_action_message.lower():
            st.error(st.session_state.last_action_message)
        else:
            st.success(st.session_state.last_action_message)

    st.markdown("---")
    uploaded_file = st.file_uploader("Optional CSV override", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_df = load_uploaded_data(uploaded_file)
            st.session_state.data_source = "uploaded"
            st.success(f"Uploaded CSV loaded: {len(st.session_state.uploaded_df)} rows")
        except Exception as exc:
            st.error(f"Could not load uploaded CSV: {exc}")

    if st.session_state.uploaded_df is not None:
        use_uploaded = st.toggle("Use uploaded CSV", value=st.session_state.data_source == "uploaded")
        st.session_state.data_source = "uploaded" if use_uploaded else "database"

    show_all_sports = st.checkbox("Show all sport types", value=False)
    full_refresh = st.checkbox("Full refresh on next manual sync", value=False)
    if full_refresh and st.button("Run Full Refresh", use_container_width=True):
        try:
            with st.spinner("Running full Strava refresh..."):
                result = sync_activities(full_refresh=True)
            st.cache_data.clear()
            st.session_state.data_source = "database"
            st.session_state.last_action_message = (
                f"Full refresh complete: {result.fetched_count} fetched, "
                f"{result.total_count} total activities."
            )
            st.rerun()
        except Exception as exc:
            st.session_state.last_action_message = f"Full refresh failed: {exc}"


try:
    database_df = load_database_data(str(status["database_path"]) + str(status["last_sync"]) + str(status["total_rows"]))
except Exception as exc:
    st.error(f"Could not load synced data: {exc}")
    database_df = pd.DataFrame()

df = st.session_state.uploaded_df if st.session_state.data_source == "uploaded" else database_df

if not df.empty and not show_all_sports and "Sport Type" in df.columns:
    walking_mask = df["Sport Type"].astype(str).str.contains("walk", case=False, na=False)
    if walking_mask.any():
        df = df[walking_mask].reset_index(drop=True)

if df.empty:
    st.info("Click Sync Now in the sidebar, wait for the daily 11:00 AM sync, or upload a CSV override.")
else:
    latest_activity = df.iloc[-1]

    st.markdown("### Latest Activity Snapshot")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Distance", f"{latest_activity['Distance (km)']:.2f} km")
    col2.metric("Duration", f"{latest_activity['Duration (min)']:.1f} min")
    col3.metric("Avg Pace", f"{latest_activity['Avg Pace (min/km)']:.2f} min/km")
    col4.metric(
        "Avg HR",
        f"{latest_activity['Avg Heart Rate']:.0f} bpm"
        if pd.notna(latest_activity["Avg Heart Rate"])
        else "N/A",
    )
    col5.metric("Elevation", f"{latest_activity['Elevation Gain (m)']:.1f} m")

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Distance Over Time")
        fig_dist = px.bar(
            df,
            x="Date",
            y="Distance (km)",
            text_auto=".2f",
            color="Distance (km)",
            color_continuous_scale="blues",
        )
        fig_dist.update_traces(textposition="outside")
        fig_dist.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Distance (km)")
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_right:
        st.markdown("#### Heart Rate Trend")
        df_hr = df.melt(
            id_vars=["Date"],
            value_vars=["Avg Heart Rate", "Max Heart Rate"],
            var_name="HR Type",
            value_name="BPM",
        ).dropna(subset=["BPM"])
        fig_hr = px.line(
            df_hr,
            x="Date",
            y="BPM",
            color="HR Type",
            markers=True,
            color_discrete_map={"Avg Heart Rate": "blue", "Max Heart Rate": "red"},
        )
        fig_hr.update_layout(xaxis_title="", yaxis_title="Beats Per Minute")
        st.plotly_chart(fig_hr, use_container_width=True)

    with col_left:
        st.markdown("#### Pace vs Elevation Gain")
        fig_elev = px.scatter(
            df,
            x="Elevation Gain (m)",
            y="Avg Pace (min/km)",
            size="Distance (km)",
            hover_data=["Date"],
            color="Avg Heart Rate",
            color_continuous_scale="rdylgn_r",
        )
        fig_elev.update_layout(xaxis_title="Elevation Gain (m)", yaxis_title="Avg Pace (min/km)")
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_right:
        st.markdown("#### Moving vs Elapsed Time")
        df_time = df.melt(
            id_vars=["Date"],
            value_vars=["Duration (min)", "Elapsed Time (min)"],
            var_name="Time Type",
            value_name="Minutes",
        )
        fig_time = px.bar(
            df_time,
            x="Date",
            y="Minutes",
            color="Time Type",
            barmode="group",
            color_discrete_map={"Duration (min)": "teal", "Elapsed Time (min)": "lightblue"},
        )
        fig_time.update_layout(xaxis_title="", yaxis_title="Minutes")
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")
    with st.expander("View Raw Data Table"):
        st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
