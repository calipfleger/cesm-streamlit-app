import xarray as xr
import numpy as np
import pandas as pd
import os

def create_dummy_dataset(path="data/dummy.nc"):
    """Creates a synthetic NetCDF dataset for testing and plotting."""
    times = pd.date_range("2000-01-01", periods=100, freq="M")
    lats = np.linspace(-30, 30, 10)
    lons = np.linspace(120, 280, 20)
    temp_data = 15 + 8 * np.random.randn(len(times), len(lats), len(lons))

    ds = xr.Dataset(
        {
            "tas": (
                ("time", "lat", "lon"),
                temp_data,
                {"units": "degC", "description": "Synthetic surface air temperature"},
            )
        },
        coords={"time": times, "lat": lats, "lon": lons},
    )

    os.makedirs("data", exist_ok=True)
    ds.to_netcdf(path)
    print(f"Dummy NetCDF file created at: {path}")

if __name__ == "__main__":
    create_dummy_dataset()

