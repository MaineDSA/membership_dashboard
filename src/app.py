import dash
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
from dash import Dash, html

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

if __name__ == "__main__":
    app.run(debug=True)
