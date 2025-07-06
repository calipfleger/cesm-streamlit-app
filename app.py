from remote_data_fetcher import remote_fetch_workflow
import streamlit as st
import os
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from cesm_utils import (
    load_netcdf_files, load_indices,
    plot_timeseries, plot_spatial_mean, plot_correlation_map,
    get_dataset_summary, save_figure_with_caption
)

st.set_page_config(layout="wide", page_title="Volcanic & Anthropogenic ENSO Signal Explorer")

st.title("🌋 Volcanic & Anthropogenic ENSO Signal Explorer")
st.markdown("""
A modular, publication-ready explorer for iCESM NetCDF outputs and ENSO-related climate indices.

**Features:**
- Explore δ18Op, SLP, SST, w500, precipitation
- Compare GHG, aerosol, and full-forcing iCESM simulations
- Upload custom NetCDF or ENSO indices (e.g., ONI, Nino 3.4)
- Save figures and download NetCDF selections

---""")

# Load NetCDF datasets
netcdf_files = load_netcdf_files("data/")
if not netcdf_files:
    st.warning("No NetCDF files found. Generated dummy dataset for demonstration.")
    dummy_ds = xr.Dataset({
        "tas": (("time", "lat", "lon"),
            np.random.rand(100, 10, 20)),
        "time": pd.date_range("2000-01-01", periods=100, freq="M"),
        "lat": np.linspace(-10, 10, 10),
        "lon": np.linspace(100, 300, 20)
    })
    dummy_path = "data/dummy.nc"
    dummy_ds.to_netcdf(dummy_path)
    netcdf_files = load_netcdf_files("data/")

# Sidebar File Selection
selected_netcdf = st.sidebar.selectbox("Select NetCDF Dataset:", netcdf_files, key="netcdf_select")
ds = xr.open_dataset(selected_netcdf)
remote_fetch_workflow()

# Index Upload/Selection
indices_df = load_indices("indices/")
uploaded_index = st.sidebar.file_uploader("Upload ENSO Index CSV", type="csv")
if uploaded_index:
    index_df = pd.read_csv(uploaded_index)
else:
    selected_index = st.sidebar.selectbox("Select ENSO Index (if any):", list(indices_df.keys()) or ["None"], key="index_select")
    index_df = indices_df.get(selected_index, pd.DataFrame())

# Time Slider
time_coord = ds.coords.get("time")
if time_coord is not None:
    time_indices = st.slider("Select Time Index Range:", 0, len(time_coord) - 1, (0, len(time_coord) - 1))
    ds = ds.isel(time=slice(*time_indices))

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Time Series", "🗺 Spatial Maps", "🔗 Correlation"])

with tab1:
    st.subheader("📈 Time Series Viewer")
    var = st.selectbox("Select Variable:", list(ds.data_vars))
    fig, ax = plt.subplots(figsize=(8, 4))
    plot_timeseries(ds, var, ax)
    st.pyplot(fig)
    save_figure_with_caption(fig, f"{var}_timeseries.png", f"Time series of {var} from {selected_netcdf}")

with tab2:
    st.subheader("🗺 Spatial Mean Map")
    var = st.selectbox("Select Variable for Map:", list(ds.data_vars), key="map_var")
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_spatial_mean(ds, var, ax)
    st.pyplot(fig)
    save_figure_with_caption(fig, f"{var}_map.png", f"Spatial average of {var} over selected time.")

with tab3:
    st.subheader("🔗 Correlation with ENSO Index")
    if not index_df.empty:
        var = st.selectbox("Select Variable for Correlation:", list(ds.data_vars), key="corr_var")
        fig, ax = plt.subplots(figsize=(6, 4))
        plot_correlation_map(ds, var, index_df, ax)
        st.pyplot(fig)
        save_figure_with_caption(fig, f"{var}_correlation.png", f"Correlation of {var} with ENSO index.")
    else:
        st.info("Upload or select an ENSO index CSV file to enable correlation plots.")

# Download section
with st.sidebar:
    st.markdown("### 📥 Download NetCDF Subset")
    if st.button("Download Current Subset"):
        subset_path = "data/exported_subset.nc"
        ds.to_netcdf(subset_path)
        with open(subset_path, "rb") as f:
            st.download_button("Download", f, file_name="subset.nc")

# Metadata Display
st.markdown("### 🧬 Dataset Summary")
st.json(get_dataset_summary(ds))

