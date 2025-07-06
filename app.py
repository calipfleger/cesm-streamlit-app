import streamlit as st
import cesm_utils
import matplotlib.pyplot as plt
import os

st.title("CESM Data Explorer")

sample_file = os.path.join("data", "sample.nc")
uploaded_file = st.file_uploader("Upload CESM NetCDF file", type=["nc"])

if uploaded_file is not None:
    ds = cesm_utils.load_cesm_data(uploaded_file)
    st.success("Loaded uploaded file!")
elif os.path.exists(sample_file):
    ds = cesm_utils.load_cesm_data(sample_file)
    st.info("No file uploaded. Loaded sample data.")
else:
    st.warning("Please upload a NetCDF file to get started.")
    ds = None

if ds is not None:
    st.write("Variables in this file:")
    st.write(list(ds.variables.keys()))

    varname = st.selectbox("Select variable to plot", list(ds.variables.keys()))
    if varname:
        data = cesm_utils.get_variable(ds, varname)
        st.write(data)

        dim_options = list(data.dims)
        if len(dim_options) >= 2:
            x_dim = st.selectbox("X axis", dim_options, index=0)
            y_dim = st.selectbox("Y axis", dim_options, index=1)
            plot_data = data.isel({dim: 0 for dim in data.dims if dim not in [x_dim, y_dim]})

            fig, ax = plt.subplots()
            plot_data.plot(ax=ax)
            st.pyplot(fig)
