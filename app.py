import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

from utils.theme import COLORS, SIDEBAR_WIDTH, SHADOW_SM

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server

NAV_ITEMS = [
    ("Executive Summary", "/", "bi bi-bar-chart-line-fill"),
    ("Recruitment Operations", "/operational", "bi bi-activity"),
    ("Talent Matching", "/talent-matching", "bi bi-people-fill"),
]


def nav_link(label, href, icon, link_id):
    return dcc.Link(
        html.Div([
            html.Div(style={
                "width": "3px", "height": "18px", "borderRadius": "3px",
                "background": "transparent", "marginRight": "10px",
            }, className="nav-indicator"),
            html.I(className=icon, style={"marginRight": "10px", "fontSize": "14.5px"}),
            html.Span(label, style={"fontSize": "13px", "fontWeight": "500"}),
        ], style={"display": "flex", "alignItems": "center"}),
        href=href,
        id=link_id,
        className="sidebar-link",
        style={
            "display": "block", "padding": "10px 14px", "borderRadius": "10px",
            "color": COLORS["text_secondary"], "textDecoration": "none", "marginBottom": "3px",
        },
    )


sidebar = html.Div([
    html.Div([
        html.Div([
            html.Div(
                html.I(className="bi bi-mortarboard-fill", style={"fontSize": "16px", "color": "#fff"}),
                style={
                    "width": "34px", "height": "34px", "borderRadius": "10px",
                    "background": f"linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%)",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "boxShadow": SHADOW_SM,
                },
            ),
            html.Div([
                html.Div("SSDC", style={"fontSize": "16.5px", "fontWeight": "800",
                                         "color": COLORS["text"], "letterSpacing": "-0.01em", "lineHeight": "1.1"}),
                html.Div("Placement Intelligence", style={
                    "fontSize": "9.5px", "color": COLORS["muted"], "textTransform": "uppercase",
                    "letterSpacing": "0.06em", "fontWeight": "600",
                }),
            ], style={"marginLeft": "10px"}),
        ], style={"display": "flex", "alignItems": "center"}),
    ], style={"padding": "20px 18px 18px 18px", "borderBottom": f"1px solid {COLORS['border_soft']}"}),

    html.Div([
        html.Div("MENU", style={
            "fontSize": "9.5px", "fontWeight": "700", "color": COLORS["muted_light"],
            "letterSpacing": "0.08em", "padding": "0 14px", "marginBottom": "8px", "marginTop": "4px",
        }),
        html.Div([nav_link(label, href, icon, f"nav-link-{i}") for i, (label, href, icon) in enumerate(NAV_ITEMS)]),
    ], style={"padding": "16px 10px"}),

    html.Div([
        html.Div([
            html.Div(style={
                "width": "7px", "height": "7px", "borderRadius": "50%",
                "background": COLORS["success"], "marginRight": "6px",
                "boxShadow": f"0 0 0 3px {COLORS['success_bg']}",
            }),
            html.Span("Data tersinkron", style={"fontSize": "11px", "fontWeight": "600", "color": COLORS["text_secondary"]}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "3px"}),
        html.Div("17 Jul 2026, 09:12", style={"fontSize": "10.5px", "color": COLORS["muted"]}),
    ], style={
        "position": "absolute", "bottom": "18px", "left": "16px", "right": "16px",
        "padding": "12px 14px", "background": COLORS["surface_alt"], "borderRadius": "12px",
        "border": f"1px solid {COLORS['border_soft']}",
    }),
], style={
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": SIDEBAR_WIDTH,
    "background": COLORS["surface"], "borderRight": f"1px solid {COLORS['border_soft']}",
    "zIndex": 100,
})

content = html.Div(
    dash.page_container,
    style={"marginLeft": SIDEBAR_WIDTH, "minHeight": "100vh", "background": COLORS["bg"]},
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    sidebar,
    content,
], style={"fontFamily": "Inter, -apple-system, sans-serif"})

@callback(
    [Output(f"nav-link-{i}", "className") for i in range(len(NAV_ITEMS))],
    Input("url", "pathname"),
)
def highlight_active_nav(pathname):
    return [
        "sidebar-link active" if href == pathname else "sidebar-link"
        for _, href, _ in NAV_ITEMS
    ]


if __name__ == "__main__":
    app.run(debug=False, port=8052)