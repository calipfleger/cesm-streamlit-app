# ---- cesm_utils.py ----
"""
Utility functions for CESM Streamlit app.

Features implemented in this refactor:
- Lazy dataset loading with chunking
- Dropdown‑selectable climate indices (Raw, Global Mean, Nino3.4)
- Journal presets that control DPI, figure size, and font size
- Publication‑grade plotting helpers that return (fig, PNG buffer, caption)
- Trend‑map calculation via xarray.polyfit
"""

from typing import Tuple, Dict, Any, Union
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import io

JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature": {"dpi": 600, "figure_size": (7, 5), "font_size": 8},
    "Science": {"dpi": 600, "figure_size": (6, 4), "font_size": 8},
    "GRL": {"dpi": 300, "figure_size": (6, 4), "font_size": 10},
    "JCLI": {"dpi": 300, "figure_size": (6, 4), "font_size": 9},
    "Climate Dynamics": {"dpi": 300, "figure_size": (6, 4), "font_size": 9},
    "Custom": {"dpi": 300, "figure_size": (6, 4), "font_size": 10},
}

# -----------------------------------------------------------------------------

def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    """Open a NetCDF file with Xarray and optional Dask chunking."""
    return xr.open_dataset(path, chunks=chunks)

# -----------------------------------------------------------------------------

def compute_index(ds: xr.Dataset, var: str, index: str) -> xr.DataArray:
    """Return a DataArray representing the chosen index."""
    da = ds[var]

    if index == "Raw":
        return da

    if index == "Global Mean":
        if {"lat", "lon"}.issubset(da.coords):
            weights = np.cos(np.deg2rad(da.lat))
            weights.name = "weights"
            return da.weighted(weights).mean(dim=("lat", "lon"))
        return da.mean(dim=[d for d in da.dims if d != "time"])

    if index == "Nino3.4":
        if {"lat", "lon"}.issubset(da.coords):
            sel = da.sel(lat=slice(-5, 5), lon=slice(190, 240))
            return sel.mean(dim=("lat", "lon"))
        raise ValueError("Nino3.4 index requires lat/lon coordinates")

    raise ValueError(f"Unknown index: {index}")

# -----------------------------------------------------------------------------

def _fig_to_buffer(fig: plt.Figure, dpi: int) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf

def _summary_stats(da: xr.DataArray) -> Dict[str, float]:
    return {
        "Mean": float(da.mean().values),
        "Std Dev": float(da.std().values),
        "Min": float(da.min().values),
        "Max": float(da.max().values),
    }

# -----------------------------------------------------------------------------

def plot_timeseries(
    ds: xr.Dataset,
    var: str,
    index: str,
    time_slice: slice,
    preset: Dict[str, Any],
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Generate a time‑series figure and caption."""
    da = compute_index(ds, var, index).sel(time=time_slice)

    # Collapse spatial dims if they remain
    spatial_dims = [d for d in da.dims if d not in ("time",)]
    if spatial_dims:
        da = da.mean(dim=spatial_dims)

    stats = _summary_stats(da)

    fig, ax = plt.subplots(figsize=preset["figure_size"], dpi=preset["dpi"])
    da.plot(ax=ax)
    ax.set_title(
        f"{index} {var} ({str(da.time.values[0])[:10]}–{str(da.time.values[-1])[:10]})",
        fontsize=preset["font_size"] + 2,
    )
    ax.set_ylabel(var)
    ax.grid(True, which="both", linestyle="--", alpha=0.3)

    caption = (
        f"Time series of **{index} {var}** from {str(da.time.values[0])[:10]} "
        f"to {str(da.time.values[-1])[:10]}. "
        f"Mean = {stats['Mean']:.3g}, SD = {stats['Std Dev']:.3g}, "
        f"Min = {stats['Min']:.3g}, Max = {stats['Max']:.3g}."
    )

    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# -----------------------------------------------------------------------------

def plot_spatial_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: Dict[str, Any],
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Plot a time‑mean spatial map."""
    da = ds[var].sel(time=time_slice).mean(dim="time")

    fig, ax = plt.subplots(figsize=preset["figure_size"], dpi=preset["dpi"])
    da.plot(ax=ax, cmap="coolwarm")
    ax.set_title(f"Mean Spatial Map: {var}", fontsize=preset["font_size"] + 2)

    caption = (
        f"Spatial mean of **{var}** over the selected period "
        f"({str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]})."
    )

    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# -----------------------------------------------------------------------------

def plot_trend_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: Dict[str, Any],
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Compute and plot the linear trend (slope) at each grid point."""
    da = ds[var].sel(time=time_slice)

    coeff = (
        da.polyfit(dim="time", deg=1)["polyfit_coefficients"]
        .sel(degree=0)
        .rename(var)
    )

    fig, ax = plt.subplots(figsize=preset["figure_size"], dpi=preset["dpi"])
    coeff.plot(ax=ax, cmap="coolwarm", robust=True)
    ax.set_title(f"Linear Trend per timestep: {var}", fontsize=preset["font_size"] + 2)

    units = da.attrs.get("units", "")
    caption = (
        f"Linear trend of **{var}** for each grid cell computed over "
        f"{str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]}. "
        f"Units: {units} per timestep."
    )

    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# -----------------------------------------------------------------------------

def plot_correlation(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: Dict[str, Any],
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Mock correlation plot (placeholder)."""
    da = ds[var].sel(time=time_slice)
    corr = da.mean(dim="time").values

    fig, ax = plt.subplots(figsize=preset["figure_size"], dpi=preset["dpi"])
    im = ax.imshow(corr, cmap="coolwarm")
    plt.colorbar(im, ax=ax)
    ax.set_title(f"Mock Correlation Plot: {var}", fontsize=preset["font_size"] + 2)

    caption = f"Mock correlation map of **{var}**. Replace with real metric."

    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# Re‑export for convenience ----------------------------------------------------
__all__ = [
    "JOURNAL_PRESETS",
    "load_dataset",
    "compute_index",
    "plot_timeseries",
    "plot_spatial_map",
    "plot_trend_map",
    "plot_correlation",
]
