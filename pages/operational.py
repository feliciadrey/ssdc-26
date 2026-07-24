import dash
from dash import html, dcc, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT, PAGE_STYLE, SPACE
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

def empty_fig(height=260, message="No data for this filter"):
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
        placeholder="All semesters", clearable=True, style={"minWidth": "140px", "border": "none"},
    ), min_width="160px"),
    filter_control("Position", dcc.Dropdown(
        id="op-filter-position",
        options=[{"label": s, "value": s} for s in POSITION_OPTIONS],
        placeholder="All positions", clearable=True, style={"minWidth": "160px", "border": "none"},
    ), min_width="180px"),
    filter_control("Work Type", dcc.Dropdown(
        id="op-filter-arr",
        options=[{"label": s, "value": s} for s in WORKING_ARR_OPTIONS],
        placeholder="All types", clearable=True, style={"minWidth": "150px", "border": "none"},
    ), min_width="170px"),
    filter_control("Field of Study", dcc.Dropdown(
        id="op-filter-bidang",
        options=[{"label": s, "value": s} for s in BIDANG_STUDI_OPTIONS],
        placeholder="All fields of study", clearable=True, style={"minWidth": "170px", "border": "none"},
    ), min_width="190px"),
], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["lg"], "flexWrap": "wrap"})

ghosting_toggle = dcc.Checklist(
    id="op-ghosting-cumulative",
    options=[{"label": " Show Cumulative", "value": "cumulative"}],
    value=[], style={"fontSize": "11px", "color": COLORS["muted"]},
)

