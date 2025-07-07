# ---- app.py ----
"""
Streamlit front-end for CESM visual analytics (rev 2025-07-07-d).

Features
========
• File picker (local or remote download)
• Multi-index plots with ±1 σ shading & optional trendlines
• User-defined index boxes (lat/lon) that persist in session_state
• Journal presets (fonts, DPI, figsize)
• Colormap dropdown + color-bar modes (Auto / Robust / Symmetric / Manual [vmin/vmax])
• Toggle overlay of index boxes on maps
• Embedded captions with summary stats
"""

from __future__ import annotations

import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt

# --- local helpers -----------------------------------------------------------
from cesm_utils import (
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
)

# Optional: your existing remote downloader
try:
    from remote_data_fetcher import remote_fetch_workflow
except ImportError:
    def remote_fetch_workflow():
        st.sidebar.info("`remote_data_fetcher.py` not found – local files only.")

# --- page config -------------------------------------------------------------
st.set_page_config(page_title="CESM Streamlit Explorer", layout="wide")
st.title("CESM / iCESM Interactive Workbook")

# --- sidebar: data acquisition ----------------------------------------------
remote_fetch_workflow()   # shows download widget if implemented

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
nc_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".nc")]

if not nc_files:
    st.warning("No NetCDF files found. Use the sidebar to fetch one.")
    st.stop()

selected_file = st.sidebar.selectbox("🎛  NetCDF dataset", nc_files)
file_path = os.path.join(DATA_DIR, selected_file)


@st.cache_data(show_spinner=True)
def _load(path: str) -> xr.Dataset:
    return load_dataset(path)


ds = _load(file_path)

# --- sidebar: variable & indices --------------------------------------------
variables = list(ds.data_vars)
var = st.sidebar.selectbox("📄 Variable", variables)

# built-in + custom boxes
if "custom_boxes" not in st.session_state:
    st.session_state["custom_boxes"] = {}

# add custom box
with st.sidebar.expander("➕ Add custom index box"):
    name = st.text_input("Name (unique)", key="box_name")
    col1, col2 = st.columns(2)
    lat_min = col1.number_input("Lat min", value=-5.0, key="latmin")
    lat_max = col2.number_input("Lat max", value=5.0, key="latmax")
    lon_min = col1.number_input("Lon min", value=190.0, key="lonmin")
    lon_max = col2.number_input("Lon max", value=240.0, key="lonmax")
    if st.button("Add box"):
        if name and name not in BUILTIN_BOXES and name not in st.session_state["custom_boxes"]:
            st.session_state["custom_boxes"][name] = {
                "lat": (lat_min, lat_max),
                "lon": (lon_min, lon_max),
            }
        else:
            st.warning("Name must be unique and non-empty.")

# combined box dict
all_boxes = {**BUILTIN_BOXES, **st.session_state["custom_boxes"]}

index_options = ["Raw", "Global Mean"] + list(all_boxes.keys())
indices = st.sidebar.multiselect("📊 Indices", index_options, default=["Raw"])

# --- sidebar: plot options ---------------------------------------------------
trendline = st.sidebar.checkbox("Add trendline to time-series", value=False)

# colormap
cmap = st.sidebar.selectbox("🎨 Colormap", sorted(plt.colormaps()))

# color-bar mode
cbar_mode = st.sidebar.radio("Colorbar Mode", ["Auto", "Robust", "Symmetric", "Manual"])
vmin = vmax = None
if cbar_mode == "Manual":
    vmin = st.sidebar.number_input("vmin")
    vmax = st.sidebar.number_input("vmax")

show_boxes = st.sidebar.checkbox("Display index boxes on maps", value=True)

custom_caption = st.sidebar.text_area("Custom caption (optional)")

journal = st.sidebar.selectbox("Journal preset", list(JOURNAL_PRESETS.keys()))
preset = JOURNAL_PRESETS[journal]

# --- sidebar: time slider ----------------------------------------------------
time_vals = ds["time"].values
idx_min, idx_max = st.sidebar.slider(
    "Time range",
    0,
    len(time_vals) - 1,
    (0, len(time_vals) - 1),
    format="",
)
time_slice = slice(time_vals[idx_min], time_vals[idx_max])

# --- tabs --------------------------------------------------------------------
tab_ts, tab_map, tab_trend = st.tabs(["📈 Time-Series", "🗺 Spatial Map", "🔭 Trend Map"])

with tab_ts:
    fig, buf, cap = plot_timeseries(
        ds,
        var,
        indices,
        time_slice,
        preset,
        all_boxes,
        user_caption=custom_caption,
        show_trendline=trendline,
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, file_name="timeseries.png")
    st.caption(cap)

with tab_map:
    fig, buf, cap = plot_spatial_map(
        ds,
        var,
        time_slice,
        preset,
        cmap,
        indices,
        all_boxes,
        cbar_mode,
        vmin,
        vmax,
        show_boxes,
        user_caption=custom_caption,
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, file_name="spatial_map.png")
    st.caption(cap)

with tab_trend:
    fig, buf, cap = plot_trend_map(
        ds,
        var,
        time_slice,
        preset,
        cmap,
        indices,
        all_boxes,
        cbar_mode,
        vmin,
        vmax,
        show_boxes,
        user_caption=custom_caption,
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, file_name="trend_map.png")
    st.caption(cap)

