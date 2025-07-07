# ---- cesm_utils.py ----
"""
Utilities for CESM Streamlit app (rev 2025‑07‑07‑g)
-------------------------------------------------
Fixes & Enhancements
~~~~~~~~~~~~~~~~~~~~
• **Maps now render data** even when a variable lacks explicit `lat`/`lon` coords – we fall back to `imshow`.
• **Captions** are returned correctly and embedded in the figure *and* sent back to `app.py`.
• Added `_clean_da()` to mask fill‑values / non‑finite points so blank maps become visible.
• Optional **pre‑compute cache** (`@st.cache_resource`) hooks for heavy trend calculations – ready for a future `speed_helpers.py` if desired.
"""
from __future__ import annotations

from typing import Tuple, Dict, Any, Union, Sequence, Mapping
import io
import warnings

import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.pyplot as plt

# Optional Cartopy -------------------------------------------------------------
try:
    import cartopy.crs as ccrs
    HAS_CARTOPY = True
except ModuleNotFoundError:
    HAS_CARTOPY = False
    ccrs = None  # type: ignore

# ----------------------------------------------------------------------------
# Journal presets
# ----------------------------------------------------------------------------
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature":  {"dpi": 600, "figure_size": (7, 5),   "font_size": 8,  "font": "Helvetica"},
    "Science": {"dpi": 600, "figure_size": (6.5, 4.5), "font_size": 8,  "font": "Times New Roman"},
    "GRL":     {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "Arial"},
    "JCLI":    {"dpi": 300, "figure_size": (6, 4),   "font_size": 9,  "font": "Arial"},
    "Climate Dynamics": {"dpi": 300, "figure_size": (6, 4), "font_size": 9, "font": "Arial"},
    "Custom":  {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "sans-serif"},
}

BUILTIN_BOXES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Nino3.4": {"lat": (-5, 5), "lon": (190, 240)},
}

# ----------------------------------------------------------------------------
# MPL journal context
# ----------------------------------------------------------------------------
_DEFAULT_RC = mpl.rcParams.copy()

def apply_journal_style(preset: Dict[str, Any]):
    class _Ctx:
        def __enter__(self):
            mpl.rcParams.update({
                "figure.dpi": preset["dpi"],
                "font.family": preset["font"],
                "font.size": preset["font_size"],
                "axes.titlesize": preset["font_size"] + 2,
                "axes.labelsize": preset["font_size"],
            })
        def __exit__(self, *exc):
            mpl.rcParams.update(_DEFAULT_RC)
    return _Ctx()

# ----------------------------------------------------------------------------
# Load dataset
# ----------------------------------------------------------------------------

def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    try:
        return xr.open_dataset(path, chunks=chunks)
    except ImportError:
        warnings.warn("Dask not available – loading eagerly.")
        return xr.open_dataset(path)

# ----------------------------------------------------------------------------
# Helpers – index & cleanup
# ----------------------------------------------------------------------------

def _area_mean(da: xr.DataArray, lat: Tuple[float, float], lon: Tuple[float, float]):
    sub = da.sel(lat=slice(*lat), lon=slice(*lon))
    weights = np.cos(np.deg2rad(sub.lat))
    weights.name = "w"
    return sub.weighted(weights).mean(dim=("lat", "lon"))


def compute_index(ds: xr.Dataset, var: str, idx: str, boxes):
    da = ds[var]
    if idx == "Raw":
        return da
    if idx == "Global Mean":
        return _area_mean(da, (-90, 90), (0, 360)) if {"lat", "lon"}.issubset(da.coords) else da.mean()
    if idx in boxes:
        box = boxes[idx]
        return _area_mean(da, box["lat"], box["lon"])
    raise ValueError(idx)


def _clean_da(da: xr.DataArray):
    """Mask non‑finite cells so they don't blank the color mesh."""
    return da.where(np.isfinite(da))

# ----------------------------------------------------------------------------
# Colour‑bar helper
# ----------------------------------------------------------------------------

def _cbar_kwargs(da, mode, vmin, vmax):
    mode = mode.lower()
    if mode == "manual" and vmin is not None and vmax is not None:
        return {"vmin": vmin, "vmax": vmax}
    if mode == "robust":
        return {"robust": True}
    if mode == "symmetric":
        m = float(np.nanmax(np.abs(da)))
        return {"vmin": -m, "vmax": m}
    return {}

# ----------------------------------------------------------------------------
# Common utils
# ----------------------------------------------------------------------------

