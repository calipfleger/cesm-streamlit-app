import xarray as xr
import numpy as np
import os

os.makedirs("data", exist_ok=True)

times = np.arange(1850, 2006)
lats = np.linspace(-90, 90, 36)
lons = np.linspace(0, 360, 72)

data = np.random.rand(len(times), len(lats), len(lons))

ds = xr.Dataset(
    {
        "d18Op": (["time", "lat", "lon"], data)
    },
    coords={
        "time": times,
        "lat": lats,
        "lon": lons
    }
)

ds["d18Op"].attrs["units"] = "per mil"
ds["d18Op"].attrs["description"] = "Oxygen isotope ratio in precipitation"

ds.to_netcdf("data/test_icesm.nc")
print("Dummy NetCDF file created at data/test_icesm.nc")

