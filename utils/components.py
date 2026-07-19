from dash import html
from utils.theme import COLORS, CARD_STYLE, SHADOW_MD, RADIUS_SM, DARK_CARD, DARK_CARD_TEXT, DARK_CARD_TEXT_MUTED


def _icon_badge(icon, bg, fg):
    return html.Div(
        html.I(className=icon, style={"fontSize": "14px", "color": fg}),
        style={
            "width": "30px", "height": "30px", "borderRadius": "9px",
            "background": bg, "display": "flex", "alignItems": "center",
            "justifyContent": "center", "flexShrink": "0",
        },
    )


def kpi_card(label, value, sub=None, color=COLORS["text"], accent=None, icon="bi bi-graph-up", trend=None):
    """KPI card with icon badge, big number, and an optional trend pill."""
    style = dict(CARD_STYLE)
    style.update({"flex": "1", "minWidth": "0", "className": "kpi-card"})

    trend_pill = None
    if trend:
        up = trend.startswith("+")
        pill_color = COLORS["success"] if up else COLORS["danger"]
        pill_bg = COLORS["success_bg"] if up else COLORS["danger_bg"]
        trend_pill = html.Span([
            html.I(className=f"bi bi-arrow-{'up' if up else 'down'}-short", style={"fontSize": "11px"}),
            trend,
        ], style={
            "fontSize": "10px", "fontWeight": "600", "color": pill_color,
            "background": pill_bg, "padding": "2px 7px", "borderRadius": "20px",
            "display": "inline-flex", "alignItems": "center", "gap": "1px",
        })

    header_row = html.Div([
        _icon_badge(icon, accent + "1A" if accent else COLORS["primary_light"], accent or COLORS["primary"]),
        trend_pill,
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"})

    return html.Div([
        header_row,
        html.Div(label, style={"fontSize": "11px", "color": COLORS["muted"],
                                "textTransform": "uppercase", "letterSpacing": "0.04em",
                                "fontWeight": "600"}),
        html.Div(value, style={"fontSize": "28px", "fontWeight": "700", "color": color,
                                "margin": "3px 0 2px 0", "letterSpacing": "-0.02em"}),
        html.Div(sub or "", style={"fontSize": "11px", "color": COLORS["muted_light"]}),
    ], className="kpi-card", style=style)


def section_card(title, subtitle, children, style_extra=None, icon="bi bi-bar-chart", accent=None):
    """Titled card with a small icon badge next to the title for visual anchoring.
    `subtitle` can be a plain string OR a Dash component (e.g. a small control
    row with a dropdown/checklist embedded) — both render fine here."""
    style = dict(CARD_STYLE)
    if style_extra:
        style.update(style_extra)

    if isinstance(subtitle, str):
        subtitle_el = html.Div(subtitle, style={"fontSize": "11px", "color": COLORS["muted"]})
    else:
        subtitle_el = subtitle

    title_row = html.Div([
        _icon_badge(icon, (accent + "1A") if accent else COLORS["primary_light"], accent or COLORS["primary"]),
        html.Div([
            html.Div(title, style={"fontSize": "13.5px", "fontWeight": "650", "color": COLORS["text"]}),
            subtitle_el,
        ]),
    ], style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "12px"})

    return html.Div([title_row, children], className="section-card", style=style)


def filter_control(label, control, min_width="160px"):
    """A labeled filter widget for the filter bar — small caps label above a
    borderless dropdown/input, wrapped in a card-like pill so a whole row of
    these reads as one cohesive filter bar rather than loose dropdowns."""
    return html.Div([
        html.Div(label, style={"fontSize": "9.5px", "fontWeight": "700", "color": COLORS["muted"],
                                "textTransform": "uppercase", "letterSpacing": "0.05em",
                                "marginBottom": "4px"}),
        control,
    ], style={
        "background": COLORS["surface"], "border": f"1px solid {COLORS['border_soft']}",
        "borderRadius": "10px", "padding": "8px 12px", "minWidth": min_width,
        "boxShadow": SHADOW_MD,
    })


def page_header(title, subtitle, badge=None):
    """`badge` accepts either a plain string (rendered as a small pill next
    to the title) or a full Dash component like a Button (rendered as a
    right-aligned action element in the header row) — so this one function
    covers both a status badge and a page-level action button."""
    badge_el = None
    if badge is not None:
        if isinstance(badge, str):
            badge_el = html.Span(badge, style={
                "fontSize": "10.5px", "fontWeight": "600", "color": COLORS["primary"],
                "background": COLORS["primary_light"], "padding": "4px 10px",
                "borderRadius": "20px", "marginLeft": "10px",
            })
        else:
            badge_el = badge  # render the component (e.g. a button) as-is

    title_block = html.Div([
        html.Div([
            html.H2(title, style={"fontSize": "21px", "fontWeight": "700",
                                   "color": COLORS["text"], "margin": "0",
                                   "letterSpacing": "-0.01em", "display": "inline"}),
            badge_el if isinstance(badge, str) else None,
        ]),
        html.Div(subtitle, style={"fontSize": "12.5px", "color": COLORS["muted"], "marginTop": "3px"}),
    ])

    if badge is None or isinstance(badge, str):
        return html.Div([title_block], style={"marginBottom": "20px"})

    # Non-string badge = a full action component -> right-aligned toolbar layout
    return html.Div([
        title_block,
        html.Div(badge_el, style={"flexShrink": "0"}),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start",
              "marginBottom": "20px"})


def dark_kpi_card(label, value, sub=None, icon="bi bi-flag-fill"):
    """The Donezo-style dark 'spotlight' card. Use for exactly ONE KPI per
    page — the one you most want the eye to land on first (e.g. the riskiest
    or most important number). Using it on more than one card per row kills
    the effect; it works because it's rare."""
    from utils.theme import DARK_CARD, DARK_CARD_TEXT, DARK_CARD_TEXT_MUTED, COLORS as C
    style = dict(DARK_CARD)
    style.update({"flex": "1", "minWidth": "0"})
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize": "12px", "fontWeight": "500", "color": DARK_CARD_TEXT_MUTED}),
            html.Div(
                html.I(className=icon, style={"fontSize": "14px", "color": DARK_CARD_TEXT}),
                style={"width": "26px", "height": "26px", "borderRadius": "8px",
                       "background": "rgba(255,255,255,0.12)", "display": "flex",
                       "alignItems": "center", "justifyContent": "center"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                  "marginBottom": "14px"}),
        html.Div(value, style={"fontSize": "26px", "fontWeight": "500", "color": DARK_CARD_TEXT}),
        html.Div(sub or "", style={"fontSize": "11px", "color": C["primary_soft"], "marginTop": "2px"}),
    ], style=style)


