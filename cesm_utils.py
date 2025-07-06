import xarray as xr

def load_cesm_data(file):
    """Load CESM NetCDF file (uploaded or path) into xarray.Dataset."""
    if hasattr(file, "read"):  # For uploaded file-like objects
        return xr.open_dataset(file)
    else:  # For file paths
        return xr.open_dataset(str(file))

def get_variable(ds, varname):
    """Return a variable (DataArray) from the xarray.Dataset."""
    return ds[varname]
