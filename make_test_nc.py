import xarray as xr
import numpy as np
years = np.arange(1810, 1820)
lat = np.linspace(-30, 30, 24)
lon = np.linspace(110, 260, 40)
data = np.random.randn(len(years), len(lat), len(lon))
d18op = np.random.randn(len(years), len(lat), len(lon)) * 0.5
nino34 = np.random.randn(len(years))

ds = xr.Dataset(
    {
        "precip": (["time", "lat", "lon"], data),
        "d18op": (["time", "lat", "lon"], d18op),
        "nino34": (["time"], nino34),
    },
    coords={
        "time": years,
        "lat": lat,
        "lon": lon,
    }
)
ds.to_netcdf("test_icesm.nc")