layout = html.Div([
    page_header("Recruitment Operations",
                "Live status of every request, from submission to placement"),
    html.Div(id="op-export-pdf-dummy", style={"display": "none"}),
    filter_bar,
    html.Div(id="op-kpi-row", style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["sm"]}),

    html.Div([
        section_card("Request Status Breakdown", "Requests by status and placement type",
                     dcc.Graph(id="op-bubble-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "5"}),
        section_card("Recruitment Funnel", "Conversion from sent candidates to placement",
                     dcc.Graph(id="op-funnel-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "5"}),
    ], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["xs"]}),

    html.Div([
        section_card("Ghosting Trend",
                     html.Div(["Candidates gone unresponsive, by month · ", ghosting_toggle],
                              style={"display": "flex", "alignItems": "center", "gap": "6px"}),
                     dcc.Graph(id="op-ghosting-trend-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card(
            "Follow-Up Escalation",
            html.Div([
                html.Span("Unresponsive candidates, by follow-up stage"),
                dbc.Button(
                    "View List ↗",
                    id="op-ghosting-open-link",
                    color="primary",
                    outline=True,
                    size="sm",
                    n_clicks=0,
                    style={"padding": "6px 12px", "fontSize": "12px", "lineHeight": "1.2"},
                ),
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "gap": "10px"}),
            dcc.Graph(id="op-ghosting-stage-graph", config={"displayModeBar": False}),
            style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["xs"]}),

    html.Div([
        section_card("Priority Requests", "Top 10 open requests by age and headcount",
                     html.Div(id="op-priority-table"),
                     style_extra={"flex": "1"}),
    ], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["xs"]}),
    html.Div([
        
    ], style={"display": "flex", "alignItems": "center", "marginTop": SPACE["xs"], "marginBottom": SPACE["sm"]}),
    dbc.Modal([
        dbc.ModalHeader("Ghosting Follow-Up List"),
        dbc.ModalBody([
            html.Div(
                "Candidates and companies marked as ghosting. Needs CDC team follow-up.",
                style={"marginBottom": "12px", "color": COLORS["muted"]},
            ),
            dbc.Alert(id="op-ghosting-modal-alert", color="success", is_open=False, style={"marginBottom": "16px"}),
            dash_table.DataTable(
                id="op-ghosting-detail-table",
                columns=[
                    {"name": "Student ID", "id": "NIM"},
                    {"name": "Name", "id": "student_name"},
                    {"name": "Company", "id": "company"},
                    {"name": "Position", "id": "position"},
                    {"name": "Last Update", "id": "last_update"},
                    {"name": "Rejection Notes", "id": "rejection"},
                ],
                data=[],
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_as_list_view=True,
                style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                              "borderBottom": f"1px solid {COLORS['border']}"},
                style_cell={"fontSize": "11px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif", "whiteSpace": "normal"},
            ),
        ]),
        dbc.ModalFooter([
            dbc.Button("Mark Done", id="op-ghosting-followup-btn", color="primary", n_clicks=0),
            dbc.Button("Close", id="op-ghosting-modal-close", color="secondary", className="ms-2", n_clicks=0),
        ]),
    ], id="op-ghosting-modal", size="xl", is_open=False, backdrop="static"),
], style=PAGE_STYLE)


@callback(
    Output("op-kpi-row", "children"),
    Output("op-bubble-graph", "figure"),
    Output("op-funnel-graph", "figure"),
    Output("op-priority-table", "children"),
    Output("op-ghosting-trend-graph", "figure"),
    Output("op-ghosting-stage-graph", "figure"),
    Output("op-ghosting-detail-table", "data"),
    Input("op-filter-semester", "value"),
    Input("op-filter-position", "value"),
    Input("op-filter-arr", "value"),
    Input("op-filter-bidang", "value"),
    Input("op-ghosting-cumulative", "value"),
)
def update_ops(min_semester, position, arr, bidang, ghosting_mode):
    d = filter_tc(min_semester, position, arr, bidang)
    ts = matching_students(d)

    open_request = int(d["is_open"].sum()) if len(d) else 0
    sent_mask = d["send_date"].notna() if len(d) else pd.Series(dtype=bool)
    avg_processing = round(d.loc[sent_mask, "processing_days"].mean(), 1) if sent_mask.any() else None
    ghosting_count = int((ts["progress_student"] == "Ghosting").sum())

    FOLLOWUP_STAGES = {"FU 1", "FU 2", "FU 3"}
    followup_count = int(ts["progress_student"].isin(FOLLOWUP_STAGES).sum()) if len(ts) else 0

    kpi_row = [
        kpi_card("Open Requests", f"{open_request}", "Positions still unfilled"),
        kpi_card("Avg. Processing Time",
                  f"{avg_processing} days" if avg_processing is not None else "-",
                  "Time from request to candidates sent"),
        kpi_card("Needs Follow-Up", f"{followup_count}", "Candidates in follow-up stage 1-3",
                  color=COLORS["warning"] if followup_count > 0 else COLORS["text"],
                  accent=COLORS["warning"] if followup_count > 0 else None),
        kpi_card("Ghosting Cases", f"{ghosting_count}", "Needs escalation",
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
                                  xaxis_title="Number of Requests", yaxis_title="Status",
                                  legend=dict(orientation="h", y=-0.3, font=dict(size=9)))
    else:
        bubble_fig = empty_fig(260, "Status data unavailable for this filter")

    if len(d) or len(ts):
        total_sent = int(d["jumlah_dikirimkan"].sum()) if len(d) else 0
        stage_counts = ts["progress_student"].value_counts()
        interview_plus = int(stage_counts.get("Interview User", 0) + stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0))
        final_plus = int(stage_counts.get("Final Interview", 0) + stage_counts.get("Placement", 0))
        placed = int(stage_counts.get("Placement", 0))
        funnel_fig = go.Figure(go.Funnel(
            y=["Sent", "In Company Review", "Interview", "Final Interview", "Placement"],
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
                    {"name": "Position", "id": "posisi"},
                    {"name": "Headcount", "id": "headcount_n"},
                    {"name": "Age (Days)", "id": "aging_days"},
                    {"name": "Priority Score", "id": "priority_score"},
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
            priority_table = html.Div("No open requests for this filter.",
                                       style={"fontSize": "12px", "color": COLORS["muted"]})
    else:
        priority_table = html.Div("No data for this filter.",
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
                                            name="Cumulative", line=dict(color=COLORS["primary_dark"], width=2)))
        else:
            trend_fig.add_trace(go.Scatter(x=month_labels, y=monthly_values, mode="lines+markers",
                                            name="Monthly Ghosting", line=dict(color=COLORS["primary_soft"], width=2)))
            trend_fig.add_trace(go.Scatter(x=month_labels, y=pd.Series(monthly_values).cumsum().tolist(),
                                            mode="lines+markers", name="Cumulative",
                                            line=dict(color=COLORS["primary_dark"], width=2, dash="dot")))
        trend_fig.update_layout(**PLOTLY_LAYOUT, height=220, legend=dict(orientation="h", y=-0.3, font=dict(size=9)))
    else:
        trend_fig = empty_fig(220, "No ghosting data for this filter")

    if len(ts_ghost):
        ghosting_detail_data = ts_ghost[["NIM", "student_name", "company", "position", "last_update", "rejection"]].copy()
        ghosting_detail_data["last_update"] = ghosting_detail_data["last_update"].dt.strftime("%Y-%m-%d")
        ghosting_detail_data = ghosting_detail_data.to_dict("records")
    else:
        ghosting_detail_data = []

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
        stage_fig.update_layout(**PLOTLY_LAYOUT, height=220, xaxis_title="Number of Candidates")
        stage_fig.update_yaxes(autorange="reversed")
    else:
        stage_fig = empty_fig(220, "No candidates in follow-up for this filter")

    return kpi_row, bubble_fig, funnel_fig, priority_table, trend_fig, stage_fig, ghosting_detail_data


@callback(
    Output("op-ghosting-modal", "is_open"),
    Output("op-ghosting-modal-alert", "children"),
    Output("op-ghosting-modal-alert", "is_open"),
    Input("op-ghosting-open-link", "n_clicks"),
    Input("op-ghosting-modal-close", "n_clicks"),
    Input("op-ghosting-followup-btn", "n_clicks"),
    State("op-ghosting-modal", "is_open"),
)
def toggle_ghosting_modal(open_clicks, close_clicks, followup_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", False

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "op-ghosting-open-link":
        return True, "", False
    if trigger_id == "op-ghosting-modal-close":
        return False, "", False
    if trigger_id == "op-ghosting-followup-btn":
        return True, "Follow-up logged. CDC team can proceed with outreach.", True

    return is_open, "", False