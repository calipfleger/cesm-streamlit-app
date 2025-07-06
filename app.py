import streamlit as st
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

# Clear title
st.title('CESM Data Visualization Workbook')

# Step 1: Generate Dummy NetCDF if not present
data_dir = 'data/'
os.makedirs(data_dir, exist_ok=True)
dummy_file = os.path.join(data_dir, 'dummy_dataset.nc')

if not os.path.exists(dummy_file):
    time = np.arange(0, 100)
    data = np.sin(time / 10) + np.random.normal(0, 0.2, size=time.size)
    dummy_ds = xr.Dataset(
        {'dummy_var': ('time', data)},
        coords={'time': time},
        attrs={'description': 'Dummy CESM data for testing', 'units': 'arbitrary'}
    )
    dummy_ds.to_netcdf(dummy_file)

# Step 2: Dataset Selection
st.sidebar.header("Select Dataset")
files = [f for f in os.listdir(data_dir) if f.endswith('.nc')]

selected_file = st.sidebar.selectbox("Choose NetCDF file:", files)
data_path = os.path.join(data_dir, selected_file)

# Step 3: Load Dataset and Metadata
ds = xr.open_dataset(data_path)
variables = list(ds.data_vars)

# Step 4: Variable Selection
selected_var = st.sidebar.selectbox("Choose variable:", variables)

# Automatic metadata extraction
metadata = {
    'variables': list(ds.data_vars),
    'dimensions': dict(ds.dims),
    'attributes': ds.attrs,
}

# Step 5: Visualization
fig, ax = plt.subplots(figsize=(10, 5))
ds[selected_var].plot(ax=ax)
ax.set_title(f"{selected_var} from {selected_file}")
st.pyplot(fig)

# Step 6: Automatic Caption Generation (Modular)
def generate_caption(metadata, dataset_name, variable_name):
    caption = (
        f"Figure: {variable_name} from CESM dataset '{dataset_name}'. "
        f"Dataset includes variables {metadata['variables']} with dimensions {metadata['dimensions']}. "
        f"Global attributes: {metadata['attributes']}."
    )
    return caption

caption = generate_caption(metadata, selected_file, selected_var)
st.markdown(f"**Caption:** {caption}")

# Step 7: Save Figure & Caption
save_dir = 'saved_figures'
os.makedirs(save_dir, exist_ok=True)

if st.button("Save Visualization"):
    fig_filename = f"{save_dir}/{selected_var}_{selected_file.replace('.nc', '')}.png"
    fig.savefig(fig_filename, bbox_inches='tight')

    caption_filename = fig_filename.replace('.png', '_caption.txt')
    with open(caption_filename, 'w') as f:
        f.write(caption)

    st.success(f"Figure and caption saved as {fig_filename} and {caption_filename}")

