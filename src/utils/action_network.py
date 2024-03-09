import logging
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from parsons import ActionNetwork

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(message)s")


def add_action_network_data(df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    an = ActionNetwork(api_token=api_key)
    people = []
    with ThreadPoolExecutor() as executor:
        executor.map(lambda page: people.extend(an.get_people(page=page)["_embedded"]["osdi:people"]), range(1, 6))
    print(people)
    return df