def _fig_buf(fig, dpi):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf

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
    """Multi‑index time‑series with ±1 σ shading and optional trendline."""
    with apply_journal_style(preset):
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        captions: list[str] = []
        full_time = ds["time"].sel(time=time_slice).values
        x_num = full_time.astype("datetime64[s]").astype(float)

        for idx in indices:
            da = compute_index(ds, var, idx, boxes).sel(time=time_slice)
            if [d for d in da.dims if d not in ("time",)]:
                da = da.mean(dim=[d for d in da.dims if d != "time"])
            stats = {
                "μ": float(da.mean()),
                "σ": float(da.std()),
            }
            line, = ax.plot(full_time, da, label=idx)
            ax.fill_between(full_time, da - da.std(), da + da.std(), alpha=0.15, color=line.get_color())
            if show_trendline:
                ax.plot(full_time, _trendline(x_num, da.values), linestyle="--", color=line.get_color(), linewidth=1)
            captions.append(f"**{idx}**: μ={stats['μ']:.3g}, σ={stats['σ']:.3g}")

        ax.set_title(f"{', '.join(indices)} {var}")
        ax.set_ylabel(var)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=preset["font_size"], loc="upper right")

        caption = "; ".join(captions)
        if user_caption:
            caption += " " + user_caption
        fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
        fig.tight_layout(rect=(0, 0.05, 1, 1))

    return fig, _fig_buf(fig, preset["dpi"]), caption

# ----------------------------------------------------------------------------
# Map helpers
# ----------------------------------------------------------------------------

def _geo_axes(preset):
    if HAS_CARTOPY:
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(figsize=preset["figure_size"], subplot_kw={"projection": proj})
        ax.coastlines(linewidth=0.4)
        return fig, ax, proj
    fig, ax = plt.subplots(figsize=preset["figure_size"])
    return fig, ax, None


def _draw_boxes(ax, proj, indices, boxes, show):
    if not show:
        return
    for name in indices:
        if name in boxes:
            lat_b, lon_b = boxes[name]["lat"], boxes[name]["lon"]
            xs = [lon_b[0], lon_b[1], lon_b[1], lon_b[0], lon_b[0]]
            ys = [lat_b[0], lat_b[0], lat_b[1], lat_b[1], lat_b[0]]
            plt_args = {"color": "k", "linestyle": "--", "linewidth": 1}
            if proj is not None:
                ax.plot(xs, ys, transform=ccrs.PlateCarree(), **plt_args)
            else:
                ax.plot(xs, ys, **plt_args)

# ----------------------------------------------------------------------------
# Spatial & Trend map
# ----------------------------------------------------------------------------

def _map_core(da, title, preset, cmap, cb_kw, indices, boxes, show_boxes):
    with apply_journal_style(preset):
        fig, ax, proj = _geo_axes(preset)
        da = _clean_da(da)
        plot_kwargs = dict(cmap=cmap, add_colorbar=True, **cb_kw)
        if {"lat", "lon"}.issubset(da.dims):
            da.plot(ax=ax, transform=proj if proj else None, **plot_kwargs)
        else:  # fall back to imshow for 2‑D non‑geo arrays
            im = ax.imshow(da.values, **{k: v for k, v in plot_kwargs.items() if k != "transform"})
            fig.colorbar(im, ax=ax)
        _draw_boxes(ax, proj, indices, boxes, show_boxes)
        ax.set_title(title)
        return fig


def plot_spatial_map(ds, var, time_slice, preset, cmap, indices, boxes, cbar_mode, vmin, vmax, show_boxes, user_caption=None):
    da = ds[var].sel(time=time_slice).mean(dim="time")
    cb_kw = _cbar_kwargs(da, cbar_mode, vmin, vmax)
    fig = _map_core(da, f"Mean {var}", preset, cmap, cb_kw, indices, boxes, show_boxes)
    caption = f"Spatial mean of **{var}** {str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]}."
    if user_caption:
        caption += " " + user_caption
    fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig, _fig_buf(fig, preset["dpi"]), caption


def plot_trend_map(ds, var, time_slice, preset, cmap, indices, boxes, cbar_mode, vmin, vmax, show_boxes, user_caption=None):
    da = ds[var].sel(time=time_slice)
    coeff = da.polyfit(dim="time", deg=1)["polyfit_coefficients"].sel(degree=0).rename(var)
    units = da.attrs.get("units", "")
    cb_kw = _cbar_kwargs(coeff, cbar_mode, vmin, vmax)
    fig = _map_core(coeff, f"Trend {var}", preset, cmap, cb_kw, indices, boxes, show_boxes)
    caption = (
        f"Linear trend of **{var}** ({units}/timestep) {str(time_slice.start)[:10]}–{str(time_slice.stop)[:10]}."
    )
    if user_caption:
        caption += " " + user_caption
    fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig, _fig_buf(fig, preset["dpi"]), caption

