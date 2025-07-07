# -*- coding: utf-8 -*-
"""
CESM Analysis Utilities - Complete Version
"""
import cftime
import io
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, Any, Union, Optional, List, Tuple

# Cartopy setup with fallback
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False
    ccrs = None
    cfeature = None
    print("Cartopy not available - using simple projections")

# Journal quality presets
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature": {
        "dpi": 600,
        "figure_size": (7, 5),
        "font_size": 8,
        "font": "Helvetica",
        "map": {
            "coastline": {"linewidth": 0.5, "color": "black"},
            "borders": {"linewidth": 0.3, "color": "gray"},
            "gridlines": {"linewidth": 0.2, "color": "gray", "alpha": 0.5},
            "land_color": "whitesmoke",
            "ocean_color": "lightcyan"
        }
    },
    "Science": {
        "dpi": 600,
        "figure_size": (6.5, 4.5),
        "font_size": 8,
        "font": "Times New Roman",
        "map": {
            "coastline": {"linewidth": 0.6, "color": "#222222"},
            "borders": {"linewidth": 0.4, "color": "#444444"},
            "gridlines": {"linewidth": 0.25, "color": "#666666", "alpha": 0.4},
            "land_color": "#f5f5f5",
            "ocean_color": "#e6f2ff"
        }
    }
}

# Region definitions
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

def load_dataset(path: str, chunks: Union[str, dict, None] = "auto") -> xr.Dataset:
    """Load NetCDF dataset with optional chunking"""
    try:
        ds = xr.open_dataset(path, chunks=chunks)
        if 'time' in ds.dims:
            ds['time'] = xr.decode_cf(ds).time
        return ds
    except Exception as e:
        raise ValueError(f"Error loading {path}: {str(e)}")

def _area_mean(da: xr.DataArray, lat: tuple, lon: tuple) -> xr.DataArray:
    """Calculate area-weighted mean"""
    sub = da.sel(lat=slice(*lat), lon=slice(*lon))
    weights = np.cos(np.deg2rad(sub.lat))
    return sub.weighted(weights).mean(("lat", "lon"))

def compute_index(ds: xr.Dataset, var: str, name: str, boxes: dict) -> xr.DataArray:
    """Compute climate indices"""
    da = ds[var]
    if name == "Raw":
        return da
    if name == "Global Mean":
        if {"lat", "lon"}.issubset(da.coords):
            return _area_mean(da, (-90, 90), (0, 360))
        return da.mean()
    if name in boxes:
        box = boxes[name]
        return _area_mean(da, box["lat"], box["lon"])
    if name in DIFF_BOXES:
        meta = DIFF_BOXES[name]
        if var != meta["var"]:
            raise ValueError(f"{name} requires variable {meta['var']}")
        west = _area_mean(da, **meta["west"])
        east = _area_mean(da, **meta["east"])
        return west - east
    raise ValueError(f"Unknown index: {name}")

def _journal_style(preset: dict):
    """Context manager for journal styling"""
    class StyleContext:
        def __enter__(self):
            mpl.rcParams.update({
                "figure.dpi": preset["dpi"],
                "font.family": preset["font"],
                "font.size": preset["font_size"],
                "axes.titlesize": preset["font_size"] + 2,
                "axes.labelsize": preset["font_size"]
            })
        def __exit__(self, *args):
            mpl.rcParams.update(mpl.rcParamsDefault)
    return StyleContext()

def _fig_buf(fig: plt.Figure, dpi: int) -> io.BytesIO:
    """Convert figure to bytes buffer"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    return buf

def plot_timeseries(
    ds: xr.Dataset,
    var: str,
    indices: List[str],
    time_slice: slice,
    preset: dict,
    boxes: dict,
    caption: Optional[str] = None,
    show_trend: bool = False
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Generate time series plot"""
    with _journal_style(preset):
        fig, ax = plt.subplots(figsize=preset["figure_size"])
        
        stats = []
        for idx_name in indices:
            da = compute_index(ds, var, idx_name, boxes).sel(time=time_slice)
            if len(da.dims) > 1:
                da = da.mean(dim=[d for d in da.dims if d != "time"])
            
            line = ax.plot(da.time, da, label=idx_name, lw=1.5)
            
            if show_trend:
                x = da.time.astype('datetime64[s]').astype(float)
                y = da.values
                coeffs = np.polyfit(x, y, 1)
                trend = np.poly1d(coeffs)(x)
                ax.plot(da.time, trend, '--', color=line[0].get_color(), lw=1)
                stats.append(f"{idx_name} trend: {coeffs[0]:.2e} per unit time")
        
        ax.set_title(f"{var} Time Series\n{time_slice.start} to {time_slice.stop}")
        ax.legend(fontsize=preset["font_size"]-1)
        ax.grid(True, ls=':', alpha=0.5)
        
        return fig, _fig_buf(fig, preset["dpi"]), "\n".join(stats)

