import dash
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
from dash import Dash, Input, Output, clientside_callback, html

DBC_CSS = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
TEMPLATES = ["darkly", "journal"]
EXTERNAL_STYLESHEETS = [dbc.themes.DARKLY, dbc.themes.JOURNAL, DBC_CSS, dbc.icons.FONT_AWESOME]
LOGO_FILE = "logo.svg"

app = Dash(
    external_stylesheets=EXTERNAL_STYLESHEETS,
    # these meta_tags ensure content is scaled correctly on different devices
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    use_pages=True,
)
app._favicon = LOGO_FILE  # type: ignore[assignment]  # noqa: SLF001
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

if __name__ == "__main__":
    app.run_server(debug=True)
