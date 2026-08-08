import functools
import hashlib
import importlib.metadata
import json
import logging
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

import dotenv
import geopy
import geopy.geocoders
import pandas as pd
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders.base import Geocoder
from tqdm import tqdm

if TYPE_CHECKING:
    from geopy.location import Location

CONFIG = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
METADATA = importlib.metadata.metadata("membership_dashboard")
PROJECT_URLS = dict(item.split(", ", 1) for item in METADATA.get_all("Project-URL", []))
REPO_URL = PROJECT_URLS.get("source", "No Repo URL Defined")

geolocator = None
if CONFIG.get("GEOCODER"):
    geopy.geocoders.options.default_user_agent = f"{METADATA.get('name')}/{METADATA.get('version')}; +{REPO_URL}"  # type: ignore[ty:invalid-assignment]
    geolocator: Geocoder | None = geopy.get_geocoder_for_service(CONFIG.get("GEOCODER"))(api_key=CONFIG.get("GEOCODER_API_KEY"))

tqdm.pandas(unit="comrades", leave=False, position=1, dynamic_ncols=True, desc="Geocoding")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_DIR = Path(PurePath(__file__).parents[2])


def persist_to_file(file_name: str) -> Callable:
    def decorator(original_func: Callable) -> Callable:
        conn: sqlite3.Connection | None = None

        @functools.wraps(original_func)
        def new_func(param: str) -> tuple[float, float]:
            if not isinstance(param, str):
                err_msg = f"Expected str, got {type(param).__name__}"
                raise TypeError(err_msg)

            nonlocal conn
            if conn is None:
                conn = sqlite3.connect(DB_DIR / file_name)
                conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
                conn.commit()

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


def geocode_address(address: str) -> tuple[float, float]:
    """Return a list of lat and long coordinates from a supplied address string, using a geocoder API."""
    min_delay = float(CONFIG.get("GEOCODER_DELAY") or 1.0)
    active_delay = min_delay
    max_retries = int(CONFIG.get("GEOCODER_RETRIES") or 4)

    for attempt in range(max_retries):
        try:
            location: Location | None = geolocator.geocode(address) if geolocator else None  # type: ignore[ty:unresolved-attribute]  # pyright: ignore[reportAttributeAccessIssue]
            time.sleep(min_delay)
            if not location:
                logger.warning("Could not geocode address: %s", address)
                return (0, 0)
            return (location.latitude, location.longitude)

        except (GeocoderServiceError, GeocoderTimedOut) as e:
            if attempt == max_retries - 1:
                raise

            logger.warning("Service limit hit (%s). Backing off for %s seconds...", e, active_delay)
            time.sleep(active_delay)
            active_delay *= 2.0

    return (0, 0)


@persist_to_file("geocoding.sqlite")
def get_geocoding(address: str) -> tuple[float, float]:
    """Return a list of lat and long coordinates from a supplied address string, either from cache or geocoder."""
    if not geolocator or not isinstance(address, str) or not address.strip():
        return (0, 0)
    return geocode_address(address)


def add_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    if not geolocator or ("lat" in df and "lon" in df):
        return df

    addresses = df.address1.fillna("") + ", " + df.city.fillna("") + ", " + df.state.fillna("") + " " + df.zip.fillna("")

    df[["lat", "lon"]] = pd.DataFrame(
        addresses.apply(get_geocoding).tolist(),
        index=df.index,
    )
    return df
