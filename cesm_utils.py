import xarray as xr
import pandas as pd
import numpy as np


import xarray as xr

def load_cesm_data(file):
    """Load CESM NetCDF file (uploaded or local path) into xarray.Dataset."""
    if hasattr(file, "read"):  # uploaded file-like object
        return xr.open_dataset(file)
    else:  # local file path
        return xr.open_dataset(str(file))

def get_variable(ds, varname):
    """Return a specific variable from the dataset."""
    return ds[varname]


def load_dataset(path):
    """Load NetCDF dataset from path."""
    return xr.open_dataset(path)

def list_variables(ds):
    """Return list of variables from dataset."""
    return list(ds.data_vars)

def slice_time(ds, variable, time_range):
    """Return selected variable sliced by time."""
    return ds[variable].sel(time=slice(time_range[0], time_range[1]))

def read_index_csv(file_path_or_obj):
    """Read index CSV from path or uploaded file."""
    return pd.read_csv(file_path_or_obj, parse_dates=True, index_col=0)

def get_metadata(ds, variable):
    """Extract units and description metadata."""
    return {
        'dims': dict(ds.dims),
        'units': ds[variable].attrs.get('units', 'N/A'),
        'desc': ds[variable].attrs.get('description', 'No description')
    }

