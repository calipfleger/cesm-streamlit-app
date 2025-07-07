# ---- app.py ----
"""
CESM Streamlit Workbook front-end
---------------------------------

• Variable/Index selector (supports ENSO family & PWC indices from cesm_utils)
• Citation Style dropdown (Nature | Science | AGU | APA)
• Four tabs:   📈 Time-Series | 🗺 Spatial Map | 🔭 Trend Map | 📚 About Indices
• About tab shows description + properly-formatted reference for each index
  and includes a session-level form to add / edit citation meta-data.
"""

from __future__ import annotations
import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt

from cesm_utils import (
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    DIFF_BOXES,           # PWC index list
    list_index_info,
    format_citation,
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
)

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page setup
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CESM Interactive Workbook", layout="wide")
st.title("CESM / iCESM Interactive Workbook")

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – file picker (local `data/` dir for now)
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
nc_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".nc")]

if not nc_files:
    st.sidebar.warning("No NetCDF files found in ./data. Add one and rerun.")
    st.stop()

file_path = os.path.join(DATA_DIR, st.sidebar.selectbox("📄 NetCDF dataset", nc_files))

@st.cache_data(show_spinner=True)
def _load(p: str) -> xr.Dataset:
    return load_dataset(p)

ds = _load(file_path)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – variable & index controls
# ─────────────────────────────────────────────────────────────────────────────
variables = list(ds.data_vars)
var = st.sidebar.selectbox("🌡 Variable", variables)

# Combine built-in mean boxes + diff indices
index_options = (
    ["Raw", "Global Mean"]
    + list(BUILTIN_BOXES.keys())
    + list(DIFF_BOXES.keys())
)
indices = st.sidebar.multiselect("📊 Indices", index_options, default=["Raw"])

trendline = st.sidebar.checkbox("Add trendline to time-series", value=False)

# Colormap & colour-bar controls
cmap = st.sidebar.selectbox("🎨 Colormap", sorted(plt.colormaps()))
cbar_mode = st.sidebar.radio("Color-bar Mode", ["Auto", "Robust", "Symmetric", "Manual"])
vmin = vmax = None
if cbar_mode == "Manual":
    vmin = st.sidebar.number_input("vmin")
    vmax = st.sidebar.number_input("vmax")

show_boxes = st.sidebar.checkbox("Display index boxes on maps", value=True)
custom_caption = st.sidebar.text_area("Custom caption (optional)")

# Citation style selector
citation_style = st.sidebar.selectbox("Citation style", ["Nature", "Science", "AGU", "APA"])

journal = st.sidebar.selectbox("Journal preset", list(JOURNAL_PRESETS.keys()))
preset = JOURNAL_PRESETS[journal]

# Time slider
tvals = ds["time"].values
t_idx = st.sidebar.slider("Time range", 0, len(tvals) - 1, (0, len(tvals) - 1), format="")
t_slice = slice(tvals[t_idx[0]], tvals[t_idx[1]])

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_ts, tab_map, tab_trend, tab_about = st.tabs(
    ["📈 Time-Series", "🗺 Spatial Map", "🔭 Trend Map", "📚 About Indices"]
)

with tab_ts:
    fig, buf, cap = plot_timeseries(
        ds, var, indices, t_slice, preset, {**BUILTIN_BOXES},  # boxes dict
        user_caption=custom_caption, show_trendline=trendline
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, "timeseries.png")
    st.caption(cap)

with tab_map:
    fig, buf, cap = plot_spatial_map(
        ds, var, t_slice, preset, cmap, indices, BUILTIN_BOXES,
        cbar_mode, vmin, vmax, show_boxes, user_caption=custom_caption
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, "spatial_map.png")
    st.caption(cap)

with tab_trend:
    fig, buf, cap = plot_trend_map(
        ds, var, t_slice, preset, cmap, indices, BUILTIN_BOXES,
        cbar_mode, vmin, vmax, show_boxes, user_caption=custom_caption
    )
    st.pyplot(fig)
    st.download_button("Download PNG", buf, "trend_map.png")
    st.caption(cap)

# ─────────────────────────────────────────────────────────────────────────────
# About Indices – description + formatted citation
# ─────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("## Index definitions & references")
    info = list_index_info()
    for name, meta in info.items():
        ref = format_citation(citation_style, meta)
        st.markdown(
            f"### {name}\n"
            f"{meta['desc']}\n\n"
            f"**Reference** ({citation_style}): {ref}"
        )

    st.markdown("---")
    st.markdown("### Add / edit citation (session only)")
    c_key  = st.text_input("Index key")
    col1, col2 = st.columns(2)
    c_auth = col1.text_input("Authors")
    c_year = col2.number_input("Year", min_value=1900, max_value=2100, value=2025)
    c_title = st.text_input("Paper title")
    c_jour  = st.text_input("Journal")
    c_doi   = st.text_input("DOI or URL")
    c_desc  = st.text_area("Short description")
    if st.button("Save citation"):
        if c_key:
            from cesm_utils import INDEX_INFO          # late import to mutate global
            INDEX_INFO[c_key] = {
                "authors": c_auth, "year": c_year, "title": c_title,
                "journal": c_jour, "doi": c_doi, "desc": c_desc, "var": var
            }
            st.success(f"{c_key} updated (session only).  Reload to persist YAML once coded.")

