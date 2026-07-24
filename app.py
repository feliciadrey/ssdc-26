import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

from utils.theme import COLORS, SIDEBAR_WIDTH, SIDEBAR_GRADIENT, SHADOW_SM, SHADOW_LG

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server

NAV_ITEMS = [
    ("Performance Overview", "/", "bi bi-bar-chart-line-fill"),
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
            "color": "rgba(255,255,255,0.75)", "textDecoration": "none", "marginBottom": "3px",
        },
    )


sidebar = html.Div([
    html.Div([
        html.Div([
            html.Div(
                html.I(className="bi bi-briefcase-fill", style={"fontSize": "16px", "color": COLORS["primary_dark"]}),
                style={
                    "width": "34px", "height": "34px", "borderRadius": "10px",
                    "background": "#FFFFFF",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "boxShadow": SHADOW_SM,
                },
            ),
            html.Div([
                html.Div("Clushthree", style={"fontSize": "16.5px", "fontWeight": "800",
                                         "color": "#FFFFFF", "letterSpacing": "-0.01em", "lineHeight": "1.1"}),
                html.Div("Student Placement System", style={
                    "fontSize": "9.5px", "color": "rgba(255,255,255,0.65)", "textTransform": "uppercase",
                    "letterSpacing": "0.06em", "fontWeight": "600",
                }),
            ], style={"marginLeft": "10px"}),
        ], style={"display": "flex", "alignItems": "center"}),
    ], style={"padding": "20px 18px 18px 18px", "borderBottom": "1px solid rgba(255,255,255,0.14)"}),

    html.Div([
        html.Div("MENU", style={
            "fontSize": "9.5px", "fontWeight": "700", "color": "rgba(255,255,255,0.45)",
            "letterSpacing": "0.08em", "padding": "0 14px", "marginBottom": "8px", "marginTop": "4px",
        }),
        html.Div([nav_link(label, href, icon, f"nav-link-{i}") for i, (label, href, icon) in enumerate(NAV_ITEMS)]),
    ], style={"padding": "16px 10px"}),

    html.Div([
        html.Div([
            html.Div(style={
                "width": "7px", "height": "7px", "borderRadius": "50%",
                "background": "#5FE3A3", "marginRight": "6px",
                "boxShadow": "0 0 0 3px rgba(95,227,163,0.25)",
            }),
            html.Span("Data synced", style={"fontSize": "11px", "fontWeight": "600", "color": "#FFFFFF"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "3px"}),
        html.Div("17 Jul 2026, 09:12", style={"fontSize": "10.5px", "color": "rgba(255,255,255,0.6)"}),
    ], style={
        "position": "absolute", "bottom": "18px", "left": "16px", "right": "16px",
        "padding": "12px 14px", "background": "rgba(255,255,255,0.10)", "borderRadius": "12px",
        "border": "1px solid rgba(255,255,255,0.16)",
    }),
], style={
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": SIDEBAR_WIDTH,
    "background": SIDEBAR_GRADIENT, "boxShadow": SHADOW_LG,
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