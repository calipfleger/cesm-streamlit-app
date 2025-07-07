# ---- cesm_utils.py ----
"""
Utilities for CESM Streamlit app (rev 2025‑07‑07‑i)
=================================================
Additions
~~~~~~~~~
• **Extra ENSO indices**: Niño 1+2, Niño 3, Niño 4 (alongside existing Niño 3.4).
• **Pacific Walker Circulation index** (`PWC-U850`) – zonal‐wind difference between
  western (5°S–5°N, 130–160 °E) and central‑eastern Pacific (5°S–5°N, 160–130 °W).
• `plot_timeseries` now shows each series’ **time‑mean** as a dotted line.
• `_clean_da` bug‑fix (removed stray parenthesis).
• All map plots and captions unchanged; new indices work automatically in
  Streamlit dropdown and CLI script.
"""
from __future__ import annotations

from typing import Tuple, Dict, Any, Union, Sequence, Mapping
import io
import warnings

import numpy as np
import xarray as xr
import matplotlib as mpl
import matplotlib.pyplot as plt

try:  # Optional Cartopy
    import cartopy.crs as ccrs
    HAS_CARTOPY = True
except ModuleNotFoundError:
    HAS_CARTOPY = False
    ccrs = None  # type: ignore

# ─────────────────────────────────────────────────────────────────────────────
# Journal presets
# ─────────────────────────────────────────────────────────────────────────────
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature":  {"dpi": 600, "figure_size": (7, 5),   "font_size": 8,  "font": "Helvetica"},
    "Science": {"dpi": 600, "figure_size": (6.5, 4.5), "font_size": 8,  "font": "Times New Roman"},
    "GRL":     {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "Arial"},
    "JCLI":    {"dpi": 300, "figure_size": (6, 4),   "font_size": 9,  "font": "Arial"},
    "Climate Dynamics": {"dpi": 300, "figure_size": (6, 4), "font_size": 9, "font": "Arial"},
    "Custom":  {"dpi": 300, "figure_size": (6, 4),   "font_size": 10, "font": "sans-serif"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Region boxes for mean indices
# lon in 0–360°E
# ─────────────────────────────────────────────────────────────────────────────
BUILTIN_BOXES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Nino1+2": {"lat": (-10, 0),  "lon": (270, 280)},   # 90‑80° W
    "Nino3":   {"lat": (-5, 5),   "lon": (210, 270)},   # 140‑90° W
    "Nino3.4": {"lat": (-5, 5),   "lon": (190, 240)},   # 170‑120° W
    "Nino4":   {"lat": (-5, 5),   "lon": (160, 210)},   # 160° E‑150° W
}

