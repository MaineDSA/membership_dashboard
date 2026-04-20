import html
import logging
import re
from datetime import datetime
from pathlib import Path, PurePath

import dotenv
from curl_cffi import requests  # for dealing with cloudflare

logger = logging.getLogger(__name__)

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
DOWNLOAD_DIR = config.get("LIST") or "membership_list"
PERISCOPE_URL = config.get("PERISCOPE_URL")
PERISCOPE_PASS = config.get("PERISCOPE_PASS")

_BASE = "https://app.periscopedata.com"
_WIDGET_TITLE = "All Members"


def _get_widget_hash(session: requests.Session, dashboard_token: str) -> str:
    resp = session.get(f"{_BASE}/shared/{dashboard_token}")
    resp.raise_for_status()
    # widget metadata is embedded as JSON in the page HTML
    text = html.unescape(resp.text)
    # find the widget object by title and extract its formula_source_hash_key
    # find the widget by title, then grab the formula_source_hash_key that follows it
    match = re.search(
        r'"title":"' + re.escape(_WIDGET_TITLE) + r'".{0,500}?"formula_source_hash_key":"([^"]+)"',
        text,
        re.DOTALL,
    )
    if not match:
        msg = f"Could not find widget '{_WIDGET_TITLE}' or its hash key in dashboard HTML."
        raise LookupError(msg)
    hash_key = match.group(1)
    logger.info("Found widget hash: %s", hash_key)
    return hash_key


def fetch_list(
    download_dir: str | None = DOWNLOAD_DIR,
    periscope_url: str | None = PERISCOPE_URL,
    periscope_pass: str | None = PERISCOPE_PASS,
) -> None:
    if download_dir is None or periscope_url is None or periscope_pass is None:
        msg = "Missing required environment variables."
        raise RuntimeError(msg)

    Path(download_dir).resolve().mkdir(parents=True, exist_ok=True)

    session: requests.Session = requests.Session(impersonate="chrome")

    # extract the dashboard token from the URL (last path component before any query string)
    dashboard_token = periscope_url.rstrip("/").split("/")[-1]
    verify_url = f"{_BASE}/shared/{dashboard_token}/verify-password"

    # GET the password page first so Cloudflare can set challenge cookies
    session.get(verify_url)

    # POST password, requires a few other args we can leave blank
    resp = session.post(verify_url, data={"password": periscope_pass, "embed": "", "border": "", "data_ts": "", "widget": ""})
    resp.raise_for_status()
    logger.info("Authorized periscope.")

    # get the widget hash from the dashboard token, which points us to the AllMembers table
    widget_hash = _get_widget_hash(session, dashboard_token)

    now = datetime.now().astimezone()
    title = f"AllMembers_{now.strftime('%Y-%m-%d')}_{now.strftime('%H%M')}"  # e.g. AllMembers_2-20-2026_1102
    # generate download url for the csv
    download_url = f"{_BASE}/shared_dashboards/{dashboard_token}/download_csv/{widget_hash}?title={title}"

    resp = session.get(download_url)
    resp.raise_for_status()
    logger.info("Downloaded CSV from periscope.")

    dest = Path(download_dir).resolve() / f"{title}.csv"
    dest.write_bytes(resp.content)
    logger.info("Saved: %s", dest)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_list()
