import dash
from dash import html, dcc, dash_table, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT
from utils.components import kpi_card, section_card, page_header, filter_control

dash.register_page(__name__, path="/operational", name="Recruitment Ops")

TODAY = pd.Timestamp(datetime(2026, 7, 18))


data = load_all()
tracking_company = data["tracking_company"].copy()
tracking_student = data["tracking_student"].copy()
talent_request = data["talent_request"].copy()


def _merge_request_detail(tc_df, tr_df):
    detail_cols = ["headcount", "minimum_semester", "working_arrangement", "bidang_studi_dibutuhkan"]
    if "id_talent_req" in tc_df.columns and "id_talent_req" in tr_df.columns:
        cols = ["id_talent_req"] + [c for c in detail_cols if c in tr_df.columns]
        return tc_df.merge(tr_df[cols], on="id_talent_req", how="left")
    tr_r = tr_df.rename(columns={"nama_posisi": "posisi"})
    cols = ["nama_perusahaan", "posisi"] + [c for c in detail_cols if c in tr_r.columns]
    return tc_df.merge(tr_r[cols], on=["nama_perusahaan", "posisi"], how="left")


tc = _merge_request_detail(tracking_company, talent_request)
tc["aging_days"] = (TODAY - tc["request_date"]).dt.days
tc["is_open"] = tc["jumlah_dikirimkan"] < tc["jumlah_permintaan"]
tc["processing_days"] = (tc["send_date"].fillna(TODAY) - tc["request_date"]).dt.days

MIN_SEMESTER_OPTIONS = sorted(int(s) for s in tc["minimum_semester"].dropna().unique()) if "minimum_semester" in tc else []
POSITION_OPTIONS = sorted(s for s in tc["posisi"].dropna().unique())
WORKING_ARR_OPTIONS = sorted(s for s in tc["working_arrangement"].dropna().unique()) if "working_arrangement" in tc else []
BIDANG_STUDI_OPTIONS = sorted(s for s in tc["bidang_studi_dibutuhkan"].dropna().unique()) if "bidang_studi_dibutuhkan" in tc else []

def empty_fig(height=260, message="Tidak ada data untuk filter ini"):
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=COLORS["muted"], size=12))
    return fig


def filter_tc(min_semester, position, arr, bidang):
    d = tc.copy()
    if min_semester is not None:
        d = d[d["minimum_semester"] == min_semester]
    if position:
        d = d[d["posisi"] == position]
    if arr:
        d = d[d["working_arrangement"] == arr]
    if bidang:
        d = d[d["bidang_studi_dibutuhkan"] == bidang]
    return d


def matching_students(d):
    if not len(d):
        return tracking_student.iloc[0:0].copy()
    if "id_tracking_company" in d.columns and "id_tracking_company" in tracking_student.columns:
        ids = set(d["id_tracking_company"])
        return tracking_student[tracking_student["id_tracking_company"].isin(ids)].copy()
    # fallback for datasets missing the FK column - can over-match on recurring postings
    pairs = set(zip(d["nama_perusahaan"], d["posisi"]))
    mask = [p in pairs for p in zip(tracking_student["company"], tracking_student["position"])]
    return tracking_student[mask].copy()

filter_bar = html.Div([
    filter_control("Min Semester", dcc.Dropdown(
        id="op-filter-semester",
        options=[{"label": str(s), "value": s} for s in MIN_SEMESTER_OPTIONS],
        placeholder="Semua semester", clearable=True, style={"minWidth": "140px", "border": "none"},
    ), min_width="160px"),
    filter_control("Position", dcc.Dropdown(
        id="op-filter-position",
        options=[{"label": s, "value": s} for s in POSITION_OPTIONS],
        placeholder="Semua posisi", clearable=True, style={"minWidth": "160px", "border": "none"},
    ), min_width="180px"),
    filter_control("Working Arr.", dcc.Dropdown(
        id="op-filter-arr",
        options=[{"label": s, "value": s} for s in WORKING_ARR_OPTIONS],
        placeholder="Semua tipe", clearable=True, style={"minWidth": "150px", "border": "none"},
    ), min_width="170px"),
    filter_control("Bidang Studi", dcc.Dropdown(
        id="op-filter-bidang",
        options=[{"label": s, "value": s} for s in BIDANG_STUDI_OPTIONS],
        placeholder="Semua bidang", clearable=True, style={"minWidth": "170px", "border": "none"},
    ), min_width="190px"),
], style={"display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap", "alignItems": "flex-start"})

ghosting_toggle = dcc.Checklist(
    id="op-ghosting-cumulative",
    options=[{"label": " Tampilkan kumulatif", "value": "cumulative"}],
    value=[], style={"fontSize": "11px", "color": COLORS["muted"]},
)