def plot_spatial_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: dict,
    cmap: str,
    indices: List[str],
    boxes: dict,
    show_boxes: bool = True,
    user_caption: Optional[str] = None
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Generate spatial map plot"""
    with _journal_style(preset):
        da = ds[var].sel(time=time_slice).mean("time")
        
        if HAS_CARTOPY:
            fig = plt.figure(figsize=preset["figure_size"])
            ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND, facecolor=preset["map"]["land_color"])
            ax.add_feature(cfeature.OCEAN, facecolor=preset["map"]["ocean_color"])
            ax.coastlines(**preset["map"]["coastline"])
        else:
            fig, ax = plt.subplots(figsize=preset["figure_size"])
        
        im = da.plot(
            ax=ax,
            cmap=cmap,
            add_colorbar=False,
            robust=True
        )
        
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(f"{var} [{da.attrs.get('units', '')}]")
        
        if show_boxes:
            for idx_name in indices:
                if idx_name in boxes:
                    box = boxes[idx_name]
                    lat, lon = box["lat"], box["lon"]
                    ax.plot(
                        [lon[0], lon[1], lon[1], lon[0], lon[0]],
                        [lat[0], lat[0], lat[1], lat[1], lat[0]],
                        'k--', linewidth=1
                    )
        
        title = f"{var} Spatial Mean\n{time_slice.start} to {time_slice.stop}"
        ax.set_title(title)
        
        caption = f"Spatial mean of {var} ({time_slice.start} to {time_slice.stop})"
        if user_caption:
            caption += f" | {user_caption}"
            
        return fig, _fig_buf(fig, preset["dpi"]), caption

def plot_trend_map(
    ds: xr.Dataset,
    var: str,
    time_slice: slice,
    preset: dict,
    cmap: str,
    indices: List[str],
    boxes: dict,
    show_boxes: bool = True
) -> Tuple[plt.Figure, io.BytesIO, str]:
    """Generate trend map plot"""
    with _journal_style(preset):
        # Calculate trend over time
        trend_data = ds[var].sel(time=time_slice).polyfit("time", 1)
        trend_slope = trend_data["polyfit_coefficients"].sel(degree=1)
        
        if HAS_CARTOPY:
            fig = plt.figure(figsize=preset["figure_size"])
            ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
            ax.add_feature(cfeature.LAND, facecolor=preset["map"]["land_color"])
            ax.add_feature(cfeature.OCEAN, facecolor=preset["map"]["ocean_color"])
            ax.coastlines(**preset["map"]["coastline"])
        else:
            fig, ax = plt.subplots(figsize=preset["figure_size"])
        
        im = trend_slope.plot(
            ax=ax,
            cmap=cmap,
            add_colorbar=False
        )
        
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label(f"{var} trend [{ds[var].attrs.get('units', '')}/time]")
        
        if show_boxes:
            for idx_name in indices:
                if idx_name in boxes:
                    box = boxes[idx_name]
                    lat, lon = box["lat"], box["lon"]
                    ax.plot(
                        [lon[0], lon[1], lon[1], lon[0], lon[0]],
                        [lat[0], lat[0], lat[1], lat[1], lat[0]],
                        'k--', linewidth=1
                    )
        
        title = f"{var} Trend\n{time_slice.start} to {time_slice.stop}"
        ax.set_title(title)
        
        caption = f"Trend of {var} ({time_slice.start} to {time_slice.stop})"
            
        return fig, _fig_buf(fig, preset["dpi"]), caption
