# -*- coding: utf-8 -*-
"""
CESM Streamlit App - Complete Working Version
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from cesm_utils import (
    load_dataset,
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    DIFF_BOXES,
    plot_timeseries,
    plot_spatial_map
)

# App configuration
st.set_page_config(
    page_title="CESM Analysis Toolkit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🌍 CESM Climate Data Analysis")
st.markdown("""
    Interactive visualization of CESM model outputs with publication-quality figures.
    Load NetCDF files from the `data` directory.
""")

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
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        st.stop()
    
    st.header("Variable Selection")
    available_vars = list(ds.data_vars)
    if not available_vars:
        st.error("No variables found in dataset")
        st.stop()
    variable = st.selectbox("Select Variable", available_vars)
    
    st.header("Time Period")
    try:
        # Convert numpy datetime64 to Python datetime objects for Streamlit
        time_values = [pd.Timestamp(t).to_pydatetime() for t in ds.time.values]
        time_range = st.slider(
            "Select Analysis Period",
            min_value=time_values[0],
            max_value=time_values[-1],
            value=(time_values[0], time_values[-1]),
            format="YYYY-MM-DD"
        )
        # Convert back to numpy datetime64 for the slice
        time_slice = slice(
            np.datetime64(time_range[0]),
            np.datetime64(time_range[1])
        )
    except Exception as e:
        st.error(f"Error processing time values: {str(e)}")
        st.stop()

    st.header("Visualization Settings")
    journal_style = st.selectbox("Journal Style", list(JOURNAL_PRESETS.keys()))
    preset = JOURNAL_PRESETS[journal_style]
    
    st.subheader("Map Settings")
    colormap = st.selectbox(
        "Colormap", 
        sorted(plt.colormaps()),
        index=sorted(plt.colormaps()).index("viridis")
    )
    show_boxes = st.checkbox("Show Region Boxes", True)

# Main tabs
tab1, tab2 = st.tabs(["Time Series", "Spatial Maps"])

with tab1:
    st.header(f"Time Series: {variable}")
    selected_indices = st.multiselect(
        "Select Indices",
        ["Raw", "Global Mean"] + list(BUILTIN_BOXES.keys()),
        default=["Raw"]
    )
    show_trend = st.checkbox("Show Trend Line", True)
    
    if selected_indices:
        try:
            fig, buf, _ = plot_timeseries(
                ds,
                variable,
                selected_indices,
                time_slice,
                preset,
                {**BUILTIN_BOXES, **DIFF_BOXES},
                show_trend=show_trend
            )
            st.pyplot(fig)
            st.download_button(
                "Download Figure",
                buf,
                file_name=f"{variable}_timeseries.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"Error generating time series: {str(e)}")

with tab2:
    st.header(f"Spatial Maps: {variable}")
    user_caption = st.text_input("Custom Caption", "")
    
    try:
        fig, buf, cap = plot_spatial_map(
            ds,
            variable,
            time_slice,
            preset,
            colormap,
            selected_indices if 'selected_indices' in locals() else ["Raw"],
            {**BUILTIN_BOXES, **DIFF_BOXES},
            show_boxes=show_boxes,
            user_caption=user_caption
        )
        st.pyplot(fig)
        st.caption(cap)
        st.download_button(
            "Download Map",
            buf,
            file_name=f"{variable}_map.png",
            mime="image/png"
        )
    except Exception as e:
        st.error(f"Error generating spatial map: {str(e)}")

if __name__ == "__main__":
    st.write("App is ready for analysis!")
