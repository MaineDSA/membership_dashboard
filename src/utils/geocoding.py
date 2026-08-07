import hashlib
import importlib.metadata
import json
import logging
from collections.abc import Callable
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

import dotenv
import geopy
import geopy.geocoders
import pandas as pd
import ratelimit
from tqdm import tqdm

if TYPE_CHECKING:
    from geopy.location import Location

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
if config.get("GEOCODER"):
    metadata = importlib.metadata.metadata("membership_dashboard")
    project_urls = dict(item.split(", ", 1) for item in metadata.get_all("Project-URL", []))
    source_url = project_urls.get("source", "No Project URL Defined")
    geopy.geocoders.options.default_user_agent = f"{metadata.get('name')}/{metadata.get('version')}; +{source_url}"  # type: ignore[ty:invalid-assignment]
    geolocator = geopy.get_geocoder_for_service(config.get("GEOCODER"))(api_key=config.get("GEOCODER_API_KEY"))

tqdm.pandas(unit="comrades", leave=False, desc="Geocoding")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def persist_to_file(file_name: Path) -> Callable:
    def decorator(original_func: Callable) -> Callable:
        try:
            with file_name.open() as f:
                cache = json.load(f)

        except (OSError, ValueError):
            cache = {}

        def new_func(param: str) -> list[float]:
            if not isinstance(param, str):
                return original_func(param)
            param_hash = hashlib.sha256(param.encode("utf-8")).hexdigest()
            if param_hash not in cache:
                cache[param_hash] = original_func(param)
                with file_name.open(mode="w") as json_file:
                    json.dump(cache, json_file)
            return cache[param_hash]

        return new_func

    return decorator


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=600, period=60)
def geocode_address(address: str) -> tuple[float, float]:
    """Return a list of lat and long coordinates from a supplied address string, using a geocoder API."""
    location: Location | None = geolocator.geocode(address)
    if not location:
        logger.warning("Could not geocode address: %s", address)
        return (0, 0)
    return (location.latitude, location.longitude)


@persist_to_file(Path(PurePath(__file__).parents[2]) / "geocoding.json")
def get_geocoding(address: str) -> tuple[float, float]:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or geocoder."""
    if not geolocator or not isinstance(address, str):
        return (0, 0)
    return geocode_address(address)


def add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    if not geolocator or ("lat" in df and "lon" in df):
        return df

    df[["lon", "lat"]] = pd.DataFrame(
        (df.address1 + ", " + df.city + ", " + df.state + " " + df.zip).progress_apply(get_geocoding).tolist(),
        index=df.index,
    )
    return df
