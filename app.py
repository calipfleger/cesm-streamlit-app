# -*- coding: utf-8 -*-
"""
CESM Streamlit App - Complete cftime Solution
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cftime
from cesm_utils import (
    load_dataset,
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    DIFF_BOXES,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
    compute_index
)

# App configuration
st.set_page_config(
    page_title="🌍 CESM Analysis Toolkit",
    layout="wide",
    initial_sidebar_state="expanded"
)

def handle_cesm_time(ds):
    """Robust time handling for CESM data with cftime support"""
    if isinstance(ds.time.values[0], cftime.datetime):
        # Convert cftime to pandas datetime for display
        time_values = ds.time.values
        time_display = pd.to_datetime([f"{t.year}-{t.month:02d}-{t.day:02d}" 
                                     for t in time_values])
        
        def get_slice(start_dt, end_dt):
            # Convert back to cftime for selection
            start_cf = cftime.DatetimeNoLeap(start_dt.year, start_dt.month, start_dt.day)
            end_cf = cftime.DatetimeNoLeap(end_dt.year, end_dt.month, end_dt.day)
            return ds.time.sel(time=slice(start_cf, end_cf))
            
        return time_display, get_slice
    else:
        # Regular datetime handling
        time_values = pd.to_datetime(ds.time.values)
        def get_slice(start_dt, end_dt):
            return ds.time.sel(time=slice(start_dt, end_dt))
        return time_values, get_slice

# Data loading
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

@st.cache_data(show_spinner="Loading dataset...")
def cached_load(path: str):
    """Cached dataset loader"""
    return load_dataset(path)

# Sidebar controls
with st.sidebar:
    st.header("Data Selection")
    data_files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.nc', '.nc4'))]
    if not data_files:
        st.error("No NetCDF files found in data directory")
        st.stop()
    
    selected_file = st.selectbox("Select NetCDF File", data_files)
    try:
        ds = cached_load(os.path.join(DATA_DIR, selected_file))
        time_display, get_slice = handle_cesm_time(ds)
        
        selected_start, selected_end = st.select_slider(
            "Select Time Period",
            options=time_display,
            value=(time_display[0], time_display[-1]),
            format="YYYY-MM-DD"
        )
        time_slice = get_slice(selected_start, selected_end)
        
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        st.stop()
    
    st.header("Variable Selection")
    available_vars = list(ds.data_vars)
    variable = st.selectbox("Select Variable", available_vars)

    st.header("Visualization Settings")
    journal_style = st.selectbox("Journal Style", list(JOURNAL_PRESETS.keys()))
    preset = JOURNAL_PRESETS[journal_style]
    
    colormap = st.selectbox(
        "Colormap", 
        sorted(plt.colormaps()),
        index=sorted(plt.colormaps()).index("viridis"))
    show_boxes = st.checkbox("Show Region Boxes", True)

# Main tabs
tab1, tab2, tab3 = st.tabs(["📈 Time Series", "🗺 Spatial Maps", "📊 Trend Analysis"])

with tab1:
    st.header(f"Time Series: {variable}")
    selected_indices = st.multiselect(
        "Select Indices",
        ["Raw", "Global Mean"] + list(BUILTIN_BOXES.keys()),
        default=["Raw"])
    show_trend = st.checkbox("Show Trend Line", True)
    
    if selected_indices:
        fig, buf, stats = plot_timeseries(
            ds,
            variable,
            selected_indices,
            time_slice,
            preset,
            {**BUILTIN_BOXES, **DIFF_BOXES},
            show_trend=show_trend)
        st.pyplot(fig)
        st.download_button(
            "Download Figure",
            buf,
            file_name=f"{variable}_timeseries.png",
            mime="image/png")

with tab2:
    st.header(f"Spatial Maps: {variable}")
    fig, buf, cap = plot_spatial_map(
        ds,
        variable,
        time_slice,
        preset,
        colormap,
        selected_indices if 'selected_indices' in locals() else ["Raw"],
        {**BUILTIN_BOXES, **DIFF_BOXES},
        show_boxes=show_boxes)
    st.pyplot(fig)
    st.download_button(
        "Download Map",
        buf,
        file_name=f"{variable}_spatial_map.png",
        mime="image/png")

with tab3:
    st.header(f"Trend Analysis: {variable}")
    fig, buf, cap = plot_trend_map(
        ds,
        variable,
        time_slice,
        preset,
        colormap,
        selected_indices if 'selected_indices' in locals() else ["Raw"],
        {**BUILTIN_BOXES, **DIFF_BOXES},
        show_boxes=show_boxes)
    st.pyplot(fig)
    st.download_button(
        "Download Trend Map",
        buf,
        file_name=f"{variable}_trend_map.png",
        mime="image/png")
