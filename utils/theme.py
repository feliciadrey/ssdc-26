COLORS = {
    "bg": "#F7F7F4",
    "surface": "#FFFFFF",
    "border": "#E4E2DC",
    "text": "#1F1F1D",
    "muted": "#6B6A63",
    "success": "#2E9E5B",
    "success_bg": "#EAF6EE",
    "warning": "#E3A008",
    "warning_bg": "#FDF3DE",
    "danger": "#D64545",
    "danger_bg": "#FBEAEA",
    "accent": "#2F6FED",
}

CATEGORICAL = ["#2F6FED", "#7C6FEF", "#2E9E5B", "#E3A008", "#E38B00", "#6B6A63", "#D64545", "#9AA0A6"]

CARD_STYLE = {
    "background": COLORS["surface"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "8px",
    "padding": "14px 16px",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface"],
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=40, r=20, t=30, b=30),
)