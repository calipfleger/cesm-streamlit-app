# ---- cesm_utils.py ----
"""
Utility functions for CESM Streamlit app.
Provides climate data analysis, plotting, and index calculations.
"""

from __future__ import annotations
from typing import Dict, Any, Union, Optional
import io
import os
import yaml
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

# Optional Cartopy for better maps
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False
    ccrs = None

# ─── Journal presets ─────────────────────────────────────────────────────────
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature": {"dpi": 600, "figure_size": (7, 5), "font_size": 8, "font": "Helvetica"},
    "Science": {"dpi": 600, "figure_size": (6.5, 4.5), "font_size": 8, "font": "Times New Roman"},
    "GRL": {"dpi": 300, "figure_size": (6, 4), "font_size": 10, "font": "Arial"},
    "JCLI": {"dpi": 300, "figure_size": (6, 4), "font_size": 9, "font": "Arial"},
    "Custom": {"dpi": 300, "figure_size": (6, 4), "font_size": 10, "font": "sans-serif"},
}

# ─── ENSO / PWC boxes (longitude in 0-360 format) ───────────────────────────
BUILTIN_BOXES = {
    "Nino1+2": {"lat": (-10, 0), "lon": (270, 280)},
    "Nino3": {"lat": (-5, 5), "lon": (210, 270)},
    "Nino3.4": {"lat": (-5, 5), "lon": (190, 240)},
    "Nino4": {"lat": (-5, 5), "lon": (160, 210)},
}

DIFF_BOXES = {
    "PWC-U850": {
        "var": "U850",
        "west": {"lat": (-5, 5), "lon": (130, 160)},
        "east": {"lat": (-5, 5), "lon": (200, 230)},
    }
}

# ─── Index metadata and citations ────────────────────────────────────────────
INDEX_INFO_FILE = "indices/index_citations.yml"

# Default index information
INDEX_INFO = {
    "Nino3.4": {
        "authors": "Trenberth, K. E.",
        "year": 1997,
        "title": "The definition of El Niño",
        "journal": "Bulletin of the American Meteorological Society",
        "doi": "10.1175/1520-0477(1997)078<2771:TDOENO>2.0.CO;2",
        "desc": "Sea surface temperature anomaly in the Niño 3.4 region (5°N-5°S, 120°-170°W)",
    },
    "Nino3": {
        "authors": "Rasmusson, E. M., & Carpenter, T. H.",
        "year": 1982,
        "title": "Variations in tropical sea surface temperature and surface wind fields associated with the Southern Oscillation/El Niño",
        "journal": "Monthly Weather Review",
        "doi": "10.1175/1520-0493(1982)110<0354:VITSST>2.0.CO;2",
        "desc": "Sea surface temperature anomaly in the Niño 3 region (5°N-5°S, 90°-150°W)",
    },
}

# ─── Matplotlib journal context manager ─────────────────────────────────────
_DEFAULT_RC = mpl.rcParams.copy()

class JournalStyle:
    def __init__(self, preset):
        self.preset = preset
    
    def __enter__(self):
        mpl.rcParams.update({
            "figure.dpi": self.preset["dpi"],
            "font.family": self.preset["font"],
            "font.size": self.preset["font_size"],
            "axes.titlesize": self.preset["font_size"] + 2,
            "axes.labelsize": self.preset["font_size"],
            "xtick.labelsize": self.preset["font_size"] - 1,
            "ytick.labelsize": self.preset["font_size"] - 1,
        })
        return self
    
    def __exit__(self, *args):
        mpl.rcParams.update(_DEFAULT_RC)

def apply_journal_style(preset):
    return JournalStyle(preset)

# ─── Data loading ────────────────────────────────────────────────────────────
def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    """Load NetCDF dataset with optional chunking."""
    try:
        return xr.open_dataset(path, chunks=chunks)
    except ImportError:
        # Fallback if dask is not available
        return xr.open_dataset(path)

