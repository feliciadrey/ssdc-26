import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.NavbarSimple(
        brand="SSDC 26 Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dbc.NavLink("Executive Summary", href="/")),
            dbc.NavItem(dbc.NavLink("Recruitment Operations", href="/operational")),
            dbc.NavItem(dbc.NavLink("Talent Matching", href="/talent-matching")),
        ],
    ),
    html.Div(dash.page_container, style={"padding": "24px"}),
])

if __name__ == "__main__":
    app.run(debug=False, port=8052)