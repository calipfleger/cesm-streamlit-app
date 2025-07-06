# app.py - Modular Streamlit App for CESM NetCDF Data

import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import seaborn as sns
from cesm_utils import (
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_correlation,
    get_summary_statistics
)

# --- App Config ---
st.set_page_config(
    page_title="Volcanic & Anthropogenic ENSO Signal Explorer",
    layout="wide",
)

st.title("Volcanic & Anthropogenic ENSO Signal Explorer")
st.markdown("""
This application visualizes CESM/iCESM output and indices (δ18Op, SST, SLP, w500, etc.)  
Supports GHG, aerosol, and full-forcing experiments. Publication-ready. Modular. Beginner-friendly.
""")

# --- Load NetCDF Dataset ---
data_dir = "data"
netcdf_files = [f for f in os.listdir(data_dir) if f.endswith(".nc")]

if not netcdf_files:
    st.warning("No NetCDF files found. Please upload or add one.")
    st.stop()

selected_file = st.sidebar.selectbox("Select NetCDF Dataset:", netcdf_files, key="dataset_select")
file_path = os.path.join(data_dir, selected_file)

try:
    ds = load_dataset(file_path)
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

variables = list(ds.data_vars)
time_dim = ds[variables[0]].dims[0]
times = ds[time_dim].values
time_slider = st.sidebar.slider("Select Time Range:", 0, len(times) - 1, (0, len(times) - 1))
selected_times = slice(times[time_slider[0]], times[time_slider[1]])

# --- Sidebar Options ---
selected_var = st.sidebar.selectbox("Select Variable:", variables, key="var_select")

# --- Tabs for Navigation ---
tab1, tab2, tab3 = st.tabs(["📈 Time Series", "🗺️ Spatial Map", "🔗 Correlation"])

with tab1:
    st.subheader("Time Series Plot")
    fig_ts, fig_ts_png = plot_timeseries(ds, selected_var, selected_times)
    st.pyplot(fig_ts)
    st.download_button("Download PNG", data=fig_ts_png, file_name="timeseries.png")

    stats = get_summary_statistics(ds, selected_var)
    st.write("Summary Statistics:", stats)

with tab2:
    st.subheader("Spatial Map")
    fig_map, fig_map_png = plot_spatial_map(ds, selected_var, selected_times)
    st.pyplot(fig_map)
    st.download_button("Download PNG", data=fig_map_png, file_name="map.png")

with tab3:
    st.subheader("Correlation Map")
    fig_corr, fig_corr_png = plot_correlation(ds, selected_var, selected_times)
    st.pyplot(fig_corr)
    st.download_button("Download PNG", data=fig_corr_png, file_name="correlation.png")

