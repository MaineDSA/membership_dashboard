import plotly.io as pio
from plotly import graph_objects as go


def with_template_if_dark(fig: go.Figure, dark_mode: bool) -> go.Figure:
    """Update the figure template based on the dark mode setting."""
    if not dark_mode:
        fig["layout"]["template"] = pio.templates["journal"]
    return fig
