# ---- app.py ----
"""Streamlit front‑end for CESM visual analytics."""

import os
import streamlit as st
import xarray as xr
from cesm_utils import (
    JOURNAL_PRESETS,
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
    plot_correlation,
)
from remote_data_fetcher import remote_fetch_workflow

# -----------------------------------------------------------------------------
st.set_page_config(page_title="CESM Streamlit Explorer", layout="wide")
st.title("Volcanic & Anthropogenic ENSO Signal Explorer")

st.markdown(
    """
    *Interactive visual analytics for CESM/iCESM NetCDF output.*
    """
)

# Sidebar – data acquisition --------------------------------------------------
remote_fetch_workflow()

data_dir = "data"
netcdf_files = [f for f in os.listdir(data_dir) if f.endswith(".nc")]

if not netcdf_files:
    st.warning("No NetCDF files found. Use the sidebar to download one.")
    st.stop()

selected_file = st.sidebar.selectbox("Select NetCDF Dataset:", netcdf_files)
file_path = os.path.join(data_dir, selected_file)

@st.cache_data(show_spinner=True)
def _load(path: str) -> xr.Dataset:
    return load_dataset(path)

ds = _load(file_path)

variables = list(ds.data_vars)
selected_var = st.sidebar.selectbox("Variable:", variables)

# Index selector
INDEX_OPTIONS = ["Raw", "Global Mean", "Nino3.4"]
selected_index = st.sidebar.selectbox("Index:", INDEX_OPTIONS)

# Journal presets
journal = st.sidebar.selectbox(
    "Journal Target (affects DPI / size):", list(JOURNAL_PRESETS.keys())
)
preset = JOURNAL_PRESETS[journal]

# Time slider
time_dim = ds[selected_var].dims[0]
times = ds[time_dim].values
time_slider = st.sidebar.slider(
    "Time Range:",
    0,
    len(times) - 1,
    (0, len(times) - 1),
    format="",
)
time_slice = slice(times[time_slider[0]], times[time_slider[1]])

# Tabs -----------------------------------------------------------------------

tab_ts, tab_map, tab_trend, tab_corr = st.tabs(
    ["📈 Time Series", "🗺️ Spatial Map", "🔭 Trend Map", "🔗 Correlation"]
)

with tab_ts:
    fig_ts, buf_ts, cap_ts = plot_timeseries(
        ds, selected_var, selected_index, time_slice, preset
    )
    st.pyplot(fig_ts)
    st.download_button("Download PNG", data=buf_ts, file_name="timeseries.png")
    st.caption(cap_ts)

with tab_map:
    try:
        fig_map, buf_map, cap_map = plot_spatial_map(
            ds, selected_var, time_slice, preset
        )
        st.pyplot(fig_map)
        st.download_button("Download PNG", data=buf_map, file_name="spatial.png")
        st.caption(cap_map)
    except Exception as e:
        st.info(f"Spatial map not available: {e}")

with tab_trend:
    try:
        fig_trend, buf_trend, cap_trend = plot_trend_map(
            ds, selected_var, time_slice, preset
        )
        st.pyplot(fig_trend)
        st.download_button("Download PNG", data=buf_trend, file_name="trend.png")
        st.caption(cap_trend)
    except Exception as e:
        st.info(f"Trend map not available: {e}")

with tab_corr:
    fig_corr, buf_corr, cap_corr = plot_correlation(
        ds, selected_var, time_slice, preset
    )
    st.pyplot(fig_corr)
    st.download_button("Download PNG", data=buf_corr, file_name="correlation.png")
    st.caption(cap_corr)

