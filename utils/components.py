from dash import html
from utils.theme import (
    COLORS, CARD_STYLE, CHART_CARD_STYLE, KPI_CARD_STYLE, SHADOW_SM, SHADOW_MD,
    RADIUS_SM, SPACE, TITLE_GRADIENT, DARK_CARD, DARK_CARD_TEXT, DARK_CARD_TEXT_MUTED,
)


def _icon_badge(icon, bg, fg, size=24):
    return html.Div(
        html.I(className=icon, style={"fontSize": f"{round(size * 0.46)}px", "color": fg}),
        style={
            "width": f"{size}px", "height": f"{size}px", "borderRadius": "8px",
            "background": bg, "display": "flex", "alignItems": "center",
            "justifyContent": "center", "flexShrink": "0",
        },
    )


def kpi_card(label, value, sub=None, color=COLORS["text"], accent=None, icon="bi bi-graph-up",
             trend_value=None, trend_suffix="%", trend_label="vs prev period"):
    """Compact KPI card, deliberately quieter than chart cards: small icon
    badge + label on one line, big number right below, one short caption.
    Designed to be scanned in under a second — no stacked header row, no
    tall padding. Plain surface + shadow, no gradient/watermark.

    trend_value: a plain number (e.g. 4.2 or -15), NOT pre-formatted.
    Rendered on its own line below `sub` so it never gets clipped by the
    caption's ellipsis, with an up/down arrow and green/red color:
      > 0  -> green, arrow up
      < 0  -> red, arrow down
      == 0 -> muted, dash (flat)
    """
    tint = accent or COLORS["primary"]
    style = dict(KPI_CARD_STYLE)
    style.update({
        "flex": "1", "minWidth": "170px",
        "boxShadow": f"0 -8px 0 0 {tint}",
    })

    trend_row = None
    if trend_value is not None:
        if trend_value > 0:
            t_color, t_icon, t_str = COLORS["success"], "bi bi-arrow-up-short", f"{trend_value}{trend_suffix}"
        elif trend_value < 0:
            t_color, t_icon, t_str = COLORS["danger"], "bi bi-arrow-down-short", f"{abs(trend_value)}{trend_suffix}"
        else:
            t_color, t_icon, t_str = COLORS["muted"], "bi bi-dash", f"0{trend_suffix}"
        trend_row = html.Div([
            html.Span([
                html.I(className=t_icon, style={"fontSize": "11px", "verticalAlign": "-1px"}),
                html.Span(t_str, style={"fontWeight": "700", "marginLeft": "1px"}),
            ], style={
                "color": t_color, "fontSize": "10.5px", "display": "inline-flex", "alignItems": "center",
                "background": t_color + "14", "padding": "1px 6px 1px 4px", "borderRadius": "20px",
            }),
            html.Span(trend_label, style={"fontSize": "9.5px", "color": COLORS["muted_light"], "marginLeft": "5px"}),
        ], style={"display": "flex", "alignItems": "center", "marginTop": "4px"})

    label_row = html.Div([
        _icon_badge(icon, tint + "1A", tint, size=20),
        html.Span(label, style={"fontSize": "10.5px", "color": COLORS["muted"],
                                 "textTransform": "uppercase", "letterSpacing": "0.04em",
                                 "fontWeight": "650"}),
    ], style={"display": "flex", "alignItems": "center", "gap": "6px", "minWidth": "0"})

    return html.Div([
        label_row,
        html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": color,
                                "margin": "4px 0 0 0", "letterSpacing": "-0.02em", "lineHeight": "1.15"}),
        html.Div(sub or "", style={"fontSize": "10.5px", "color": COLORS["muted_light"],
                                    "marginTop": "1px", "whiteSpace": "nowrap", "overflow": "hidden",
                                    "textOverflow": "ellipsis"}),
        trend_row,
    ], className="kpi-card", style=style)


def section_card(title, subtitle, children, style_extra=None, icon="bi bi-bar-chart", accent=None):
    """Titled card for charts/tables. Uses the slightly heavier CHART_CARD_STYLE
    by default (more shadow + radius than KPI cards) so charts read as the
    primary visual layer of the page, per the intended scan order.
    `subtitle` can be a plain string OR a Dash component (e.g. a small control
    row with a dropdown/checklist embedded) — both render fine here."""
    style = dict(CHART_CARD_STYLE)
    if style_extra:
        style.update(style_extra)

    subtitle_el = html.Div(subtitle, style={"fontSize": "11px", "color": COLORS["muted"]})

    title_row = html.Div([
        _icon_badge(icon, (accent + "1A") if accent else COLORS["primary_light"], accent or COLORS["primary"], size=28),
        html.Div([
            html.Div(title, style={"fontSize": "14.5px", "fontWeight": "700", "color": COLORS["text"]}),
            html.Div(subtitle_el, style={"minHeight": "16px", "display": "flex", "alignItems": "center"}),
        ], style={"minWidth": "0", "flex": "1"}),
    ], style={"display": "flex", "alignItems": "flex-start", "gap": "10px", "marginBottom": SPACE["xs"]})

    return html.Div([title_row, children], className="section-card", style=style)