# ─── Index calculation helpers ───────────────────────────────────────────────
def _area_mean(da: xr.DataArray, lat_range: tuple, lon_range: tuple) -> xr.DataArray:
    """Calculate area-weighted mean over lat/lon box."""
    # Handle longitude wrapping
    if lon_range[0] > lon_range[1]:  # crosses 0 meridian
        lon_sel = da.sel(lon=slice(lon_range[0], 360)).append(
            da.sel(lon=slice(0, lon_range[1]))
        )
        sub = lon_sel.sel(lat=slice(*lat_range))
    else:
        sub = da.sel(lat=slice(*lat_range), lon=slice(*lon_range))
    
    # Area weighting by cosine of latitude
    weights = np.cos(np.deg2rad(sub.lat))
    return sub.weighted(weights).mean(("lat", "lon"))

def compute_index(ds: xr.Dataset, var: str, name: str, boxes: dict) -> xr.DataArray:
    """Compute climate index from dataset."""
    da = ds[var]
    
    if name == "Raw":
        return da
    elif name == "Global Mean":
        if {"lat", "lon"}.issubset(da.coords):
            return _area_mean(da, (-90, 90), (0, 360))
        else:
            return da.mean()
    elif name in boxes:
        box = boxes[name]
        return _area_mean(da, box["lat"], box["lon"])
    elif name in DIFF_BOXES:
        meta = DIFF_BOXES[name]
        if var != meta["var"]:
            raise ValueError(f"{name} requires variable {meta['var']}, got {var}")
        west_mean = _area_mean(da, **meta["west"])
        east_mean = _area_mean(da, **meta["east"])
        return west_mean - east_mean
    else:
        raise ValueError(f"Unknown index: {name}")

def _clean_data(da: xr.DataArray) -> xr.DataArray:
    """Remove invalid values from data array."""
    # Remove NaN, inf, and fill values
    mask = np.isfinite(da) & (np.abs(da) < 1e30)
    
    # Handle fill values from attributes
    for attr in ("_FillValue", "missing_value"):
        if attr in da.attrs:
            fill_val = da.attrs[attr]
            mask = mask & (da != fill_val)
    
    return da.where(mask)

# ─── Color bar utilities ─────────────────────────────────────────────────────
def _cbar_kwargs(da: xr.DataArray, mode: str, vmin: Optional[float], vmax: Optional[float]) -> dict:
    """Get colorbar keyword arguments based on mode."""
    mode = mode.lower()
    
    if mode == "manual" and vmin is not None and vmax is not None:
        return {"vmin": vmin, "vmax": vmax}
    elif mode == "robust":
        return {"robust": True}
    elif mode == "symmetric":
        max_val = float(np.nanmax(np.abs(da)))
        return {"vmin": -max_val, "vmax": max_val}
    else:  # auto
        return {}