def donut_kpi_card(label, sub, percent, target=None):
    """Circular progress ring for a single rate/percentage metric — reads
    faster than a bar for 'how close to done/target is this one number',
    which is exactly the placement-rate / fulfillment-rate use case.
    Built with a CSS conic-gradient ring (no SVG/data-URI needed)."""
    style = dict(CARD_STYLE)
    style.update({"flex": "1", "minWidth": "0", "display": "flex",
                  "alignItems": "center", "gap": "14px"})

    ring_outer = html.Div(
        html.Div(f"{percent}%", style={
            "width": "48px", "height": "48px", "borderRadius": "50%",
            "background": COLORS["surface"], "display": "flex",
            "alignItems": "center", "justifyContent": "center",
            "fontSize": "13px", "fontWeight": "600", "color": COLORS["primary_dark"],
        }),
        style={
            "width": "64px", "height": "64px", "borderRadius": "50%",
            "background": f"conic-gradient({COLORS['primary']} 0% {percent}%, {COLORS['primary_light']} {percent}% 100%)",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "flexShrink": "0",
        },
    )

    return html.Div([
        ring_outer,
        html.Div([
            html.Div(label, style={"fontSize": "12px", "color": COLORS["text_secondary"], "fontWeight": "500"}),
            html.Div(sub or (f"Target {target}%" if target else ""),
                     style={"fontSize": "11px", "color": COLORS["muted"], "marginTop": "2px"}),
        ]),
    ], style=style)