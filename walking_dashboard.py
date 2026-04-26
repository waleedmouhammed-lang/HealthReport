from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

from config import CSV_PATH


REQUIRED_COLUMNS = [
    "Date",
    "Distance (km)",
    "Duration (min)",
    "Elapsed Time (min)",
    "Avg Pace (min/km)",
    "Avg Heart Rate",
    "Max Heart Rate",
    "Elevation Gain (m)",
]


st.set_page_config(
    page_title="Walking Activity Dashboard",
    page_icon="🚶‍♂️",
    layout="wide",
)

st.title("🚶‍♂️ Outdoor Walking Dashboard")
st.markdown("Monitor your daily walking metrics, track progression, and optimize your training.")


def clean_activity_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    numeric_columns = [
        "Distance (km)",
        "Duration (min)",
        "Elapsed Time (min)",
        "Avg Pace (min/km)",
        "Avg Heart Rate",
        "Max Heart Rate",
        "Elevation Gain (m)",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Avg Heart Rate"] = df["Avg Heart Rate"].mask(df["Avg Heart Rate"].eq(0))
    df["Max Heart Rate"] = df["Max Heart Rate"].mask(df["Max Heart Rate"].eq(0))
    return df.sort_values(by="Date", ascending=True).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_synced_data(csv_path, modified_time):
    return clean_activity_data(pd.read_csv(csv_path))


def load_uploaded_data(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8-sig"))
    return clean_activity_data(pd.read_csv(stringio))


def synced_csv_mtime():
    return CSV_PATH.stat().st_mtime if CSV_PATH.exists() else None


if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

if "data_source" not in st.session_state:
    st.session_state.data_source = "synced"


with st.sidebar:
    st.header("Data Management")

    mtime = synced_csv_mtime()
    if mtime:
        synced_df = load_synced_data(str(CSV_PATH), mtime)
        st.success(f"Synced CSV loaded: {len(synced_df)} rows")
        st.caption(f"Last updated: {pd.to_datetime(mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        synced_df = pd.DataFrame()
        st.warning("No synced CSV found yet. Run the Strava sync first.")

    if st.button("Reload synced data", width="stretch"):
        st.cache_data.clear()
        st.session_state.data_source = "synced"
        st.rerun()

    uploaded_file = st.file_uploader("Optional CSV override", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_df = load_uploaded_data(uploaded_file)
            st.session_state.data_source = "uploaded"
            st.success(f"Uploaded CSV loaded: {len(st.session_state.uploaded_df)} rows")
        except Exception as exc:
            st.error(f"Could not load uploaded CSV: {exc}")

    if st.session_state.uploaded_df is not None:
        use_uploaded = st.toggle(
            "Use uploaded CSV",
            value=st.session_state.data_source == "uploaded",
        )
        st.session_state.data_source = "uploaded" if use_uploaded else "synced"

    st.markdown("---")
    show_all_sports = st.checkbox("Show all sport types", value=False)


df = (
    st.session_state.uploaded_df
    if st.session_state.data_source == "uploaded"
    else synced_df
)

if not df.empty and not show_all_sports and "Sport Type" in df.columns:
    walking_mask = df["Sport Type"].astype(str).str.contains("walk", case=False, na=False)
    if walking_mask.any():
        df = df[walking_mask].reset_index(drop=True)


if df.empty:
    st.info("Run the Strava sync or upload a CSV from the sidebar to populate the dashboard.")
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
        fig_dist.update_layout(
            coloraxis_showscale=False,
            xaxis_title="",
            yaxis_title="Distance (km)",
        )
        st.plotly_chart(fig_dist, width="stretch")

    with col_right:
        st.markdown("#### Heart Rate Trend")
        df_hr = df.melt(
            id_vars=["Date"],
            value_vars=["Avg Heart Rate", "Max Heart Rate"],
            var_name="HR Type",
            value_name="BPM",
        )
        df_hr = df_hr.dropna(subset=["BPM"])
        fig_hr = px.line(
            df_hr,
            x="Date",
            y="BPM",
            color="HR Type",
            markers=True,
            color_discrete_map={"Avg Heart Rate": "blue", "Max Heart Rate": "red"},
        )
        fig_hr.update_layout(xaxis_title="", yaxis_title="Beats Per Minute")
        st.plotly_chart(fig_hr, width="stretch")

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
        fig_elev.update_layout(
            xaxis_title="Elevation Gain (m)",
            yaxis_title="Avg Pace (min/km)",
        )
        st.plotly_chart(fig_elev, width="stretch")

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
            color_discrete_map={
                "Duration (min)": "teal",
                "Elapsed Time (min)": "lightblue",
            },
        )
        fig_time.update_layout(xaxis_title="", yaxis_title="Minutes")
        st.plotly_chart(fig_time, width="stretch")

    st.markdown("---")

    with st.expander("View Raw Data Table"):
        st.dataframe(df.sort_values(by="Date", ascending=False), width="stretch")
