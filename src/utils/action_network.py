import hashlib
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePath

import dotenv
import pandas as pd
import ratelimit
from parsons import ActionNetwork
from tqdm import tqdm

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
an = ActionNetwork(api_token=config.get("AN"))

cache_lock = threading.Lock()


def persist_to_file(file_name: Path):
    def decorator(original_func):
        try:
            with open(file_name) as f:
                cache = json.load(f)
        except (OSError, ValueError):
            cache = {}

        def new_func(param: str) -> str:
            if not isinstance(param, str):
                return original_func(param)
            param_hash = hashlib.sha256(param.encode("utf-8")).hexdigest()
            with cache_lock:
                if param_hash not in cache:
                    cache[param_hash] = original_func(param)
                    with open(file_name, "w") as cache_file:
                        json.dump(cache, cache_file)
            return cache[param_hash]

        return new_func

    return decorator


@persist_to_file(Path(PurePath(__file__).parents[2], "action_network.json"))
def get_data(email_addr: str) -> str | None:
    def cached_query() -> str | None:
        query = f"email_address eq '{email_addr}'"
        data = an.get_people(filter=query)
        if "identifiers" not in data:
            return None
        identifiers = [i.replace("action_network:", "") for i in data["identifiers"][0] if i.startswith("action_network:")]
        return ",".join(identifiers)

    @ratelimit.sleep_and_retry
    @ratelimit.limits(calls=4, period=1)
    def rate_limiter() -> str | None:
        return cached_query()

    return rate_limiter()


def add_action_network_identifier(df: pd.DataFrame) -> pd.DataFrame:
    if "AN" not in config:
        logging.info("Action Network API key not configured, skipping tagging")
        return df

    with ThreadPoolExecutor() as executor:
        df["action_network_id"] = list(tqdm(executor.map(get_data, df["email"]), total=df.shape[0], leave=False, unit="comrades", desc="Action Network Lookup"))

    return df
