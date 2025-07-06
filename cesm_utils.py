# cesm_utils.py - Helper functions for CESM Streamlit App

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io

def load_dataset(path):
    return xr.open_dataset(path)

def plot_timeseries(ds, var, time_range):
    da = ds[var].sel(time=time_range)
    mean_ts = da.mean(dim=["lat", "lon"])

    fig, ax = plt.subplots()
    mean_ts.plot(ax=ax)
    ax.set_title(f"Time Series: {var}")
    ax.set_ylabel(var)
    return fig, fig_to_buffer(fig)

def plot_spatial_map(ds, var, time_range):
    da = ds[var].sel(time=time_range).mean(dim="time")

    fig, ax = plt.subplots()
    im = da.plot(ax=ax, cmap="coolwarm")
    ax.set_title(f"Mean Spatial Map: {var}")
    return fig, fig_to_buffer(fig)

def plot_correlation(ds, var, time_range):
    da = ds[var].sel(time=time_range)
    corr = da.mean(dim="time").values

    fig, ax = plt.subplots()
    im = ax.imshow(corr, cmap="coolwarm")
    plt.colorbar(im, ax=ax)
    ax.set_title(f"Mock Correlation Plot: {var}")
    return fig, fig_to_buffer(fig)

def get_summary_statistics(ds, var):
    da = ds[var]
    return {
        "Mean": float(da.mean().values),
        "Std Dev": float(da.std().values),
        "Min": float(da.min().values),
        "Max": float(da.max().values)
    }

def fig_to_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf

