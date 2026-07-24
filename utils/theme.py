COLORS = {
    "bg": "#E1F3E7",
    "surface": "#FFFFFF",
    "surface_alt": "#EAF2ED",
    "surface_raised": "#FFFFFF",
    "border": "#DCE6DF",
    "border_soft": "#E9F0EA",

    "text": "#101B14",
    "text_secondary": "#3D4C42",
    "muted": "#6B7A70",
    "muted_light": "#9AA79E",

    "primary": "#1B6B47",
    "primary_dark": "#0F4A30",
    "primary_light": "#E1F0E6",
    "primary_soft": "#2F8259",

    "success": "#1F8A5A",
    "success_bg": "#E5F5EC",
    "success_border": "#BFE3CE",
    "warning": "#B8860B",
    "warning_bg": "#FBF1DC",
    "warning_border": "#F0DCA0",
    "danger": "#B23A3A",
    "danger_bg": "#FBEAEA",
    "danger_border": "#EFC4C4",

    "accent": "#2F6FED",
}

CATEGORICAL = [
    "#1B6B47", "#5FA37A", "#8FBFA0", "#B8860B",
    "#4A7C6B", "#6B7A70", "#B23A3A", "#9AA79E",
]

SHADOW_SM = "0 1px 2px rgba(16, 27, 20, 0.04), 0 1px 1px rgba(16, 27, 20, 0.03)"
SHADOW_MD = "0 4px 12px rgba(16, 27, 20, 0.06), 0 2px 4px rgba(16, 27, 20, 0.04)"
SHADOW_LG = "0 12px 28px rgba(16, 27, 20, 0.10), 0 4px 8px rgba(16, 27, 20, 0.05)"


SPACE = {
    "3xs": "2px",
    "2xs": "4px",
    "xs": "8px",
    "sm": "12px",
    "md": "16px",
    "lg": "20px",
    "xl": "24px",
    "2xl": "32px",
}

PAGE_STYLE = {
    "padding": SPACE["lg"],
    "background": COLORS["bg"],
    "minHeight": "100vh",
}

CARD_STYLE = {
    "background": f"linear-gradient(180deg, {COLORS['surface']} 0%, #FDFEFC 100%)",
    "border": f"1px solid {COLORS['border_soft']}",
    "borderRadius": "12px",
    "padding": "14px 16px",
    "boxShadow": SHADOW_SM,
    "transition": "box-shadow 0.2s ease, transform 0.2s ease",
}

CHART_CARD_STYLE = {
    "background": f"linear-gradient(180deg, {COLORS['surface']} 0%, #FDFEFC 100%)",
    "border": f"1px solid {COLORS['border_soft']}",
    "borderRadius": "14px",
    "padding": "16px 18px",
    "boxShadow": SHADOW_MD,
    "transition": "box-shadow 0.2s ease, transform 0.2s ease",
}


KPI_CARD_STYLE = {
    "background": COLORS["surface"],
    "border": f"1px solid {COLORS['border_soft']}",
    "borderRadius": "12px",
    "padding": "11px 14px 12px",
    "boxShadow": SHADOW_SM,
    "transition": "box-shadow 0.2s ease, transform 0.2s ease",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=40, r=20, t=24, b=28),
    colorway=CATEGORICAL,
)

SIDEBAR_WIDTH = "232px"
SIDEBAR_GRADIENT = f"linear-gradient(180deg, {COLORS['primary_dark']} 0%, {COLORS['primary']} 55%, {COLORS['primary_soft']} 100%)"

TITLE_GRADIENT = f"linear-gradient(90deg, {COLORS['primary_dark']} 0%, {COLORS['primary']} 55%, {COLORS['primary_soft']} 100%)"
RADIUS_SM = "8px"
RADIUS_MD = "12px"
RADIUS_LG = "16px"

DARK_CARD = {
    "background": COLORS["primary_dark"],
    "borderRadius": "14px",
    "padding": "14px 16px",
}
DARK_CARD_TEXT_MUTED = "#9FE1CB"
DARK_CARD_TEXT = "#EAF3DE"