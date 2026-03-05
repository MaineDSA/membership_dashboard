from dash import Input, Output, clientside_callback
from plotly import graph_objects as go
from plotly import io as pio


def with_template_if_dark(fig: go.Figure, *, is_dark_mode: bool) -> go.Figure:
    """Update the figure template based on the dark mode setting."""
    fig["layout"]["paper_bgcolor"] = "rgba(0, 0, 0, 0)"
    if not is_dark_mode:
        fig["layout"]["template"] = pio.templates["journal"]
    return fig


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
