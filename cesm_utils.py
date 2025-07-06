import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_netcdf_files(directory):
    """Return a list of .nc files in a directory."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".nc")]

def load_indices(directory):
    """Load all CSV index files in a folder and return a dictionary of DataFrames."""
    indices = {}
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(directory, file), index_col=0)
                indices[file] = df
            except Exception:
                pass
    return indices

def plot_timeseries(ds, varname, ax=None):
    """Plot a global average timeseries of the selected variable."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
    var = ds[varname]
    if {"lat", "lon"}.issubset(var.dims):
        ts = var.mean(dim=["lat", "lon"])
    elif "lat" in var.dims:
        ts = var.mean(dim="lat")
    else:
        ts = var
    ts.plot(ax=ax)
    ax.set_title(f"{varname} Global Mean Time Series")
    ax.set_xlabel("Time")
    ax.set_ylabel(varname)

def plot_spatial_mean(ds, varname, ax=None):
    """Plot the time-averaged spatial field of a variable."""
    if ax is None:
        fig, ax = plt.subplots()
    var = ds[varname]
    if "time" in var.dims:
        mean = var.mean(dim="time")
    else:
        mean = var
    if {"lat", "lon"}.issubset(mean.dims):
        mean.plot(ax=ax, cmap="coolwarm")
        ax.set_title(f"{varname} Time-Mean Spatial Map")
    else:
        ax.text(0.5, 0.5, f"{varname} has no spatial dims", ha="center")

def plot_correlation_map(ds, varname, index_df, ax=None):
    """Plot spatial map of correlation between NetCDF var and ENSO index."""
    if ax is None:
        fig, ax = plt.subplots()
    var = ds[varname]
    index = index_df.iloc[:, 0].values
    if "time" in var.dims:
        time_len = min(var.sizes["time"], len(index))
        var = var.isel(time=slice(0, time_len))
        index = index[:time_len]
    if {"lat", "lon"}.issubset(var.dims):
        corr = xr.corr(var, xr.DataArray(index, dims="time"), dim="time")
        corr.plot(ax=ax, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_title(f"Correlation of {varname} with ENSO Index")
    else:
        ax.text(0.5, 0.5, f"{varname} is not 3D (time, lat, lon)", ha="center")

def get_dataset_summary(ds):
    """Return a dictionary of dataset summary metadata."""
    return {
        "dimensions": dict(ds.sizes),
        "variables": list(ds.data_vars),
        "coords": list(ds.coords),
        "attributes": dict(ds.attrs)
    }

def save_figure_with_caption(fig, filename, caption):
    """Save the figure and optionally show a caption."""
    outdir = "saved_figures"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, filename)
    fig.savefig(path, bbox_inches="tight", dpi=300)
    st = __import__('streamlit')
    st.markdown(f"**Figure saved as:** `{filename}`")
    st.markdown(f"📄 *{caption}*")

