import threading

import dash
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
from dash import Dash, Input, Output, callback, clientside_callback, html

from src.utils import scan_lists
from src.utils.fetch_list import fetch_list
from src.utils.scan_lists import BRANCH_ZIPS_PATH, MEMBER_LIST_NAME, get_membership_lists

# shared state for the background fetch thread
_fetch_state: dict = {"running": False, "status": ""}
_fetch_lock = threading.Lock()

FAVICON = {
    "rel": "icon",
    "href": "/assets/favicon.svg",
    "type": "image/svg+xml",
}
DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
EXTERNAL_STYLESHEETS = [dbc.themes.DARKLY, dbc.themes.JOURNAL, dbc.icons.FONT_AWESOME, FAVICON, DBC_CSS]
TEMPLATES = ["darkly", "journal"]

app = Dash(
    external_stylesheets=EXTERNAL_STYLESHEETS,
    # these meta_tags ensure content is scaled correctly on different devices
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    suppress_callback_exceptions=True,
    use_pages=True,
)
app.layout = html.Div(dash.page_container)
dash_bootstrap_templates.load_figure_template(TEMPLATES)

clientside_callback(
    """
    (switchOn) => {
       switchOn
         ? document.documentElement.setAttribute("data-bs-theme", "dark")
         : document.documentElement.setAttribute("data-bs-theme", "light")
       return window.dash_clientside.no_update
    }
    """,
    Output(component_id="color-mode-switch", component_property="id"),
    Input(component_id="color-mode-switch", component_property="value"),
)


def _run_fetch() -> None:
    try:
        fetch_list()
        scan_lists.MEMB_LISTS = get_membership_lists(MEMBER_LIST_NAME, BRANCH_ZIPS_PATH)
        with _fetch_lock:
            _fetch_state["status"] = "Done. Reload to update dropdowns."
    except RuntimeError as e:
        with _fetch_lock:
            _fetch_state["status"] = f"Error: {e}"
    finally:
        with _fetch_lock:
            _fetch_state["running"] = False


@callback(
    Output("fetch-list-poll", "disabled"),
    Output("fetch-list-status", "children"),
    Input("fetch-list-button", "n_clicks"),
    prevent_initial_call=True,
)
def start_fetch(n_clicks: int) -> tuple[bool, str]:  # noqa: ARG001
    with _fetch_lock:
        if _fetch_state["running"]:
            return False, _fetch_state["status"]
        _fetch_state["running"] = True
        _fetch_state["status"] = "Fetching..."
    threading.Thread(target=_run_fetch, daemon=True).start()
    return False, "Fetching..."


@callback(
    Output("fetch-list-poll", "disabled", allow_duplicate=True),
    Output("fetch-list-status", "children", allow_duplicate=True),
    Input("fetch-list-poll", "n_intervals"),
    prevent_initial_call=True,
)
def poll_fetch_status(n_intervals: int) -> tuple[bool, str]:  # noqa: ARG001
    with _fetch_lock:
        running = _fetch_state["running"]
        status = _fetch_state["status"]
    return running, status


if __name__ == "__main__":
    app.run(debug=True)
