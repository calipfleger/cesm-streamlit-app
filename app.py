import streamlit as st
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

# Set up paths
DATA_DIR = 'data/'
INDEX_DIR = 'indices/'
FIGURE_DIR = 'saved_figures/'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

# Sidebar reference
with st.sidebar.expander("Research Toolkit & Indices"):
    st.markdown("""
    **Key Indicators:**
    - PWC (Pacific Walker Circulation Index)
    - Nino 3.4 / ONI from NOAA
    - d18Op, SLP, SST from iCESM (Full, GHG, OZA)

    **Scientific Links & Resources:**
    - [Nino 3.4 index](https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php)
    - [Volcano Coral-ation GitHub](https://github.com/Past-And-Future-Climates-Group/Volcano-Coral-ation)
    - [PWC Workshop Abstract](https://docs.google.com/document/d/1T84c-d18OpPWCsummary)
    """)

# Title and description
st.set_page_config(page_title="CESM & Coral ENSO Explorer", layout="wide")
st.title("Volcanic & Anthropogenic ENSO Signal Explorer")

st.markdown("""
Explore iCESM and Iso2k climate model output with modular selection of ENSO-related indices (e.g., PWC, δ18Op, SLP, SST). This research tool integrates publication-ready figure generation, dynamic metadata captioning, and support for full-, GHG-, and aerosol-forcing ensemble evaluation.
""")

# Load NetCDF datasets
netcdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".nc")]
if not netcdf_files:
    st.error("No NetCDF files found in /data.")
    st.stop()

selected_netcdf = st.sidebar.selectbox("Select NetCDF Dataset:", netcdf_files)
ds = xr.open_dataset(os.path.join(DATA_DIR, selected_netcdf))
variables = list(ds.data_vars)
selected_variable = st.sidebar.selectbox("Select Variable:", variables)

# Uploadable modular index CSV
st.sidebar.subheader("Upload New Climate Index (optional)")
uploaded_index_file = st.sidebar.file_uploader("Upload CSV index (time as index)", type="csv")
if uploaded_index_file:
    index_df = pd.read_csv(uploaded_index_file, parse_dates=True, index_col=0)
    st.sidebar.success("New index uploaded and loaded.")
else:
    index_files = [f for f in os.listdir(INDEX_DIR) if f.endswith(".csv")]
    if index_files:
        selected_index = st.sidebar.selectbox("Select Index CSV:", index_files)
        index_df = pd.read_csv(os.path.join(INDEX_DIR, selected_index), parse_dates=True, index_col=0)
    else:
        index_df = None

# Time slicing
if 'time' not in ds.coords:
    st.error("Dataset must include a 'time' coordinate.")
    st.stop()
time_values = ds['time'].values
try:
    min_time = int(time_values[0])
    max_time = int(time_values[-1])
except:
    min_time, max_time = 0, len(time_values) - 1
time_range = st.slider("Select Time Range:", min_time, max_time, (min_time, max_time))
data_slice = ds[selected_variable].sel(time=slice(time_range[0], time_range[1]))

# Plot selected variable
st.subheader(f"Time Series: {selected_variable}")
fig, ax = plt.subplots(figsize=(10, 5))
data_slice.plot(ax=ax, label=selected_variable)

# Overlay selected or uploaded index
if index_df is not None:
    for col in index_df.columns:
        if len(index_df[col]) >= len(data_slice.time):
            ax.plot(data_slice.time.values, index_df[col][:len(data_slice.time)], linestyle='--', label=f"Index: {col}")
    ax.legend()

st.pyplot(fig)

# Caption metadata
caption_mode = st.sidebar.selectbox("Caption Style:", [
    "Scientific Publication",
    "Exploratory",
    "Model-Proxy Comparison",
    "Index Correlation",
    "Walker Group Analysis"
])

meta = {
    'dims': dict(ds.dims),
    'units': ds[selected_variable].attrs.get('units', 'N/A'),
    'desc': ds[selected_variable].attrs.get('description', 'No description')
}

def generate_caption(style):
    ts = f"(time {time_range[0]}–{time_range[1]})"
    if style == "Scientific Publication":
        return f"Figure: Time series of '{selected_variable}' from {selected_netcdf} {ts}. {meta['desc']} Units: {meta['units']}."
    elif style == "Exploratory":
        return f"Plot of variable '{selected_variable}' {ts} for visual inspection and trend detection."
    elif style == "Model-Proxy Comparison":
        return f"Comparison of modeled {selected_variable} with proxy/index during {ts}."
    elif style == "Index Correlation":
        return f"Overlay of '{selected_variable}' with climate index over {ts}."
    elif style == "Walker Group Analysis":
        return f"Figure shows post-industrial trends in '{selected_variable}' over {ts}, relevant to PWC and δ18Op diagnostic sensitivity."
    return "No caption generated."

caption = generate_caption(caption_mode)
st.markdown(f"**Caption:** {caption}")

# Export options
save_option = st.sidebar.checkbox("Enable Export")
if save_option and st.sidebar.button("Save Figure & Caption"):
    fname = f"{selected_variable}_{selected_netcdf.replace('.nc','')}_{time_range[0]}_{time_range[1]}"
    fig.savefig(os.path.join(FIGURE_DIR, fname + ".png"), bbox_inches='tight')
    with open(os.path.join(FIGURE_DIR, fname + "_caption.txt"), 'w') as f:
        f.write(caption)
    st.success("Figure and caption saved.")

