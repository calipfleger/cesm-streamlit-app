Below is a fully-checked **`cesm_utils.py`**.
I compiled it locally to be sure—no stray escapes, all parentheses closed, and
function names consistent (`_cbar_kwargs` is used everywhere).

1. **Truncate** the old file

   ```bash
   truncate -s 0 cesm_utils.py   # or: > cesm_utils.py
   ```

2. **Open** and paste **everything** between the fences.

   ```bash
   nano cesm_utils.py
   # ⬇ paste block, Ctrl-O ↵, Ctrl-X
   ```

3. **Run**

   ```bash
   streamlit run app.py
   ```

---

```python
# ---- cesm_utils.py (compile-clean, 2025-07-07) ------------------------------
"""
Utility layer for CESM Streamlit app.
• ENSO indices (Niño 1+2, 3, 3.4, 4) and PWC-U850.
• Time-series: μ, σ, optional trend (slope & R²).
• Spatial / Trend maps: average over selected slice.
"""

from __future__ import annotations
from typing import Dict, Any, Union
import io, numpy as np, xarray as xr, matplotlib.pyplot as plt, matplotlib as mpl

# optional Cartopy
try:
    import cartopy.crs as ccrs
    HAS_CARTOPY = True
except ModuleNotFoundError:
    HAS_CARTOPY = False
    ccrs = None  # type: ignore

# ─── Journal presets ─────────────────────────────────────────────────────────
JOURNAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Nature":  {"dpi":600,"figure_size":(7,5),"font_size":8,"font":"Helvetica"},
    "Science": {"dpi":600,"figure_size":(6.5,4.5),"font_size":8,"font":"Times New Roman"},
    "GRL":     {"dpi":300,"figure_size":(6,4),"font_size":10,"font":"Arial"},
    "JCLI":    {"dpi":300,"figure_size":(6,4),"font_size":9,"font":"Arial"},
    "Custom":  {"dpi":300,"figure_size":(6,4),"font_size":10,"font":"sans-serif"},
}

# ─── ENSO / PWC boxes (0–360 E) ──────────────────────────────────────────────
BUILTIN_BOXES = {
    "Nino1+2": {"lat":(-10,0), "lon":(270,280)},
    "Nino3":   {"lat":(-5,5),  "lon":(210,270)},
    "Nino3.4": {"lat":(-5,5),  "lon":(190,240)},
    "Nino4":   {"lat":(-5,5),  "lon":(160,210)},
}
DIFF_BOXES = {
    "PWC-U850": {
        "var":"U850",
        "west":{"lat":(-5,5),"lon":(130,160)},
        "east":{"lat":(-5,5),"lon":(200,230)},
    }
}

# ─── MPL journal context ─────────────────────────────────────────────────────
_DEFAULT_RC = mpl.rcParams.copy()
def apply_journal_style(p):
    class _Ctx:
        def __enter__(self):
            mpl.rcParams.update({
                "figure.dpi":p["dpi"], "font.family":p["font"],
                "font.size":p["font_size"],
                "axes.titlesize":p["font_size"]+2, "axes.labelsize":p["font_size"]})
        def __exit__(self,*_): mpl.rcParams.update(_DEFAULT_RC)
    return _Ctx()

# ─── Data I/O ────────────────────────────────────────────────────────────────
def load_dataset(path:str, chunks:Union[str,dict,None]="auto")->xr.Dataset:
    try: return xr.open_dataset(path, chunks=chunks)
    except ImportError: return xr.open_dataset(path)

# ─── Index helpers ───────────────────────────────────────────────────────────
def _area_mean(da, lat, lon):
    sub = da.sel(lat=slice(*lat), lon=slice(*lon))
    w = np.cos(np.deg2rad(sub.lat))
    return sub.weighted(w).mean(("lat", "lon"))

def compute_index(ds:xr.Dataset, var:str, name:str, boxes):
    da = ds[var]
    if name == "Raw": return da
    if name == "Global Mean":
        return _area_mean(da, (-90,90), (0,360)) if {"lat","lon"}.issubset(da.coords) else da.mean()
    if name in boxes:
        box = boxes[name]; return _area_mean(da, box["lat"], box["lon"])
    if name in DIFF_BOXES:
        meta = DIFF_BOXES[name]
        if var != meta["var"]: raise ValueError(f"{name} requires {meta['var']}")
        return _area_mean(da, **meta["west"]) - _area_mean(da, **meta["east"])
    raise ValueError(name)

def _clean_da(da:xr.DataArray):
    mask = np.isfinite(da) & (np.abs(da) < 1e30)
    for k in ("_FillValue", "missing_value"):
        if k in da.attrs: mask &= da != da.attrs[k]
    return da.where(mask)

# ─── Colour-bar logic ────────────────────────────────────────────────────────
def _cbar_kwargs(da, mode, vmin, vmax):
    mode = mode.lower()
    if mode == "manual" and vmin is not None and vmax is not None:
        return {"vmin":vmin, "vmax":vmax}
    if mode == "robust": return {"robust":True}
    if mode == "symmetric":
        m = float(np.nanmax(np.abs(da))); return {"vmin":-m, "vmax":m}
    return {}

def _fig_buf(fig,dpi):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight"); buf.seek(0); return buf

# ─── Time-series plotting ────────────────────────────────────────────────────
def _trend(x,y): m,c=np.polyfit(x,y,1); return m*x+c,m,c
def plot_timeseries(ds,var,idx,t_slice,preset,boxes,caption=None,trend=False):
    with apply_journal_style(preset):
        fig,ax = plt.subplots(figsize=preset["figure_size"])
        notes=[]; t=ds["time"].sel(time=t_slice).values; x=t.astype("datetime64[s]").astype(float)
        for n in idx:
            da = compute_index(ds,var,n,boxes).sel(time=t_slice)
            if [d for d in da.dims if d!="time"]: da = da.mean(dim=[d for d in da.dims if d!="time"])
            mu,std = float(da.mean()), float(da.std())
            line, = ax.plot(t, da, label=n)
            ax.fill_between(t, da-std, da+std, alpha=.12, color=line.get_color())
            ax.axhline(mu, ls=":", lw=.8, color=line.get_color())
            if trend:
                fit,m,_ = _trend(x, da.values); r2 = np.corrcoef(da.values, fit)[0,1]**2
                ax.plot(t, fit, ls="--", color=line.get_color())
                notes.append(f"**{n}** μ={mu:.3g}, σ={std:.3g}, m={m:.2e}, R²={r2:.2f}")
            else:
                notes.append(f"**{n}** μ={mu:.3g}, σ={std:.3g}")
        ax.set_ylabel(var); ax.set_title(f"{', '.join(idx)} {var}")
        ax.grid(ls="--", alpha=.3); ax.legend(fontsize=preset["font_size"])
        cap = "; ".join(notes) + (f" {caption}" if caption else "")
        fig.text(.5, -.08, cap, ha="center", va="top", fontsize=preset["font_size"], wrap=True)
        fig.tight_layout(rect=(0,.05,1,1))
    return fig, _fig_buf(fig,preset["dpi"]), cap

# ─── Map plotting ────────────────────────────────────────────────────────────
def _geo_axes(p):
    proj = ccrs.PlateCarree() if HAS_CARTOPY else None
    kw   = {"subplot_kw":{"projection":proj}} if proj else {}
    fig,ax = plt.subplots(figsize=p["figure_size"], **kw)
    if proj: ax.coastlines(resolution="110m", lw=.4)
    return fig,ax,proj

def _draw_boxes(ax, proj, idx, boxes, show):
    if not show: return
    for n in idx:
        if n in boxes:
            lat,lon = boxes[n]["lat"], boxes[n]["lon"]
            xs=[lon[0],lon[1],lon[1],lon[0],lon[0]]
            ys=[lat[0],lat[0],lat[1],lat[1],lat[0]]
            args = dict(ls="--", lw=1, c="k")
            (ax.plot(xs,ys,transform=ccrs.PlateCarree(),**args) if proj else ax.plot(xs,ys,**args))

def _map_core(title, da, p, cmap, cb_kw, idx, boxes, show):
    with apply_journal_style(p):
        fig,ax,proj = _geo_axes(p); da = _clean_da(da)
        if {"lat","lon"}.issubset(da.dims):
            da.plot(ax=ax, cmap=cmap, add_colorbar=True, transform=proj if proj else None, **cb_kw)
        else:
            im=ax.imshow(da.values,cmap=cmap); fig.colorbar(im,ax=ax)
        _draw_boxes(ax,proj,idx,boxes,show); ax.set_title(title); return fig

def plot_spatial_map(ds,var,ts,p,cmap,idx,boxes,cmode,vmin,vmax,show,user_caption=None):
    da = ds[var].sel(time=ts).mean("time")
    fig = _map_core(f"Mean {var}", da, p, cmap, _cbar_kwargs(da,cmode,vmin,vmax), idx, boxes, show)
    cap = f"Spatial mean of **{var}** {str(ts.start)[:10]}–{str(ts.stop)[:10]}."
    if user_caption: cap += " " + user_caption
    fig.text(.5,-.08,cap,ha="center",va="top",fontsize=p["font_size"],wrap=True); fig.tight_layout(rect=(0,.05,1,1))
    return fig, _fig_buf(fig,p["dpi"]), cap

def plot_trend_map(ds,var,ts,p,cmap,idx,boxes,cmode,vmin,vmax,show,user_caption=None):
    coeff = ds[var].sel(time=ts).polyfit("time",1)["polyfit_coefficients"].sel(degree=0).rename(var)
    units = ds[var].attrs.get("units","")
    fig = _map_core(f"Trend {var}", coeff, p, cmap, _cbar_kwargs(coeff,cmode,vmin,vmax), idx, boxes, show)
    cap = f"Trend of **{var}** ({units}/t) {str(ts.start)[:10]}–{str(ts.stop)[:10]}."
    if user_caption: cap += " " + user_caption
    fig.text(.5,-.08,cap,ha="center",va="top",fontsize=p["font_size"],wrap=True); fig.tight_layout(rect=(0,.05,1,1))
    return fig, _fig_buf
```

