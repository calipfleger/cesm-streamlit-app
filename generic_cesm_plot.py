#!/usr/bin/env python
"""
generic_cesm_plot.py
====================

Generate time-series, spatial-mean, and trend-map figures for *any* NetCDF file
using the publication-ready helpers in `cesm_utils.py`.

Quick example
-------------
python generic_cesm_plot.py \
    --nc data/dummy.nc \
    --var PRECT \
    --indices Raw "Global Mean" Nino3.4 \
    --journal GRL \
    --cmap RdBu_r \
    --cbar Symmetric \
    --trendline \
    --outdir figs
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Tuple
import matplotlib.pyplot as plt

from cesm_utils import (
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
)

# ────────────────────────── CLI parsing ──────────────────────────────────────
def _cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch-plot CESM NetCDF figures.")
    p.add_argument("--nc", required=True, help="Path to NetCDF file")
    p.add_argument("--var", required=True, help="Variable name inside the file")
    p.add_argument("--indices", nargs="+", default=["Raw"], help="Indices to plot")
    p.add_argument("--journal", default="GRL", choices=JOURNAL_PRESETS, help="Journal preset")
    p.add_argument("--cmap", default="RdBu_r", help="Matplotlib colormap")
    p.add_argument("--cbar", default="Auto", choices=["Auto", "Robust", "Symmetric", "Manual"])
    p.add_argument("--vmin", type=float, help="vmin if --cbar Manual")
    p.add_argument("--vmax", type=float, help="vmax if --cbar Manual")
    p.add_argument("--trendline", action="store_true", help="Add trendline to time-series")
    p.add_argument("--outdir", default="figs", help="Directory to save PNGs")
    return p.parse_args()

# ────────────────────────── Figure factory ───────────────────────────────────
def make_figs(
    nc: str,
    var: str,
    idx: List[str],
    journal: str,
    cmap: str,
    cbar: str,
    vmin: float | None,
    vmax: float | None,
    trend: bool,
    outdir: str,
) -> Tuple[Path, Path, Path]:
    ds = load_dataset(nc)
    preset = JOURNAL_PRESETS[journal]
    boxes = BUILTIN_BOXES
    t_slice = slice(ds["time"].values[0], ds["time"].values[-1])
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # 1️⃣  Time-series - Fixed parameter name
    fig, _, _ = plot_timeseries(ds, var, idx, t_slice, preset, boxes, trendline=trend)
    ts_path = Path(outdir) / "timeseries.png"
    fig.savefig(ts_path, dpi=preset["dpi"], bbox_inches="tight")
    plt.close(fig)

    # 2️⃣  Spatial mean map
    fig, _, _ = plot_spatial_map(ds, var, t_slice, preset, cmap, idx, boxes, cbar, vmin, vmax, True)
    sm_path = Path(outdir) / "spatial_map.png"
    fig.savefig(sm_path, dpi=preset["dpi"], bbox_inches="tight")
    plt.close(fig)

    # 3️⃣  Trend map
    fig, _, _ = plot_trend_map(ds, var, t_slice, preset, cmap, idx, boxes, cbar, vmin, vmax, True)
    tr_path = Path(outdir) / "trend_map.png"
    fig.savefig(tr_path, dpi=preset["dpi"], bbox_inches="tight")
    plt.close(fig)

    return ts_path, sm_path, tr_path

# ────────────────────────── Script entry-point ───────────────────────────────
if __name__ == "__main__":
    args = _cli()
    outputs = make_figs(
        nc=args.nc,
        var=args.var,
        idx=args.indices,
        journal=args.journal,
        cmap=args.cmap,
        cbar=args.cbar,
        vmin=args.vmin,
        vmax=args.vmax,
        trend=args.trendline,
        outdir=args.outdir,
    )
    print("✓ Figures written to:", *map(str, outputs), sep="\n  ")

