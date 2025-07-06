import streamlit as st
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cartopy.crs as ccrs
import io

st.set_page_config(layout="wide")
st.title("iCESM Volcanic Sensitivity Visualization App")

st.markdown("""
Upload your iCESM NetCDF climate model output (e.g. precipitation, δ¹⁸O, ENSO indices) and compare different volcanic eruption scenarios.
""")

# --- Sidebar: File upload and controls ---
with st.sidebar:
    st.header("1. Upload Model Data")
    nc_file = st.file_uploader("Upload NetCDF file (.nc)", type=["nc"])
    
    st.header("2. (Optional) Upload Proxy Data")
    proxy_file = st.file_uploader("Upload Proxy CSV (year,value)", type=["csv"])

    st.header("3. Visualization Controls")
    year_range = st.slider("Year Range After Eruption", 0, 10, (0, 5))
    region = st.selectbox(
        "Region for Timeseries (for regional analysis)",
        options=["Global", "El Niño 3.4 (Pacific)", "Australia (NW, KNI-51 region)"]
    )

    st.header("4. Help")
    st.markdown("**Sample dataset:** [Download test NetCDF](https://github.com/ai-cecs/cesm-streamlit-app/raw/main/testdata/test_icesm.nc)  \n"
                "Sample proxy: [Download proxy CSV](https://github.com/ai-cecs/cesm-streamlit-app/raw/main/testdata/kni51_proxy.csv)")

# --- Load Model Data ---
if nc_file:
    with st.spinner("Loading NetCDF file..."):
        ds = xr.open_dataset(nc_file)
        st.success(f"Loaded dataset with variables: {list(ds.variables)}")
else:
    st.warning("Please upload a NetCDF file to begin.")
    st.stop()

# --- Variable Selection ---
var_choices = [v for v in ds.data_vars if ds[v].ndim >= 1]
varname = st.selectbox("Climate Variable to Visualize", var_choices)
data = ds[varname]

# --- Time selection ---
if "year" in ds.coords:
    years = ds["year"].values
elif "time" in ds.coords:
    years = ds["time"].dt.year.values
else:
    st.error("No year or time coordinate found!")
    st.stop()
eruption_year = years[0]  # Assume first year is eruption year for this demo
year_sel = (years >= (eruption_year + year_range[0])) & (years <= (eruption_year + year_range[1]))
year_index = np.where(year_sel)[0]

# --- Map Visualization ---
if data.ndim >= 3 and {"lat", "lon"}.issubset(data.dims):
    st.subheader("Spatial Map: Mean Response After Eruption")
    mean_map = data.isel(time=year_index).mean(dim="time")
    fig = plt.figure(figsize=(9, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    im = ax.pcolormesh(ds["lon"], ds["lat"], mean_map.squeeze(), cmap='BrBG', shading='auto')
    ax.coastlines()
    plt.colorbar(im, ax=ax, shrink=0.5, label=f"Mean {varname}")
    st.pyplot(fig)

# --- ENSO Timeseries (Nino3.4) ---
if "nino34" in ds.data_vars:
    st.subheader("ENSO Timeseries (Nino3.4)")
    nino = ds["nino34"]
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(years, nino, marker='o')
    ax.axvline(eruption_year, color='red', linestyle='--', label="Eruption")
    ax.set_xlabel("Year")
    ax.set_ylabel("Nino3.4 Index")
    ax.legend()
    st.pyplot(fig)

# --- Regional Timeseries ---
st.subheader("Regional Timeseries")
if region == "Global":
    ts = data.mean(dim=[d for d in data.dims if d in ["lat", "lon"]])
elif region == "El Niño 3.4 (Pacific)":
    mask = ((ds['lat'] >= -5) & (ds['lat'] <= 5) & (ds['lon'] >= 190) & (ds['lon'] <= 240))
    ts = data.where(mask).mean(dim=["lat", "lon"])
elif region == "Australia (NW, KNI-51 region)":
    mask = ((ds["lat"] >= -20) & (ds["lat"] <= -10) & (ds["lon"] >= 120) & (ds["lon"] <= 130))
    ts = data.where(mask).mean(dim=["lat", "lon"])
else:
    ts = data.mean(dim=[d for d in data.dims if d in ["lat", "lon"]])

fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(years, ts, label="Model")
ax.axvline(eruption_year, color='red', linestyle='--', label="Eruption Year")
ax.set_xlabel("Year")
ax.set_ylabel(f"{varname}")
ax.legend()

# Overlay proxy, if available
if proxy_file:
    pdf = pd.read_csv(proxy_file)
    ax.plot(pdf['year'], pdf['value'], marker='o', color='black', label="Proxy")
    ax.legend()
st.pyplot(fig)

# --- Download Processed Data ---
st.subheader("Download Processed Timeseries")
outdf = pd.DataFrame({"year": years, "model": ts.values})
if proxy_file:
    outdf["proxy"] = np.interp(years, pdf['year'], pdf['value'])
st.download_button("Download as CSV", outdf.to_csv(index=False), file_name="processed_timeseries.csv")

# --- Metadata Display ---
st.expander("Raw Dataset Metadata").write(ds)
