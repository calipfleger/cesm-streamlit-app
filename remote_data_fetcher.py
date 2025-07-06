import streamlit as st
import os
import urllib.request
from pathlib import Path

def remote_fetch_workflow():
    st.sidebar.markdown("### 🌐 Download NetCDF from Remote Path")

    remote_url = st.sidebar.text_input("Enter remote HTTP or HTTPS NetCDF URL:")
    
    if remote_url:
        filename = remote_url.split("/")[-1]
        target_path = os.path.join("data", filename)
        
        if st.sidebar.button("Download and Save"):
            try:
                Path("data").mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(remote_url, target_path)
                st.sidebar.success(f"✅ Downloaded and saved to `{target_path}`")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to download: {e}")