layout = html.Div([
    page_header("Recruitment Operations",
                "Program manager view · update real-time"),
    html.Div(id="op-export-pdf-dummy", style={"display": "none"}),
    filter_bar,
    html.Div(id="op-kpi-row", style={"display": "flex", "gap": "12px", "marginBottom": "16px", "flexWrap": "wrap"}),

    html.Div([
        section_card("Distribusi Progress Request", "Status pengiriman saat ini, per jenis penempatan",
                     dcc.Graph(id="op-bubble-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Recruitment Funnel", "Konversi dari dikirim ke placement",
                     dcc.Graph(id="op-funnel-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Priority Req Table", "Skor = usia request x headcount, top 10 masih terbuka",
                     html.Div(id="op-priority-table", style={"height": "260px", "overflowY": "auto"}),
                     style_extra={"flex": "4"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),

    html.Div([
        section_card("Ghosting Trend",
                     html.Div(["Per bulan · ", ghosting_toggle],
                              style={"display": "flex", "alignItems": "center", "gap": "6px"}),
                     dcc.Graph(id="op-ghosting-trend-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card(
            "Eskalasi Follow-Up ke Ghosting",
            "Kandidat belum merespons, per level follow-up",
            dcc.Graph(id="op-ghosting-stage-graph", config={"displayModeBar": False}),
            style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": "12px"}),
], style={"padding": "24px", "background": COLORS["bg"], "minHeight": "100vh"})


@callback(
    Output("op-kpi-row", "children"),
    Output("op-bubble-graph", "figure"),
    Output("op-funnel-graph", "figure"),
    Output("op-priority-table", "children"),
    Output("op-ghosting-trend-graph", "figure"),
    Output("op-ghosting-stage-graph", "figure"),
    Input("op-filter-semester", "value"),
    Input("op-filter-position", "value"),
    Input("op-filter-arr", "value"),
    Input("op-filter-bidang", "value"),
    Input("op-ghosting-cumulative", "value"),
)
def update_ops(min_semester, position, arr, bidang, ghosting_mode):
    d = filter_tc(min_semester, position, arr, bidang)
    ts = matching_students(d)

    # ---- KPIs ----
    open_request = int(d["is_open"].sum()) if len(d) else 0
    sent_mask = d["send_date"].notna() if len(d) else pd.Series(dtype=bool)
    avg_processing = round(d.loc[sent_mask, "processing_days"].mean(), 1) if sent_mask.any() else None
    ghosting_count = int((ts["progress_student"] == "Ghosting").sum())

    FOLLOWUP_STAGES = {"FU 1", "FU 2", "FU 3"}
    followup_count = int(ts["progress_student"].isin(FOLLOWUP_STAGES).sum()) if len(ts) else 0

    kpi_row = [
        kpi_card("Open Request", f"{open_request}", "Belum sepenuhnya terpenuhi"),
        kpi_card("Average Processing Time",
                  f"{avg_processing} hari" if avg_processing is not None else "-",
                  "Request date -> send date"),
        kpi_card("Perlu Follow-up", f"{followup_count}", "Kandidat FU 1-3, sebelum berstatus Ghosting",
                  color=COLORS["warning"] if followup_count > 0 else COLORS["text"],
                  accent=COLORS["warning"] if followup_count > 0 else None),
        kpi_card("Jumlah Ghosting", f"{ghosting_count}", "Perlu eskalasi",
                  color=COLORS["danger"], accent=COLORS["danger"]),
    ]

    PROGRESS_ORDER = ["Draft", "Submitted", "On Review", "Shortlisted", "Closed"]

    if len(d) and "progress" in d.columns and "jenis_penempatan" in d.columns:
        present = [p for p in PROGRESS_ORDER if p in d["progress"].unique()]
        other_progress = sorted(p for p in d["progress"].dropna().unique() if p not in PROGRESS_ORDER)
        row_order = list(reversed(present + other_progress))

        jenis_values = sorted(d["jenis_penempatan"].dropna().unique())
        bubble_fig = go.Figure()
        for i, jp in enumerate(jenis_values):
            sub = d[d["jenis_penempatan"] == jp]
            counts = sub["progress"].value_counts().reindex(row_order, fill_value=0)
            bubble_fig.add_trace(go.Bar(
                y=row_order, x=counts.values, name=str(jp), orientation="h",
                marker_color=CATEGORICAL[i % len(CATEGORICAL)],
            ))
        bubble_fig.update_layout(**PLOTLY_LAYOUT, height=260, barmode="stack",
                                  xaxis_title="Jumlah request", yaxis_title="Progress",
                                  legend=dict(orientation="h", y=-0.3, font=dict(size=9)))
    else:
        bubble_fig = empty_fig(260, "Data progress / jenis penempatan tidak tersedia untuk filter ini")

    if len(d) or len(ts):
        total_sent = int(d["jumlah_dikirimkan"].sum()) if len(d) else 0
        stage_counts = ts["progress_student"].value_counts()
        interview_plus = int(stage_counts.get("Interview User", 0) + stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0))
        final_plus = int(stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0))
        placed = int(stage_counts.get("Placement", 0))
        funnel_fig = go.Figure(go.Funnel(
            y=["Dikirim", "Diproses perusahaan", "Interview", "Final interview", "Placement"],
            x=[total_sent, len(ts), interview_plus, final_plus, placed],
            marker={"color": [CATEGORICAL[0]] * 4 + [COLORS["success"]]},
            textinfo="value+percent previous",
        ))
        funnel_fig.update_layout(**PLOTLY_LAYOUT, height=260)
    else:
        funnel_fig = empty_fig(260)

    if len(d):
        open_d = d[d["is_open"]].copy()
        if len(open_d) and "headcount" in open_d.columns:
            open_d["headcount_n"] = pd.to_numeric(open_d["headcount"], errors="coerce").fillna(1)
            open_d["priority_score"] = (open_d["aging_days"].clip(lower=0) * open_d["headcount_n"]).round(0)
            open_d = open_d.sort_values("priority_score", ascending=False).head(10)
            priority_table = dash_table.DataTable(
                columns=[
                    {"name": "Company", "id": "nama_perusahaan"},
                    {"name": "Posisi", "id": "posisi"},
                    {"name": "Headcount", "id": "headcount_n"},
                    {"name": "Usia (hari)", "id": "aging_days"},
                    {"name": "Skor", "id": "priority_score"},
                ],
                data=open_d[["nama_perusahaan", "posisi", "headcount_n", "aging_days", "priority_score"]].to_dict("records"),
                style_as_list_view=True,
                style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                              "borderBottom": f"1px solid {COLORS['border']}"},
                style_cell={"fontSize": "11px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
                style_data_conditional=[
                    {"if": {"filter_query": "{aging_days} > 7"}, "backgroundColor": COLORS["danger_bg"]},
                ],
            )
        else:
            priority_table = html.Div("Tidak ada request terbuka untuk filter ini.",
                                       style={"fontSize": "12px", "color": COLORS["muted"]})
    else:
        priority_table = html.Div("Tidak ada data untuk filter ini.",
                                   style={"fontSize": "12px", "color": COLORS["muted"]})
        
    ts_ghost = ts[ts["progress_student"] == "Ghosting"]
    if len(ts_ghost) and ts_ghost["last_update"].notna().any():
        by_month = (
            ts_ghost.dropna(subset=["last_update"])
                    .groupby(ts_ghost["last_update"].dt.to_period("M"))
                    .size()
        )
        months = sorted(by_month.index)
        month_labels = [str(m) for m in months]
        monthly_values = [by_month.get(m, 0) for m in months]
        trend_fig = go.Figure()
        if "cumulative" in (ghosting_mode or []):
            cum_values = pd.Series(monthly_values).cumsum().tolist()
            trend_fig.add_trace(go.Scatter(x=month_labels, y=cum_values, mode="lines+markers",
                                            name="Kumulatif", line=dict(color=COLORS["primary_dark"], width=2)))
        else:
            trend_fig.add_trace(go.Scatter(x=month_labels, y=monthly_values, mode="lines+markers",
                                            name="Ghosting per bulan", line=dict(color=COLORS["primary_soft"], width=2)))
            trend_fig.add_trace(go.Scatter(x=month_labels, y=pd.Series(monthly_values).cumsum().tolist(),
                                            mode="lines+markers", name="Kumulatif",
                                            line=dict(color=COLORS["primary_dark"], width=2, dash="dot")))
        trend_fig.update_layout(**PLOTLY_LAYOUT, height=220, legend=dict(orientation="h", y=-0.3, font=dict(size=9)))
    else:
        trend_fig = empty_fig(220, "Belum ada data ghosting untuk filter ini")

    FU_STAGES = ["FU 1", "FU 2", "FU 3", "Ghosting"]
    FU_COLORS = {
        "FU 1": CATEGORICAL[0],
        "FU 2": CATEGORICAL[1] if len(CATEGORICAL) > 1 else COLORS["primary_soft"],
        "FU 3": CATEGORICAL[2] if len(CATEGORICAL) > 2 else COLORS["primary"],
        "Ghosting": COLORS["primary_dark"],
    }
    if len(ts) and ts["progress_student"].isin(FU_STAGES).any():
        fu_counts = ts["progress_student"].value_counts().reindex(FU_STAGES, fill_value=0)
        stage_fig = go.Figure(go.Bar(
            x=fu_counts.values, y=fu_counts.index, orientation="h",
            marker_color=[FU_COLORS[s] for s in fu_counts.index],
        ))
        stage_fig.update_layout(**PLOTLY_LAYOUT, height=220, xaxis_title="Jumlah kandidat")
        stage_fig.update_yaxes(autorange="reversed")
    else:
        stage_fig = empty_fig(220, "Belum ada kandidat di tahap follow-up untuk filter ini")

    return kpi_row, bubble_fig, funnel_fig, priority_table, trend_fig, stage_fig