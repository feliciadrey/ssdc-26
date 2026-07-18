from dash import html

from utils.theme import CARD_STYLE, COLORS


def page_header(title, subtitle, right_content=None):
    left = html.Div([
        html.Div(title, style={
            "fontSize": "28px",
            "fontWeight": "700",
            "color": COLORS["text"],
            "marginBottom": "6px",
        }),
        html.Div(subtitle, style={
            "fontSize": "14px",
            "color": COLORS["muted"],
        }),
    ])

    if right_content is None:
        return html.Div([left], style={"marginBottom": "24px"})

    return html.Div([
        left,
        html.Div(right_content, style={"display": "flex", "alignItems": "center"}),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "flex-start",
        "marginBottom": "24px",
    })


def section_card(title, subtitle, content, style_extra=None):
    style = {
        **CARD_STYLE,
        "display": "flex",
        "flexDirection": "column",
        "gap": "12px",
    }
    if style_extra:
        style.update(style_extra)

    return html.Div([
        html.Div([
            html.Div(title, style={
                "fontSize": "15px",
                "fontWeight": "700",
                "color": COLORS["text"],
            }),
            html.Div(subtitle, style={
                "fontSize": "12px",
                "color": COLORS["muted"],
            }),
        ]),
        html.Div(content, style={"width": "100%"}),
    ], style=style)


def filter_control(label, children, min_width="200px"):
    return html.Div([
        html.Div(label, style={
            "fontSize": "11px",
            "fontWeight": "600",
            "color": COLORS["muted"],
            "marginBottom": "6px",
            "textTransform": "uppercase",
            "letterSpacing": "0.03em",
        }),
        children,
    ], style={
        "background": COLORS["surface"],
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "8px",
        "padding": "8px 12px",
        "minWidth": min_width,
    })


def kpi_card(title, value, note, color=None, accent=None):
    color = color or COLORS["text"]
    accent = accent or COLORS["accent"]
    return html.Div([
        html.Div(title, style={
            "fontSize": "12px",
            "fontWeight": "600",
            "color": COLORS["muted"],
            "marginBottom": "8px",
        }),
        html.Div(value, style={
            "fontSize": "28px",
            "fontWeight": "700",
            "color": color,
        }),
        html.Div(note, style={
            "fontSize": "11px",
            "color": COLORS["muted"],
        }),
    ], style={
        **CARD_STYLE,
        "flex": "1",
        "minWidth": "160px",
        "border": f"1px solid {COLORS['border']}",
    })