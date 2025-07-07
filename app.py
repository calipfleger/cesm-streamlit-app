# ---- app.py ----
from __future__ import annotations

import os
import streamlit as st
import matplotlib.pyplot as plt

from cesm_utils import (
    JOURNAL_PRESETS,
    BUILTIN_BOXES,
    DIFF_BOXES,
    load_dataset,
    plot_timeseries,
    plot_spatial_map,
    plot_trend_map,
    list_index_info,
    format_citation,
    save_citations,
)

# ── Streamlit page config ────────────────────────────────────────────────────
st.set_page_config(page_title="CESM Workbook", layout="wide")
st.title("CESM / iCESM Interactive Workbook")

# ── Dataset picker ───────────────────────────────────────────────────────────
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
files = [f for f in os.listdir(DATA_DIR) if f.endswith(".nc")]

if not files:
    st.error("No NetCDF files in ./data")
    st.stop()

file_path = os.path.join(DATA_DIR, st.sidebar.selectbox("Dataset", files))


@st.cache_data(show_spinner=True)
def _load(path):
    return load_dataset(path)


ds = _load(file_path)

# ── Sidebar controls ────────────────────────────────────────────────────────
var = st.sidebar.selectbox("Variable", list(ds.data_vars))

BOXES = {**BUILTIN_BOXES, **DIFF_BOXES}
index_options = ["Raw", "Global Mean"] + list(BOXES.keys())
indices = st.sidebar.multiselect("Indices", index_options, default=["Raw"])

trendline = st.sidebar.checkbox("Add trendline", True)

cmap = st.sidebar.selectbox("Colormap", sorted(plt.colormaps()))
cbar_mode = st.sidebar.radio("Color-bar mode", ["Auto", "Robust", "Symmetric", "Manual"])
vmin = vmax = None
if cbar_mode == "Manual":
    vmin = st.sidebar.number_input("vmin")
    vmax = st.sidebar.number_input("vmax")

show_boxes = st.sidebar.checkbox("Show index boxes", True)
custom_caption = st.sidebar.text_area("Custom caption")

journal = st.sidebar.selectbox("Journal preset", list(JOURNAL_PRESETS.keys()))
preset = JOURNAL_PRESETS[journal]

citation_style = st.sidebar.selectbox("Citation style", ["Nature", "Science", "AGU", "APA"])

# Time slider
time_vals = ds["time"].values
lo, hi = st.sidebar.slider("Time slice", 0, len(time_vals) - 1, (0, len(time_vals) - 1), format="")
time_slice = slice(time_vals[lo], time_vals[hi])

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_ts, tab_map, tab_trend, tab_about = st.tabs(
    ["📈 Time-Series", "🗺 Spatial Map", "🔭 Trend Map", "📚 About Indices"]
)

with tab_ts:
    fig, buf, cap = plot_timeseries(
        ds,
        var,
        indices,
        time_slice,
        preset,
        BOXES,
        custom_caption,
        trendline,
    )
    st.pyplot(fig)
    st.download_button("PNG", buf, file_name="timeseries.png")
    st.caption(cap)

with tab_map:
    fig, buf, cap = plot_spatial_map(
        ds,
        var,
        time_slice,
        preset,
        cmap,
        indices,
        BOXES,
        cbar_mode,
        vmin,
        vmax,
        show_boxes,
        user_caption=custom_caption,
    )
    st.pyplot(fig)
    st.download_button("PNG", buf, file_name="spatial_mean.png")
    st.caption(cap)

with tab_trend:
    fig, buf, cap = plot_trend_map(
        ds,
        var,
        time_slice,
        preset,
        cmap,
        indices,
        BOXES,
        cbar_mode,
        vmin,
        vmax,
        show_boxes,
        user_caption=custom_caption,
    )
    st.pyplot(fig)
    st.download_button("PNG", buf, file_name="trend_map.png")
    st.caption(cap)

# ── About / citations tab ────────────────────────────────────────────────────
with tab_about:
    st.markdown("## Index definitions & references")
    for name, meta in list_index_info().items():
        ref = format_citation(citation_style, meta)
        st.markdown(
            f"### {name}\n"
            f"{meta.get('desc', '')}\n\n"
            f"**Reference** ({citation_style}): {ref}"
        )

    st.markdown("---")
    st.markdown("### Add / edit citation (persists to YAML)")
    key = st.text_input("Index key")
    col1, col2 = st.columns(2)
    authors = col1.text_input("Authors")
    year = col2.number_input("Year", min_value=1900, max_value=2100, value=2025, step=1)
    title = st.text_input("Paper title")
    journal_name = st.text_input("Journal")
    doi = st.text_input("DOI or URL")
    desc = st.text_area("Short description")

    if st.button("Save citation") and key:
        from cesm_utils import INDEX_INFO

        INDEX_INFO[key] = {
            "authors": authors,
            "year": year,
            "title": title,
            "journal": journal_name,
            "doi": doi,
            "desc": desc,
        }
        save_citations()
        st.success(f"{key} saved. Reload the page to see it in the list.")

