from pathlib import Path, PurePath

import dash
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
import dotenv
from dash import Dash, html

from src.utils.scan_lists import BRANCH_ZIPS_PATH, MEMBER_LIST_NAME, update_membership_lists

FAVICON = {
    "rel": "icon",
    "href": "/assets/favicon.svg",
    "type": "image/svg+xml",
}
DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
EXTERNAL_STYLESHEETS = [dbc.themes.DARKLY, dbc.themes.JOURNAL, dbc.icons.FONT_AWESOME, FAVICON, DBC_CSS]
TEMPLATES = ["darkly", "journal"]

update_membership_lists(MEMBER_LIST_NAME, BRANCH_ZIPS_PATH)

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
dash_bootstrap_templates.load_figure_template(TEMPLATES)  # pyright: ignore[reportArgumentType]

if __name__ == "__main__":
    config = dotenv.dotenv_values(Path(PurePath(__file__).parents[1], ".env"))
    is_debug = config.get("DEBUG") == "TRUE" if config.get("DEBUG") else False
    app.run(debug=is_debug)
