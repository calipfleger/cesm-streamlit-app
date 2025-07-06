import os
import subprocess
import xarray as xr
import streamlit as st

def fetch_remote_netcdf(user, host, remote_path, local_dir="data"):
    """
    Download a NetCDF file from a remote HPC or server via SCP.
    """
    os.makedirs(local_dir, exist_ok=True)
    filename = os.path.basename(remote_path)
    local_path = os.path.join(local_dir, filename)

    st.info(f"Fetching {filename} from {host}...")
    try:
        subprocess.run(["scp", f"{user}@{host}:{remote_path}", local_path], check=True)
        st.success(f"Downloaded to {local_path}")
        return local_path
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to fetch file: {e}")
        return None

def clean_netcdf(file_path):
    """
    Load and clean a NetCDF file using xarray.
    """
    try:
        ds = xr.open_dataset(file_path)
        ds = ds.drop_vars([v for v in ds.data_vars if ds[v].isnull().all()], errors='ignore')
        ds = ds.squeeze(drop=True)
        return ds
    except Exception as e:
        st.error(f"Error cleaning file: {e}")
        return None

def remote_fetch_workflow():
    st.sidebar.markdown("### 🔗 Fetch Remote NetCDF File")
    with st.sidebar.form("remote_fetch"):
        user = st.text_input("SSH Username", "your_username")
        host = st.text_input("SSH Host", "remote.cluster.edu")
        path = st.text_input("Remote NetCDF Path", "/path/to/file.nc")
        submit = st.form_submit_button("Fetch")

    if submit:
        fetched_path = fetch_remote_netcdf(user, host, path)
        if fetched_path:
            cleaned_ds = clean_netcdf(fetched_path)
            if cleaned_ds:
                st.session_state["remote_dataset"] = cleaned_ds
                st.session_state["remote_path"] = fetched_path
                st.success("Remote dataset loaded and cleaned!")

