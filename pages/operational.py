import dash
from dash import html, dcc, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT
from utils.components import kpi_card, section_card, page_header

dash.register_page(__name__, path="/", name="Performance Overview")

data = load_all()
tracking_company = data["tracking_company"]
tracking_student = data["tracking_student"]
talent_request = data["talent_request"]
company = data["company"]

# ---- KPI calculations ----
total_requests = len(talent_request)
total_sent = int(tracking_company["jumlah_dikirimkan"].sum())
total_requested = int(tracking_company["jumlah_permintaan"].sum())
fulfillment_rate = round(100 * total_sent / total_requested, 0) if total_requested else 0

total_placed = int((tracking_student["progress_student"] == "Placement").sum())
placement_rate = round(100 * total_placed / len(tracking_student), 1) if len(tracking_student) else 0

ghosting_count = int((tracking_student["progress_student"] == "Ghosting").sum())
ghosting_rate = round(100 * ghosting_count / len(tracking_student), 1) if len(tracking_student) else 0

kpi_row = html.Div([
    kpi_card("Talent request masuk", f"{total_requests}", "Semester berjalan"),
    kpi_card("Kandidat dikirim", f"{total_sent}", f"Fulfillment {fulfillment_rate:.0f}% dari diminta"),
    kpi_card("Placement rate", f"{placement_rate}%", "Target 45%",
             color=COLORS["success"] if placement_rate >= 40 else COLORS["warning"],
             accent=COLORS["success"] if placement_rate >= 40 else COLORS["warning"]),
    kpi_card("Total placement", f"{total_placed}", "Kandidat berhasil ditempatkan",
             color=COLORS["success"], accent=COLORS["success"]),
    kpi_card("Ghosting rate", f"{ghosting_rate}%", "Dari total kandidat ditracking",
             color=COLORS["danger"] if ghosting_rate > 7 else COLORS["text"],
             accent=COLORS["danger"] if ghosting_rate > 7 else None),
], style={"display": "flex", "gap": "12px", "marginBottom": "16px"})

# ---- Funnel ----
stage_counts = tracking_student["progress_student"].value_counts()
funnel_fig = go.Figure(go.Funnel(
    y=["Dikirim", "Diproses perusahaan", "Interview", "Final interview", "Placement"],
    x=[
        total_sent,
        len(tracking_student),
        int(stage_counts.get("Interview User", 0) + stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0)),
        int(stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0)),
        total_placed,
    ],
    marker={"color": [CATEGORICAL[0]] * 4 + [COLORS["success"]]},
    textinfo="value+percent previous",
))
funnel_fig.update_layout(**PLOTLY_LAYOUT, height=260)

# ---- Composition by jenis penempatan ----
jenis_counts = tracking_student["jenis_penempatan"].value_counts().sort_values()
bar_fig = go.Figure(go.Bar(
    x=jenis_counts.values, y=jenis_counts.index, orientation="h",
    marker_color=CATEGORICAL[0],
))
bar_fig.update_layout(**PLOTLY_LAYOUT, height=260, xaxis_title=None, yaxis_title=None)

# ---- Trend by month ----
tc = tracking_company.dropna(subset=["send_date"]).copy()
tc["month"] = tc["send_date"].dt.to_period("M").astype(str)
trend = tc.groupby("month")["jumlah_dikirimkan"].sum().reset_index()
trend_fig = go.Figure()
trend_fig.add_trace(go.Scatter(x=trend["month"], y=trend["jumlah_dikirimkan"],
                                mode="lines+markers", line=dict(color=CATEGORICAL[0], width=2)))
if len(trend):
    target = trend["jumlah_dikirimkan"].mean() * 1.15
    trend_fig.add_hline(y=target, line_dash="dash", line_color=COLORS["danger"],
                         annotation_text="Target")
trend_fig.update_layout(**PLOTLY_LAYOUT, height=200)