# PWC difference index definition
DIFF_BOXES = {
    "PWC-U850": {
        "var": "U850",  # variable required
        "west": {"lat": (-5, 5), "lon": (130, 160)},   # 130‑160° E
        "east": {"lat": (-5, 5), "lon": (200, 230)},   # 160‑130° W
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# MPL context helper
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_RC = mpl.rcParams.copy()

def apply_journal_style(preset):
    class _Ctx:
        def __enter__(self):
            mpl.rcParams.update({
                "figure.dpi": preset["dpi"],
                "font.family": preset["font"],
                "font.size": preset["font_size"],
                "axes.titlesize": preset["font_size"] + 2,
                "axes.labelsize": preset["font_size"],
            })
        def __exit__(self, *_):
            mpl.rcParams.update(_DEFAULT_RC)
    return _Ctx()

# ─────────────────────────────────────────────────────────────────────────────
# I/O
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    try:
        return xr.open_dataset(path, chunks=chunks)
    except ImportError:
        warnings.warn("Dask not available – loading eagerly.")
        return xr.open_dataset(path)

# ─────────────────────────────────────────────────────────────────────────────
# Index computation
# ─────────────────────────────────────────────────────────────────────────────

def _area_mean(da, lat_bnds, lon_bnds):
    sub = da.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    w = np.cos(np.deg2rad(sub.lat))
    return sub.weighted(w).mean(dim=("lat", "lon"))


def compute_index(ds: xr.Dataset, var: str, name: str, boxes):
    da = ds[var]
    if name == "Raw":
        return da
    if name == "Global Mean":
        return _area_mean(da, (-90, 90), (0, 360)) if {"lat", "lon"}.issubset(da.coords) else da.mean()
    if name in boxes:
        box = boxes[name]
        return _area_mean(da, box["lat"], box["lon"])
    if name in DIFF_BOXES:
        meta = DIFF_BOXES[name]
        req_var = meta["var"]
        if var != req_var:
            raise ValueError(f"Index '{name}' requires variable '{req_var}' but got '{var}'.")
        west = _area_mean(da, **meta["west"])
        east = _area_mean(da, **meta["east"])
        return west - east
    raise ValueError(name)

# ─────────────────────────────────────────────────────────────────────────────
# Data cleaning
# ─────────────────────────────────────────────────────────────────────────────

def _clean_da(da: xr.DataArray) -> xr.DataArray:
    fill_vals = []
    for key in ("_FillValue", "missing_value"):
        if key in da.attrs:
            fv = da.attrs[key]
            fill_vals.extend(fv if np.iterable(fv) else [fv])
    mask = np.isfinite(da)
    for fv in fill_vals:
        mask &= da != fv
    mask &= np.abs(da) < 1e30
    return da.where(mask)

# ─────────────────────────────────────────────────────────────────────────────
# Colour‑bar helper
# ─────────────────────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────────────────────
# Plot: Time‑series
# ─────────────────────────────────────────────────────────────────────────────

def _trendline(x, y):
    a, b = np.polyfit(x, y, 1)
    return a * x + b


def plot_timeseries(ds, var, indices, t_slice, preset, boxes, user_caption=None, show_trendline=False):
    with apply_journal_style(preset):
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        captions = []
        t = ds["time"].sel(time=t_slice).values
        x_num = t.astype("datetime64[s]").astype(float)
        for name in indices:
            da = compute_index(ds, var, name, boxes).sel(time=t_slice)
            if [d for d in da.dims if d not in ("time",)]:
                da = da.mean(dim=[d for d in da.dims if d != "time"])
            μ, σ = float(da.mean()), float(da.std())
            line, = ax.plot(t, da, label=name)
            ax.fill_between(t, da - σ, da + σ, alpha=0.12, color=line.get_color())
            ax.axhline(μ, linestyle=":", color=line.get_color(), linewidth=0.8)
            if show_trendline:
                ax.plot(t, _trendline(x_num, da.values), linestyle="--", color=line.get_color())
            captions.append(f"**{name}**: μ={μ:.3g}, σ={σ:.3g}")
        ax.set_ylabel(var)
        ax.set_title(f"{', '.join(indices)} {var}")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=preset["font_size"], loc="upper right")
        cap = "; ".join(captions)
        if user_caption:
            cap += " " + user_caption
        fig.text(0.5, -0.08, cap, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
        fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig, _fig_buf(fig, preset["dpi"]), cap

# ─────────────────────────────────────────────────────────────────────────────
# Map helpers & full map functions (restored)
# ─────────────────────────────────────────────────────────────────────────────

def _fig_buf(fig, dpi):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf


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
            kw = {"color": "k", "linestyle": "--", "linewidth": 1}
            if proj is not None:
                ax.plot(xs, ys, transform=ccrs.PlateCarree(), **kw)
            else:
                ax.plot(xs, ys, **kw)


def _map_core(da, title, preset, cmap, cb_kw, indices, boxes, show_boxes):
    with apply_journal_style(preset):
        fig, ax, proj = _geo_axes(preset)
        da = _clean_da(da)
        if {"lat", "lon"}.issubset(da.dims):
            da.plot(ax=ax, cmap=cmap, add_colorbar=True, transform=proj if proj else None, **cb_kw)
        else:  # fallback imshow
            im = ax.imshow(da.values, cmap=cmap, **{k: v for k, v in cb_kw.items() if k not in {"robust"}})
            fig.colorbar(im, ax=ax)
        _draw_boxes(ax, proj, indices, boxes, show_boxes)
        ax.set_title(title)
        return fig


def plot_spatial_map(ds, var, t_slice, preset, cmap, indices, boxes, cbar_mode, vmin, vmax, show_boxes, user_caption=None):
    da = ds[var].sel(time=t_slice).mean(dim="time")
    cb_kw = _cbar_kwargs(da, cbar_mode, vmin, vmax)
    fig = _map_core(da, f"Mean {var}", preset, cmap, cb_kw, indices, boxes, show_boxes)
    caption = f"Spatial mean of **{var}** {str(t_slice.start)[:10]}–{str(t_slice.stop)[:10]}."
    if user_caption:
        caption += " " + user_caption
    fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig, _fig_buf(fig, preset["dpi"]), caption


def plot_trend_map(ds, var, t_slice, preset, cmap, indices, boxes, cbar_mode, vmin, vmax, show_boxes, user_caption=None):
    da = ds[var].sel(time=t_slice)
    coeff = da.polyfit(dim="time", deg=1)["polyfit_coefficients"].sel(degree=0).rename(var)
    units = da.attrs.get("units", "")
    cb_kw = _cbar_kwargs(coeff, cbar_mode, vmin, vmax)
    fig = _map_core(coeff, f"Trend {var}", preset, cmap, cb_kw, indices, boxes, show_boxes)
    caption = f"Linear trend of **{var}** ({units}/timestep) {str(t_slice.start)[:10]}–{str(t_slice.stop)[:10]}."
    if user_caption:
        caption += " " + user_caption
    fig.text(0.5, -0.08, caption, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig, _fig_buf(fig, preset["dpi"]), caption

