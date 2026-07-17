import dash
from dash import html, dcc, dash_table
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT
from utils.components import section_card, page_header

dash.register_page(__name__, path="/operational", name="Operational Pulse")

data = load_all()
tracking_company = data["tracking_company"]
tracking_student = data["tracking_student"]

TODAY = pd.Timestamp(datetime(2026, 7, 17))

# ---- Alert cards ----
ghosting_count = int((tracking_student["progress_student"] == "Ghosting").sum())
fu_count = int(tracking_student["progress_student"].isin(["FU 1", "FU 2", "FU 3"]).sum())
unprocessed = int((tracking_company["progress"] == "Draft").sum())


def alert_card(label, value, bg, fg, note):
    return html.Div([
        html.Div(label, style={"fontSize": "11px", "color": fg}),
        html.Div(str(value), style={"fontSize": "26px", "fontWeight": "700", "color": fg}),
        html.Div(note, style={"fontSize": "10px", "color": fg}),
    ], style={"background": bg, "border": f"1px solid {fg}33", "borderRadius": "8px",
              "padding": "14px 16px", "flex": "1"})


alert_row = html.Div([
    alert_card("Ghosting aktif", ghosting_count, COLORS["danger_bg"], COLORS["danger"],
               "Perlu eskalasi segera"),
    alert_card("Perlu follow-up", fu_count, COLORS["warning_bg"], COLORS["warning"],
               "Status FU1 / FU2 / FU3"),
    alert_card("Request belum diproses", unprocessed, COLORS["success_bg"], COLORS["success"],
               "Status masih Draft"),
], style={"display": "flex", "gap": "12px", "marginBottom": "16px"})

# ---- Stage distribution ----
stage_order = ["Selecting Student by Company", "Study Case", "CDC Briefing Student",
               "Interview User", "Final Interview", "Placement", "FU 1", "FU 2", "FU 3",
               "Ghosting", "Rejected", "Finish"]
stage_counts = tracking_student["progress_student"].value_counts().reindex(stage_order, fill_value=0)
stage_colors = {
    "Placement": COLORS["success"], "Ghosting": COLORS["danger"], "Rejected": COLORS["muted"],
    "FU 1": COLORS["warning"], "FU 2": COLORS["warning"], "FU 3": COLORS["warning"],
}
colors = [stage_colors.get(s, CATEGORICAL[0]) for s in stage_order]

stage_fig = go.Figure()
for stage, count, color in zip(stage_order, stage_counts.values, colors):
    stage_fig.add_trace(go.Bar(x=[count], y=["Progress"], name=stage, orientation="h",
                                marker_color=color, hovertemplate=f"{stage}: {count}<extra></extra>"))
stage_fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", height=110, showlegend=True,
                         legend=dict(orientation="h", font=dict(size=9), y=-0.6),
                         yaxis=dict(visible=False))

# ---- SLA aging table ----
tr = tracking_company.copy()
tr["days_since_request"] = (TODAY - tr["request_date"]).dt.days
tr_no_send = tr[tr["send_date"].isna()].sort_values("days_since_request", ascending=False)


def age_color(days):
    if days > 7:
        return COLORS["danger_bg"]
    if days >= 3:
        return COLORS["warning_bg"]
    return COLORS["success_bg"]


sla_table = dash_table.DataTable(
    columns=[
        {"name": "Company", "id": "nama_perusahaan"},
        {"name": "Posisi", "id": "posisi"},
        {"name": "Hari sejak request", "id": "days_since_request"},
    ],
    data=tr_no_send[["nama_perusahaan", "posisi", "days_since_request"]].head(10).to_dict("records"),
    style_as_list_view=True,
    style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                  "borderBottom": f"1px solid {COLORS['border']}"},
    style_cell={"fontSize": "12px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
    style_data_conditional=[
        {"if": {"filter_query": "{days_since_request} > 7"}, "backgroundColor": COLORS["danger_bg"]},
        {"if": {"filter_query": "{days_since_request} >= 3 && {days_since_request} <= 7"},
         "backgroundColor": COLORS["warning_bg"]},
    ],
)

# ---- Company x FU heatmap ----
fu_data = tracking_student[tracking_student["progress_student"].isin(["FU 1", "FU 2", "FU 3"])]
if len(fu_data):
    heat = fu_data.pivot_table(index="company", columns="progress_student", values="NIM",
                                aggfunc="count", fill_value=0)
    heat = heat.reindex(columns=["FU 1", "FU 2", "FU 3"], fill_value=0)
    heatmap_fig = go.Figure(go.Heatmap(
        z=heat.values, x=heat.columns, y=heat.index,
        colorscale=[[0, COLORS["surface"]], [1, COLORS["danger"]]],
        showscale=False,
    ))
else:
    heatmap_fig = go.Figure()
heatmap_fig.update_layout(**PLOTLY_LAYOUT, height=220)

# ---- Detail tracking table ----
detail_table = dash_table.DataTable(
    columns=[
        {"name": "Perusahaan", "id": "nama_perusahaan"},
        {"name": "Posisi", "id": "posisi"},
        {"name": "Request date", "id": "request_date"},
        {"name": "Send date", "id": "send_date"},
        {"name": "Diminta", "id": "jumlah_permintaan"},
        {"name": "Dikirim", "id": "jumlah_dikirimkan"},
        {"name": "Progress", "id": "progress"},
    ],
    data=tracking_company.assign(
        request_date=tracking_company["request_date"].dt.date.astype(str),
        send_date=tracking_company["send_date"].dt.date.astype(str).replace("NaT", "-"),
    )[["nama_perusahaan", "posisi", "request_date", "send_date",
       "jumlah_permintaan", "jumlah_dikirimkan", "progress"]].to_dict("records"),
    style_as_list_view=True,
    page_size=8,
    filter_action="native",
    sort_action="native",
    style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                  "borderBottom": f"1px solid {COLORS['border']}"},
    style_cell={"fontSize": "12px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
)

layout = html.Div([
    page_header("Operational Pulse & Ghosting Radar", "Program manager view · update real-time"),
    alert_row,
    section_card("Progress stage distribution", "Jumlah kandidat per tahapan seleksi",
                 dcc.Graph(figure=stage_fig, config={"displayModeBar": False}),
                 style_extra={"marginBottom": "12px"}),
    html.Div([
        section_card("Talent request SLA / aging", "Belum ada send_date, diurutkan dari paling lama",
                     sla_table, style_extra={"flex": "6"}),
        section_card("Company x follow-up stage", "Warna makin gelap = makin banyak stuck",
                     dcc.Graph(figure=heatmap_fig, config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
    section_card("Tracking company detail", "Filterable & sortable — klik header kolom untuk sort",
                 detail_table),
], style={"padding": "24px", "background": COLORS["bg"], "minHeight": "100vh"})