# ---- cesm_utils.py -----------------------------------------------------------
"""
Utilities for CESM Streamlit app (rev 2025-07-07-f)

Changes vs. rev-e
-----------------
• Fixed unterminated strings / brackets that broke syntax.
• Completed `plot_spatial_map` and `plot_trend_map` implementations.
• No behavioural changes otherwise (journal presets, custom boxes,
  manual colour-bar, trendlines, etc.).
"""
from __future__ import annotations

from typing import Tuple, Dict, Any, Union, Sequence, Mapping
import io
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

# Optional Cartopy (coastlines)
try:
    import cartopy.crs as ccrs
    HAS_CARTOPY = True
except ModuleNotFoundError:
    HAS_CARTOPY = False
    ccrs = None  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# Journal presets
# ──────────────────────────────────────────────────────────────────────────────
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature":  {"dpi": 600, "figure_size": (7, 5),   "font_size": 8,  "font": "Helvetica"},
    "Science": {"dpi": 600, "figure_size": (6.5, 4.5), "font_size": 8,  "font": "Times New Roman"},
    "GRL":     {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "Arial"},
    "JCLI":    {"dpi": 300, "figure_size": (6, 4),   "font_size": 9,  "font": "Arial"},
    "Climate Dynamics": {"dpi": 300, "figure_size": (6, 4), "font_size": 9, "font": "Arial"},
    "Custom":  {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "sans-serif"},
}

# Built-in boxes
BUILTIN_BOXES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Nino3.4": {"lat": (-5, 5), "lon": (190, 240)},
}

# ──────────────────────────────────────────────────────────────────────────────
# MPL journal-style context
# ──────────────────────────────────────────────────────────────────────────────
_DEFAULT_RC = mpl.rcParams.copy()


def apply_journal_style(preset: Dict[str, Any]):
    class _JournalCtx:
        def __enter__(self):
            mpl.rcParams.update(
                {
                    "figure.dpi": preset["dpi"],
                    "font.family": preset["font"],
                    "font.size": preset["font_size"],
                    "axes.titlesize": preset["font_size"] + 2,
                    "axes.labelsize": preset["font_size"],
                }
            )

        def __exit__(self, *_):
            mpl.rcParams.update(_DEFAULT_RC)

    return _JournalCtx()

# ──────────────────────────────────────────────────────────────────────────────
# Dataset loader (lazy but Dask-optional)
# ──────────────────────────────────────────────────────────────────────────────
def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    try:
        return xr.open_dataset(path, chunks=chunks)
    except ImportError:
        warnings.warn("Dask not available – loading eagerly.")
        return xr.open_dataset(path)

# ──────────────────────────────────────────────────────────────────────────────
# Index helpers
# ──────────────────────────────────────────────────────────────────────────────
def _area_mean(
    da: xr.DataArray, lat_bnds: Tuple[float, float], lon_bnds: Tuple[float, float]
) -> xr.DataArray:
    sub = da.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    weights = np.cos(np.deg2rad(sub.lat))
    weights.name = "w"
    return sub.weighted(weights).mean(dim=("lat", "lon"))


def compute_index(
    ds: xr.Dataset,
    var: str,
    index: str,
    boxes: Mapping[str, Dict[str, Tuple[float, float]]],
) -> xr.DataArray:
    da = ds[var]
    if index == "Raw":
        return da
    if index == "Global Mean":
        if {"lat", "lon"}.issubset(da.coords):
            return _area_mean(da, (-90, 90), (0, 360))
        return da.mean(dim=[d for d in da.dims if d != "time"])
    if index in boxes:
        box = boxes[index]
        return _area_mean(da, box["lat"], box["lon"])
    raise ValueError(f"Unknown index '{index}'.")

# ──────────────────────────────────────────────────────────────────────────────
# Colour-bar helper
# ──────────────────────────────────────────────────────────────────────────────
def _cbar_kwargs(da: xr.DataArray, mode: str, vmin: float | None, vmax: float | None):
    mode = mode.lower()
    if mode == "manual" and vmin is not None and vmax is not None:
        return {"vmin": vmin, "vmax": vmax}
    if mode == "robust":
        return {"robust": True}
    if mode == "symmetric":
        vmax_auto = float(np.nanmax(np.abs(da)))
        return {"vmin": -vmax_auto, "vmax": vmax_auto}
    return {}

# ──────────────────────────────────────────────────────────────────────────────
# Small utilities
# ──────────────────────────────────────────────────────────────────────────────
def _fig_to_buf(fig: mpl.figure.Figure, dpi: int):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf


def _summary(da: xr.DataArray) -> Dict[str, float]:
    return {
        "Mean": float(da.mean()),
        "Std Dev": float(da.std()),
        "Min": float(da.min()),
        "Max": float(da.max()),
    }

