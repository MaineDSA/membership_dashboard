import functools
import hashlib
import importlib.metadata
import json
import logging
import sqlite3
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

tqdm.pandas(unit="comrades", leave=False, position=1, desc="Geocoding")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def persist_to_file(file_name: Path) -> Callable:
    conn = sqlite3.connect(file_name)
    conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()

    def decorator(original_func: Callable) -> Callable:
        @functools.wraps(original_func)
        def new_func(param: str) -> tuple[float, float]:
            if not isinstance(param, str):
                err_msg = f"Expected str, got {type(param).__name__}"
                raise TypeError(err_msg)

            param_hash = hashlib.sha256(param.encode("utf-8")).hexdigest()

            cursor = conn.execute("SELECT value FROM cache WHERE key = ?", (param_hash,))
            row = cursor.fetchone()

            if row:
                return tuple(json.loads(row[0]))

            result = original_func(param)

            conn.execute("INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)", (param_hash, json.dumps(result)))
            conn.commit()

            return result

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


@persist_to_file(Path(PurePath(__file__).parents[2]) / "geocoding.sqlite")
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
