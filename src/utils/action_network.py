import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePath

import pandas as pd
import ratelimit
from parsons import ActionNetwork
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")


def persist_to_file(file_name: Path):
    def decorator(original_func):
        try:
            cache = json.load(open(file_name))
        except (OSError, ValueError):
            cache = {}

        def new_func(param: str) -> str:
            if not isinstance(param, str):
                return original_func(param)
            param_hash = hashlib.sha256(param.encode("utf-8")).hexdigest()
            if param_hash not in cache:
                cache[param_hash] = original_func(param)
                json.dump(cache, open(file_name, "w"))
            return cache[param_hash]

        return new_func

    return decorator


def add_action_network_identifier(df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    an = ActionNetwork(api_token=api_key)

    @persist_to_file(Path(PurePath(__file__).parents[2], "action_network.json"))
    def get_data(email_addr: str) -> str:
        def cached_query():
            query = f"email_address eq '{email_addr}'"
            data = an.get_people(filter=query)
            identifiers = [i.replace("action_network:", "") for i in data["identifiers"][0] if i.startswith("action_network:")]
            return ",".join(identifiers)

        @ratelimit.sleep_and_retry
        @ratelimit.limits(calls=4, period=1)
        def rate_limiter():
            return cached_query()

        return rate_limiter()

    with ThreadPoolExecutor(max_workers=1) as executor:
        df["action_network_id"] = list(tqdm(executor.map(get_data, df["email"]), total=df.shape[0], unit="comrades", leave=False, desc="Action Network Lookup"))

    return df