def filter_control(label, control, min_width="160px"):
    """A labeled filter widget for the filter bar — small caps label above a
    borderless dropdown/input, wrapped in a card-like pill so a whole row of
    these reads as one cohesive filter bar rather than loose dropdowns."""
    return html.Div([
        html.Div(label, style={"fontSize": "9px", "fontWeight": "700", "color": COLORS["muted"],
                                "textTransform": "uppercase", "letterSpacing": "0.05em",
                                "marginBottom": "3px"}),
        control,
    ], style={
        "background": COLORS["surface"], "border": f"1px solid {COLORS['border_soft']}",
        "borderRadius": "9px", "padding": "6px 10px", "minWidth": min_width,
        "boxShadow": SHADOW_SM,
    })


def page_header(title, subtitle, badge=None):
    """Page title rendered with the same green gradient as the sidebar nav,
    so the title is unmistakably the top of the scan order on every page.
    `badge` accepts either a plain string (rendered as a small pill next
    to the title) or a full Dash component like a Button (rendered as a
    right-aligned action element in the header row) — so this one function
    covers both a status badge and a page-level action button."""
    badge_el = None
    if badge is not None:
        if isinstance(badge, str):
            badge_el = html.Span(badge, style={
                "fontSize": "10.5px", "fontWeight": "600", "color": COLORS["primary"],
                "background": COLORS["primary_light"], "padding": "3px 9px",
                "borderRadius": "20px", "marginLeft": "10px",
            })
        else:
            badge_el = badge  # render the component (e.g. a button) as-is

    title_el = html.H2(title, style={
        "fontSize": "30px", "fontWeight": "800", "margin": "0",
        "letterSpacing": "-0.02em", "display": "inline-block", "lineHeight": "1.15",
        "backgroundImage": TITLE_GRADIENT,
        "backgroundClip": "text", "WebkitBackgroundClip": "text",
        "color": "transparent", "WebkitTextFillColor": "transparent",
    })

    title_block = html.Div([
        html.Div([
            title_el,
            badge_el if isinstance(badge, str) else None,
        ]),
        html.Div(subtitle, style={"fontSize": "13px", "color": COLORS["muted"], "marginTop": "4px"}),
    ])

    if badge is None or isinstance(badge, str):
        return html.Div([title_block], style={"marginBottom": SPACE["md"]})

    return html.Div([
        title_block,
        html.Div(badge_el, style={"flexShrink": "0"}),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start",
              "marginBottom": SPACE["md"]})


def dark_kpi_card(label, value, sub=None, icon="bi bi-flag-fill"):
    """The Donezo-style dark 'spotlight' card. Use for exactly ONE KPI per
    page — the one you most want the eye to land on first (e.g. the riskiest
    or most important number). Using it on more than one card per row kills
    the effect; it works because it's rare."""
    from utils.theme import COLORS as C
    style = dict(DARK_CARD)
    style.update({"flex": "1", "minWidth": "0"})
    return html.Div([
        html.Div([
            html.Span(label, style={"fontSize": "11.5px", "fontWeight": "500", "color": DARK_CARD_TEXT_MUTED}),
            html.Div(
                html.I(className=icon, style={"fontSize": "13px", "color": DARK_CARD_TEXT}),
                style={"width": "24px", "height": "24px", "borderRadius": "7px",
                       "background": "rgba(255,255,255,0.12)", "display": "flex",
                       "alignItems": "center", "justifyContent": "center"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                  "marginBottom": "10px"}),
        html.Div(value, style={"fontSize": "24px", "fontWeight": "600", "color": DARK_CARD_TEXT}),
        html.Div(sub or "", style={"fontSize": "10.5px", "color": C["primary_soft"], "marginTop": "2px"}),
    ], style=style)


def donut_kpi_card(label, sub, percent, target=None):
    """Circular progress ring for a single rate/percentage metric — reads
    faster than a bar for 'how close to done/target is this one number',
    which is exactly the placement-rate / fulfillment-rate use case.
    Built with a CSS conic-gradient ring (no SVG/data-URI needed)."""
    style = dict(KPI_CARD_STYLE)
    style.update({"flex": "1", "minWidth": "0", "display": "flex",
                  "alignItems": "center", "gap": "12px"})

    ring_outer = html.Div(
        html.Div(f"{percent}%", style={
            "width": "40px", "height": "40px", "borderRadius": "50%",
            "background": COLORS["surface"], "display": "flex",
            "alignItems": "center", "justifyContent": "center",
            "fontSize": "12px", "fontWeight": "700", "color": COLORS["primary_dark"],
        }),
        style={
            "width": "54px", "height": "54px", "borderRadius": "50%",
            "background": f"conic-gradient({COLORS['primary']} 0% {percent}%, {COLORS['primary_light']} {percent}% 100%)",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "flexShrink": "0",
        },
    )

    return html.Div([
        ring_outer,
        html.Div([
            html.Div(label, style={"fontSize": "11.5px", "color": COLORS["text_secondary"], "fontWeight": "600"}),
            html.Div(sub or (f"Target {target}%" if target else ""),
                     style={"fontSize": "10.5px", "color": COLORS["muted"], "marginTop": "1px"}),
        ]),
    ], style=style)