def _fig_to_buffer(fig: plt.Figure, dpi: int) -> io.BytesIO:
    """Convert matplotlib figure to PNG buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf

# ─── Time series plotting ────────────────────────────────────────────────────
def _calculate_trend(x: np.ndarray, y: np.ndarray) -> tuple:
    """Calculate linear trend and statistics."""
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    fitted = slope * x + intercept
    correlation = np.corrcoef(y, fitted)[0, 1]
    r_squared = correlation ** 2
    return fitted, slope, intercept, r_squared

def plot_timeseries(
    ds: xr.Dataset,
    var: str,
    indices: list,
    time_slice: slice,
    preset: dict,
    boxes: dict,
    custom_caption: str = "",
    trendline: bool = False,
) -> tuple:
    """Plot time series for selected indices."""
    
    with apply_journal_style(preset):
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        
        notes = []
        time_vals = ds["time"].sel(time=time_slice).values
        
        # Convert time to numeric for trend calculation
        time_numeric = time_vals.astype("datetime64[s]").astype(float)
        
        for idx_name in indices:
            # Compute index
            da = compute_index(ds, var, idx_name, boxes).sel(time=time_slice)
            
            # Average over non-time dimensions if needed
            extra_dims = [d for d in da.dims if d != "time"]
            if extra_dims:
                da = da.mean(dim=extra_dims)
            
            # Clean data
            da = _clean_data(da)
            
            # Calculate statistics
            mean_val = float(da.mean())
            std_val = float(da.std())
            
            # Plot time series
            line, = ax.plot(time_vals, da, label=idx_name, linewidth=1.5)
            color = line.get_color()
            
            # Add shaded standard deviation
            ax.fill_between(time_vals, da - std_val, da + std_val, 
                          alpha=0.2, color=color)
            
            # Add mean line
            ax.axhline(mean_val, linestyle=":", linewidth=1, color=color, alpha=0.7)
            
            # Add trend line if requested
            if trendline:
                fitted, slope, _, r2 = _calculate_trend(time_numeric, da.values)
                ax.plot(time_vals, fitted, linestyle="--", color=color, alpha=0.8)
                notes.append(f"**{idx_name}**: μ={mean_val:.3g}, σ={std_val:.3g}, "
                           f"trend={slope:.2e}/yr, R²={r2:.3f}")
            else:
                notes.append(f"**{idx_name}**: μ={mean_val:.3g}, σ={std_val:.3g}")
        
        # Formatting
        ax.set_ylabel(f"{var} [{ds[var].attrs.get('units', '')}]")
        ax.set_title(f"{', '.join(indices)} - {var}")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=preset["font_size"])
        
        # Caption
        caption = "; ".join(notes)
        if custom_caption:
            caption += f". {custom_caption}"
        
        # Add caption below figure
        fig.text(0.5, -0.08, caption, ha="center", va="top", 
                fontsize=preset["font_size"], wrap=True)
        
        fig.tight_layout(rect=(0, 0.05, 1, 1))
    
    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# ─── Spatial map plotting ────────────────────────────────────────────────────
def _create_geo_axes(preset: dict) -> tuple:
    """Create axes with optional cartopy projection."""
    if HAS_CARTOPY:
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(figsize=preset["figure_size"], 
                              subplot_kw={"projection": proj})
        ax.coastlines(resolution="110m", linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3)
        return fig, ax, proj
    else:
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        return fig, ax, None

def _draw_index_boxes(ax, proj, indices: list, boxes: dict, show_boxes: bool):
    """Draw index region boxes on map."""
    if not show_boxes:
        return
    
    for idx_name in indices:
        if idx_name in boxes:
            box = boxes[idx_name]
            lat_range, lon_range = box["lat"], box["lon"]
            
            # Create rectangle coordinates
            lons = [lon_range[0], lon_range[1], lon_range[1], lon_range[0], lon_range[0]]
            lats = [lat_range[0], lat_range[0], lat_range[1], lat_range[1], lat_range[0]]
            
            plot_kwargs = {"linestyle": "--", "linewidth": 1.5, "color": "black", "alpha": 0.8}
            
            if proj:
                ax.plot(lons, lats, transform=ccrs.PlateCarree(), **plot_kwargs)
            else:
                ax.plot(lons, lats, **plot_kwargs)

def plot_spatial_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: dict,
    cmap: str,
    indices: list,
    boxes: dict,
    cbar_mode: str,
    vmin: Optional[float],
    vmax: Optional[float],
    show_boxes: bool,
    user_caption: str = "",
) -> tuple:
    """Plot spatial mean map."""
    
    # Calculate time mean
    da = ds[var].sel(time=time_slice).mean("time")
    da = _clean_data(da)
    
    with apply_journal_style(preset):
        fig, ax, proj = _create_geo_axes(preset)
        
        # Plot data
        cbar_kws = _cbar_kwargs(da, cbar_mode, vmin, vmax)
        
        if {"lat", "lon"}.issubset(da.dims):
            im = da.plot(ax=ax, cmap=cmap, add_colorbar=True, 
                        transform=proj if proj else None, **cbar_kws)
        else:
            im = ax.imshow(da.values, cmap=cmap, **cbar_kws)
            plt.colorbar(im, ax=ax)
        
        # Draw index boxes
        _draw_index_boxes(ax, proj, indices, boxes, show_boxes)
        
        # Title and formatting
        units = ds[var].attrs.get("units", "")
        ax.set_title(f"Mean {var} ({units})")
        
        # Caption
        start_date = str(time_slice.start)[:10] if time_slice.start else "start"
        stop_date = str(time_slice.stop)[:10] if time_slice.stop else "end"
        caption = f"Spatial mean of **{var}** from {start_date} to {stop_date}."
        if user_caption:
            caption += f" {user_caption}"
        
        fig.text(0.5, -0.08, caption, ha="center", va="top", 
                fontsize=preset["font_size"], wrap=True)
        
        fig.tight_layout(rect=(0, 0.05, 1, 1))
    
    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

def plot_trend_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: dict,
    cmap: str,
    indices: list,
    boxes: dict,
    cbar_mode: str,
    vmin: Optional[float],
    vmax: Optional[float],
    show_boxes: bool,
    user_caption: str = "",
) -> tuple:
    """Plot trend map."""
    
    # Calculate linear trend
    da_slice = ds[var].sel(time=time_slice)
    trend_da = da_slice.polyfit("time", 1)["polyfit_coefficients"].sel(degree=0)
    trend_da = trend_da.rename(var)
    trend_da = _clean_data(trend_da)
    
    with apply_journal_style(preset):
        fig, ax, proj = _create_geo_axes(preset)
        
        # Plot trend
        cbar_kws = _cbar_kwargs(trend_da, cbar_mode, vmin, vmax)
        
        if {"lat", "lon"}.issubset(trend_da.dims):
            im = trend_da.plot(ax=ax, cmap=cmap, add_colorbar=True,
                              transform=proj if proj else None, **cbar_kws)
        else:
            im = ax.imshow(trend_da.values, cmap=cmap, **cbar_kws)
            plt.colorbar(im, ax=ax)
        
        # Draw index boxes
        _draw_index_boxes(ax, proj, indices, boxes, show_boxes)
        
        # Title and formatting
        units = ds[var].attrs.get("units", "")
        ax.set_title(f"Trend in {var} ({units}/time)")
        
        # Caption
        start_date = str(time_slice.start)[:10] if time_slice.start else "start"
        stop_date = str(time_slice.stop)[:10] if time_slice.stop else "end"
        caption = f"Linear trend of **{var}** from {start_date} to {stop_date}."
        if user_caption:
            caption += f" {user_caption}"
        
        fig.text(0.5, -0.08, caption, ha="center", va="top",
                fontsize=preset["font_size"], wrap=True)
        
        fig.tight_layout(rect=(0, 0.05, 1, 1))
    
    return fig, _fig_to_buffer(fig, preset["dpi"]), caption

# ─── Citation management ─────────────────────────────────────────────────────
def load_index_info() -> dict:
    """Load index information from YAML file."""
    if os.path.exists(INDEX_INFO_FILE):
        try:
            with open(INDEX_INFO_FILE, 'r') as f:
                loaded_info = yaml.safe_load(f) or {}
            # Merge with defaults
            return {**INDEX_INFO, **loaded_info}
        except Exception:
            pass
    return INDEX_INFO.copy()

def save_citations():
    """Save current INDEX_INFO to YAML file."""
    os.makedirs(os.path.dirname(INDEX_INFO_FILE), exist_ok=True)
    with open(INDEX_INFO_FILE, 'w') as f:
        yaml.dump(INDEX_INFO, f, default_flow_style=False)

def list_index_info() -> dict:
    """Get all index information."""
    return load_index_info()

def format_citation(style: str, meta: dict) -> str:
    """Format citation in specified style."""
    authors = meta.get("authors", "Unknown")
    year = meta.get("year", "Unknown")
    title = meta.get("title", "Unknown")
    journal = meta.get("journal", "Unknown")
    doi = meta.get("doi", "")
    
    if style == "Nature":
        citation = f"{authors} {title}. {journal} ({year})"
    elif style == "Science":
        citation = f"{authors}, {title}. {journal} {year}"
    elif style == "AGU":
        citation = f"{authors} ({year}), {title}, {journal}"
    elif style == "APA":
        citation = f"{authors} ({year}). {title}. {journal}."
    else:
        citation = f"{authors} ({year}). {title}. {journal}."
    
    if doi:
        citation += f" DOI: {doi}"
    
    return citation
```