# ──────────────────────────────────────────────────────────────────────────────
# Time-series plot (same as previous good version, kept for completeness)
# ──────────────────────────────────────────────────────────────────────────────
def _trendline(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a, b = np.polyfit(x, y, 1)
    return a * x + b


def plot_timeseries(
    ds: xr.Dataset,
    var: str,
    indices: Sequence[str],
    time_slice: slice,
    preset: Dict[str, Any],
    boxes: Mapping[str, Dict[str, Tuple[float, float]]],
    user_caption: str | None = None,
    show_trendline: bool = False,
):
    with apply_journal_style(preset):
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        captions: list[str] = []

        full_time = ds["time"].sel(time=time_slice).values
        x_num = full_time.astype("datetime64[s]").astype(float)

        for idx in indices:
            da = compute_index(ds, var, idx, boxes).sel(time=time_slice)
            if [d for d in da.dims if d not in ("time",)]:
                da = da.mean(dim=[d for d in da.dims if d != "time"])
            stats = _summary(da)

            line, = ax.plot(full_time, da, label=idx)
            ax.fill_between(
                full_time,
                da - da.std(),
                da + da.std(),
                alpha=0.15,
                color=line.get_color(),
            )

            if show_trendline:
                ax.plot(
                    full_time,
                    _trendline(x_num, da.values),
                    linestyle="--",
                    color=line.get_color(),
                )
            captions.append(
                f"**{idx}**: μ = {stats['Mean']:.3g}, σ = {stats['Std Dev']:.3g}"
            )

        ax.set_title(f"{', '.join(indices)} {var}")
        ax.set_ylabel(var)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=preset["font_size"], loc="upper right")

        full_cap = "; ".join(captions) + (" " + user_caption if user_caption else "")
        fig.text(
            0.5,
            -0.08,
            full_cap,
            ha="center",
            va="top",
            fontsize=preset["font_size"],
            wrap=True,
        )
        fig.tight_layout(rect=(0, 0.05, 1, 1))

    return fig, _fig_to_buf(fig, preset["dpi"]), full_cap

# ──────────────────────────────────────────────────────────────────────────────
# Map helpers
# ──────────────────────────────────────────────────────────────────────────────
def _geo_axes(preset):
    if HAS_CARTOPY:
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(
            figsize=preset["figure_size"], subplot_kw={"projection": proj}
        )
        ax.coastlines(linewidth=0.5)
        return fig, ax, proj
    fig, ax = plt.subplots(figsize=preset["figure_size"])
    return fig, ax, None


def _draw_boxes(ax, proj, indices, boxes, show):
    if not show:
        return
    for idx in indices:
        if idx in boxes:
            lat_bnds = boxes[idx]["lat"]
            lon_bnds = boxes[idx]["lon"]
            xs = [
                lon_bnds[0],
                lon_bnds[1],
                lon_bnds[1],
                lon_bnds[0],
                lon_bnds[0],
            ]
            ys = [
                lat_bnds[0],
                lat_bnds[0],
                lat_bnds[1],
                lat_bnds[1],
                lat_bnds[0],
            ]
            if proj is not None:
                ax.plot(xs, ys, transform=ccrs.PlateCarree(), color="k", linestyle="--")
            else:
                ax.plot(xs, ys, color="k", linestyle="--")

# ──────────────────────────────────────────────────────────────────────────────
# Spatial & Trend map functions (complete)
# ──────────────────────────────────────────────────────────────────────────────
def plot_spatial_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: Dict[str, Any],
    cmap: str,
    indices: Sequence[str],
    boxes: Mapping[str, Dict[str, Tuple[float, float]]],
    cbar_mode: str,
    vmin: float | None,
    vmax: float | None,
    show_boxes: bool,
    user_caption: str | None = None,
):
    da = ds[var].sel(time=time_slice).mean(dim="time")
    cb_kw = _cbar_kwargs(da, cbar_mode, vmin, vmax)

    with apply_journal_style(preset):
        fig, ax, proj = _geo_axes(preset)
        da.plot(
            ax=ax,
            cmap=cmap,
            add_colorbar=True,
            transform=proj if proj else None,
            **cb_kw,
        )
        _draw_boxes(ax, proj, indices, boxes, show_boxes)
        ax.set_title(f"Mean {var}")

        caption = (
            f"Spatial mean of **{var}** "
            f"{str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]}."
        )
        if user_caption:
            caption += " " + user_caption

        fig.text(
            0.5,
            -0.08,
            caption,
            ha="center",
            va="top",
            fontsize=preset["font_size"],
            wrap=True,
        )
        fig.tight_layout(rect=(0, 0.05, 1, 1))

    return fig, _fig_to_buf(fig, preset["dpi"]), caption


def plot_trend_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: Dict[str, Any],
    cmap: str,
    indices: Sequence[str],
    boxes: Mapping[str, Dict[str, Tuple[float, float]]],
    cbar_mode: str,
    vmin: float | None,
    vmax: float | None,
    show_boxes: bool,
    user_caption: str | None = None,
):
    da = ds[var].sel(time=time_slice)
    coeff = (
        da.polyfit(dim="time", deg=1)["polyfit_coefficients"]
        .sel(degree=0)
        .rename(var)
    )
    cb_kw = _cbar_kwargs(coeff, cbar_mode, vmin, vmax)
    units = da.attrs.get("units", "")

    with apply_journal_style(preset):
        fig, ax, proj = _geo_axes(preset)
        coeff.plot(
            ax=ax,
            cmap=cmap,
            add_colorbar=True,
            transform=proj if proj else None,
            **cb_kw,
        )
        _draw_boxes(ax, proj, indices, boxes, show_boxes)
        ax.set_title(f"Trend {var}")

        caption = (
            f"Linear trend of **{var}** ({units}/timestep) "
            f"{str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]}."
        )
        if user_caption:
            caption += " " + user_caption

        fig.text(
            0.5,
            -0.08,
            caption,
            ha="center",
            va="top",
            fontsize=preset["font_size"],
            wrap=True,
        )
        fig.tight_layout(rect=(0, 0.05, 1, 1))

    return fig, _fig_to_buf(fig, preset["dpi"]), caption

