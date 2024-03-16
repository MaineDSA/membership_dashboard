import hashlib
import json
from pathlib import Path, PurePath

import dotenv
import mapbox
import pandas as pd
import ratelimit
from tqdm import tqdm

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
geocoder = mapbox.Geocoder(access_token=config.get("MAPBOX"))
tqdm.pandas(unit="comrades", leave=False, desc="Geocoding")


def persist_to_file(file_name: Path):
    def decorator(original_func):
        try:
            cache = json.load(open(file_name))
        except (OSError, ValueError):
            cache = {}

        def new_func(param: str) -> list[float]:
            if not isinstance(param, str):
                return original_func(param)
            param_hash = hashlib.sha256(param.encode("utf-8")).hexdigest()
            if param_hash not in cache:
                cache[param_hash] = original_func(param)
                json.dump(cache, open(file_name, "w"))
            return cache[param_hash]

        return new_func

    return decorator


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=600, period=60)
def mapbox_geocoder(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, using the Mapbox API"""
    response = geocoder.forward(address, country=["us"])
    if "features" not in response.geojson():
        return [0, 0]
    return response.geojson()["features"][0]["center"]


@persist_to_file(Path(PurePath(__file__).parents[2], ".api_cache/geocoding.json"))
def get_geocoding(address: str) -> list[float]:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or mapbox_geocoder"""
    if not isinstance(address, str) or "MAPBOX" not in config:
        return [0, 0]
    return mapbox_geocoder(address)


def add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    if "lat" in df:
        return df

    df[["lon", "lat"]] = pd.DataFrame(
        (df.address1 + ", " + df.city + ", " + df.state + " " + df.zip).progress_apply(get_geocoding).tolist(),
        index=df.index,
    )
    return df