# ---- Placement rate by prodi ----
ts_with_prodi = tracking_student.merge(
    data["student_all"][["NIM", "program_studi"]], on="NIM", how="left"
)
prodi_summary = ts_with_prodi.groupby("program_studi").agg(
    total=("NIM", "count"),
    placed=("progress_student", lambda s: (s == "Placement").sum())
).reset_index()
prodi_summary["rate"] = pd.to_numeric(
    100 * prodi_summary["placed"] / prodi_summary["total"],
    errors="coerce",
).round(1).fillna(0)
prodi_summary = prodi_summary.sort_values("rate", ascending=True)
avg_rate = prodi_summary["rate"].mean() if len(prodi_summary) else 0
prodi_summary["color"] = prodi_summary["rate"].apply(
    lambda r: COLORS["success"] if r >= avg_rate else (COLORS["warning"] if r >= avg_rate * 0.7 else COLORS["danger"])
)
prodi_fig = go.Figure(go.Bar(
    x=prodi_summary["rate"], y=prodi_summary["program_studi"], orientation="h",
    marker_color=prodi_summary["color"],
))
prodi_fig.update_layout(**PLOTLY_LAYOUT, height=260, xaxis_title="Placement rate (%)")

# ---- Company leaderboard ----
comp_summary = tracking_company.groupby("nama_perusahaan").agg(
    diminta=("jumlah_permintaan", "sum"),
    dikirim=("jumlah_dikirimkan", "sum"),
).reset_index()
ts_company = tracking_student.groupby("company")["progress_student"].apply(
    lambda s: (s == "Placement").sum()
).reset_index(name="placed")
comp_summary = comp_summary.merge(ts_company, left_on="nama_perusahaan", right_on="company", how="left")
comp_summary["placed"] = comp_summary["placed"].fillna(0).astype(int)
comp_summary["rate_%"] = pd.to_numeric(
    100 * comp_summary["placed"] / comp_summary["dikirim"].replace(0, pd.NA),
    errors="coerce",
).round(0).fillna(0)
comp_summary = comp_summary.sort_values("rate_%", ascending=False).head(10)
comp_table = dash_table.DataTable(
    columns=[
        {"name": "Company", "id": "nama_perusahaan"},
        {"name": "Dikirim", "id": "dikirim"},
        {"name": "Placed", "id": "placed"},
        {"name": "Rate %", "id": "rate_%"},
    ],
    data=comp_summary[["nama_perusahaan", "dikirim", "placed", "rate_%"]].to_dict("records"),
    style_as_list_view=True,
    style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600",
                  "fontSize": "11px", "borderBottom": f"1px solid {COLORS['border']}"},
    style_cell={"fontSize": "12px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
    style_data_conditional=[{
        "if": {"filter_query": "{rate_%} >= 50", "column_id": "rate_%"},
        "color": COLORS["success"], "fontWeight": "600",
    }],
)

layout = html.Div([
    page_header("Placement Performance Overview", "Genap 2025/2026 · seluruh program studi"),
    kpi_row,
    html.Div([
        section_card("Placement funnel", "Konversi dari dikirim ke placement",
                     dcc.Graph(figure=funnel_fig, config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card("Placement by jenis penempatan", "Magang / part-time / full-time",
                     dcc.Graph(figure=bar_fig, config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),

    section_card("Placement trend by month", "Jumlah kandidat dikirim, dengan target reference line",
                 dcc.Graph(figure=trend_fig, config={"displayModeBar": False}),
                 style_extra={"marginBottom": "12px"}),

    html.Div([
        section_card("Placement rate by program studi", "Sorted, hijau = di atas rata-rata",
                     dcc.Graph(figure=prodi_fig, config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card("Top companies by acceptance rate", "10 besar",
                     comp_table, style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": "12px"}),
], style={"padding": "24px", "background": COLORS["bg"], "minHeight": "100vh"})