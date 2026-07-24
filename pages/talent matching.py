import dash
from dash import html, dcc, dash_table, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import re
from datetime import datetime

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT, PAGE_STYLE, SPACE
from utils.components import kpi_card, section_card, page_header, filter_control

dash.register_page(__name__, path="/talent-matching", name="Talent Matching")

TODAY = pd.Timestamp(datetime(2026, 7, 18))

data = load_all()
student_all = data["student_all"].copy()
status_student = data["status_student"].copy()
talent_request = data["talent_request"].copy()
company = data["company"].copy()
tracking_student = data["tracking_student"].copy()

for _df in (student_all, status_student, talent_request, company, tracking_student):
    _df.columns = _df.columns.str.strip().str.lower()

tracking_student["last_update"] = pd.to_datetime(tracking_student["last_update"], errors="coerce")

last_activity_by_nim = tracking_student.groupby("nim")["last_update"].max()

_tracking_sorted = tracking_student.dropna(subset=["last_update"]).sort_values("last_update")
latest_rejection_by_nim = _tracking_sorted.groupby("nim")["rejection"].last()

company_lookup = company.rename(columns={"company_name": "nama_perusahaan"})[
    ["nama_perusahaan", "kota"]
].drop_duplicates(subset="nama_perusahaan")
tr = talent_request.merge(company_lookup, on="nama_perusahaan", how="left")

sp = student_all.merge(
    status_student, on="nim", how="left", suffixes=("_all", "_status")
)

sp["program_studi"] = sp["program_studi_status"].fillna(sp["program_studi_all"])
sp["semester"] = pd.to_numeric(sp["semester_status"], errors="coerce").fillna(
    pd.to_numeric(sp["semester_all"], errors="coerce")
)
sp["is_synced"] = sp["sync_date"].notna()

STALE_WEEKS = 7
STALE_DAYS = STALE_WEEKS * 7

sp["last_activity_date"] = sp["nim"].map(last_activity_by_nim)
sp["activity_gap_days"] = (sp["last_activity_date"] - sp["sync_date"]).dt.days

sp["doc_complete"] = (
    sp["cv"].astype(str).str.strip().str.lower().eq("ada")
    & sp["portofolio"].astype(str).str.strip().str.lower().eq("ada")
)

sp["is_active"] = sp["status"].astype(str).str.strip().str.lower().eq("active")
sp["is_eligible"] = sp["is_active"] & sp["doc_complete"] & sp["ipk"].notna()


def is_available_status(value):
    text = str(value).lower()
    return any(k in text for k in ["siap", "tersedia", "available", "ready"])


sp["is_available"] = sp["ketersediaan"].apply(is_available_status) if "ketersediaan" in sp else False
sp["latest_rejection_status"] = sp["nim"].map(latest_rejection_by_nim)


def sync_bucket(row):
    if not row["is_synced"]:
        return "Belum Sync"
    if pd.isna(row["last_activity_date"]):
        # Never appeared in tracking_student — nothing to compare sync_date
        # against, so freshness can't be assessed for this student.
        return "Belum Ditrack"
    gap = row["activity_gap_days"]
    if gap <= 0:
        # sync_date is at/after their last tracking activity — profile was
        # (re)synced no earlier than the moment it was actually used. Good.
        return "Sync Setelah Aktivitas"
    if gap <= STALE_DAYS:
        return f"Selaras (<= {STALE_WEEKS} minggu)"
    return f"Stale (> {STALE_WEEKS} minggu)"


sp["sync_bucket"] = sp.apply(sync_bucket, axis=1)

# Buckets considered "in sync" for KPI / funnel purposes.
GOOD_SYNC_BUCKETS = {"Sync Setelah Aktivitas", f"Selaras (<= {STALE_WEEKS} minggu)"}

PRODI_OPTIONS = sorted(s for s in sp["program_studi"].dropna().unique())
POSITION_OPTIONS = sorted(s for s in tr["nama_posisi"].dropna().unique())
WORKING_ARR_OPTIONS = sorted(s for s in tr["working_arrangement"].dropna().unique()) if "working_arrangement" in tr else []
COMPANY_OPTIONS = sorted(s for s in company["company_name"].dropna().unique()) if "company_name" in company else []
SEMESTER_OPTIONS = sorted(int(s) for s in sp["semester"].dropna().unique())
DOMISILI_OPTIONS = sorted(s for s in sp["domisili"].dropna().unique()) if "domisili" in sp else []

TOOLS_OPTIONS = []
if "tools" in sp.columns:
    tool_tokens = set()
    for raw in sp["tools"].dropna().astype(str):
        for token in re.split(r"\s*[;,/]\s*|\band\b|&", raw.lower()):
            token = token.strip()
            if token:
                tool_tokens.add(token)
    TOOLS_OPTIONS = sorted(tool_tokens)

_ipk_valid = pd.to_numeric(sp["ipk"], errors="coerce").dropna()
IPK_MIN = float(_ipk_valid.min()) if len(_ipk_valid) else 2.0
IPK_MAX = float(_ipk_valid.max()) if len(_ipk_valid) else 4.0


def empty_fig(height=240, message="No data for this filter"):
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=COLORS["muted"], size=12))
    return fig


def filter_students(prodi, position, arr, semester, domisili, ipk_range, tool_search):
    d = sp.copy()
    if prodi:
        d = d[d["program_studi"] == prodi]
    if semester:
        d = d[d["semester"] >= semester]
    if domisili:
        d = d[d["domisili"] == domisili]
    if ipk_range:
        ipk_num = pd.to_numeric(d["ipk"], errors="coerce")
        d = d[ipk_num.between(ipk_range[0], ipk_range[1])]
    if tool_search:
        selected_tools = [str(t).strip().lower() for t in tool_search if str(t).strip()]
        if selected_tools:
            d = d[d["tools"].astype(str).str.lower().apply(
                lambda text: all(tool in text for tool in selected_tools)
            )]

    req = None
    reqs = tr.copy()
    if position:
        reqs = reqs[reqs["nama_posisi"] == position]
    if arr and "working_arrangement" in reqs.columns:
        reqs = reqs[reqs["working_arrangement"] == arr]
    if len(reqs):
        req = reqs.sort_values("request_date", ascending=False).iloc[0]
    return d, req


def match_score(row, req):
    if req is None:
        return None
    score = 0.0
    bidang = req.get("bidang_studi_dibutuhkan")
    if pd.notna(bidang) and str(row.get("program_studi")).strip().lower() == str(bidang).strip().lower():
        score += 30
    min_sem = req.get("minimum_semester")
    if pd.notna(min_sem) and pd.notna(row.get("semester")) and row["semester"] >= min_sem:
        score += 20
    ipk = pd.to_numeric(row.get("ipk"), errors="coerce")
    if pd.notna(ipk):
        score += min(ipk / 4.0, 1.0) * 20
    kota = req.get("kota")
    if pd.notna(kota) and pd.notna(row.get("domisili")) and str(kota).strip().lower() in str(row["domisili"]).strip().lower():
        score += 15
    ketersediaan = str(row.get("ketersediaan", "")).lower()
    if any(k in ketersediaan for k in ["siap", "tersedia", "available", "ready"]):
        score += 10
    tools_req = str(req.get("deskripsi_requirement", "")).lower()
    tools_student = str(row.get("tools", "")).lower()
    if tools_req and tools_student:
        req_words = {w.strip(",.") for w in tools_req.split() if len(w) > 2}
        stu_words = {w.strip(",.") for w in tools_student.replace(",", " ").split() if len(w) > 2}
        overlap = req_words & stu_words
        if overlap:
            score += min(len(overlap), 5)
    return round(score, 1)


TABLE_COLUMNS = [
    {"name": "Student ID", "id": "nim"},
    {"name": "Name", "id": "nama_status"},
    {"name": "Study Program", "id": "program_studi"},
    {"name": "Semester", "id": "semester"},
    {"name": "GPA", "id": "ipk"},
    {"name": "Location", "id": "domisili"},
    {"name": "Tools", "id": "tools"},
]
TABLE_FIELDS = ["nim", "nama_status", "program_studi", "semester", "ipk", "domisili", "tools"]


def build_match_table(dt, selected_ids=None, sent_nims=None):
    """Build the Ranked Candidate Matches table with a left-hand checkbox
    column (row_selectable). Candidates already sent to the currently
    selected target company are dropped from the list entirely — once
    sent, they're off the queue. selected_ids / sent_nims are lists of
    NIM strings, kept in dcc.Store so they survive the table being
    rebuilt whenever filters change."""
    selected_ids = selected_ids or []
    sent_nims = set(sent_nims or [])

    dt = dt[~dt["nim"].isin(sent_nims)] if len(dt) else dt
    records = dt[TABLE_FIELDS].fillna("-").to_dict("records")
    for rec in records:
        # "id" here is the row_id dash_table uses for selected_row_ids —
        # it doesn't need to be a visible column, just present in the dict.
        rec["id"] = rec["nim"]

    return dash_table.DataTable(
        id="tm-match-datatable",
        columns=TABLE_COLUMNS,
        data=records,
        row_selectable="multi",
        selected_row_ids=[i for i in selected_ids if i in {r["nim"] for r in records}],
        style_as_list_view=True,
        sort_action="native",
        page_action="native",
        page_size=15,
        style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                      "borderBottom": f"1px solid {COLORS['border']}"},
        style_cell={"fontSize": "11px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
    )


ipk_lo, ipk_hi = round(IPK_MIN, 1), round(IPK_MAX, 1)
ipk_marks = {
    round(v, 1): {"label": f"{v:.1f}", "style": {"fontSize": "10px", "color": COLORS["muted"]}}
    for v in [ipk_lo + i * 0.5 for i in range(int((ipk_hi - ipk_lo) / 0.5) + 1)]
} or {ipk_lo: str(ipk_lo), ipk_hi: str(ipk_hi)}
ipk_marks[ipk_lo] = {"label": f"{ipk_lo:.1f}", "style": {"fontSize": "10px", "color": COLORS["muted"]}}
ipk_marks[ipk_hi] = {"label": f"{ipk_hi:.1f}", "style": {"fontSize": "10px", "color": COLORS["muted"]}}

ipk_slider = html.Div([
    html.Div([
        html.Span("GPA Range", style={"fontSize": "9.5px", "fontWeight": "700", "color": COLORS["muted"],
                                         "textTransform": "uppercase", "letterSpacing": "0.05em"}),
        html.Span(id="tm-ipk-value-label", style={"fontSize": "11px", "fontWeight": "600",
                                                    "color": COLORS["primary_dark"]}),
    ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "10px"}),
    dcc.RangeSlider(
        id="tm-filter-ipk",
        min=ipk_lo, max=ipk_hi, step=0.05,
        value=[ipk_lo, ipk_hi],
        marks=ipk_marks,
        allowCross=False,
        tooltip={"placement": "top", "always_visible": False},
    ),
], style={
    "background": COLORS["surface"], "border": f"1px solid {COLORS['border_soft']}",
    "borderRadius": "9px", "padding": "8px 12px 6px 12px", "minWidth": "280px",
})

filter_bar = html.Div([
    filter_control("Study Program", dcc.Dropdown(
        id="tm-filter-prodi",
        options=[{"label": s, "value": s} for s in PRODI_OPTIONS],
        placeholder="All programs", clearable=True, style={"minWidth": "160px", "border": "none"},
    ), min_width="180px"),
    filter_control("Position", dcc.Dropdown(
        id="tm-filter-position",
        options=[{"label": s, "value": s} for s in POSITION_OPTIONS],
        placeholder="Select target position", clearable=True, style={"minWidth": "170px", "border": "none"},
    ), min_width="190px"),
    filter_control("Work Type", dcc.Dropdown(
        id="tm-filter-arr",
        options=[{"label": s, "value": s} for s in WORKING_ARR_OPTIONS],
        placeholder="All types", clearable=True, style={"minWidth": "140px", "border": "none"},
    ), min_width="160px"),
    filter_control("Min Semester", dcc.Dropdown(
        id="tm-filter-semester",
        options=[{"label": str(s), "value": s} for s in SEMESTER_OPTIONS],
        placeholder="All semesters", clearable=True, style={"minWidth": "130px", "border": "none"},
    ), min_width="150px"),
    filter_control("Location", dcc.Dropdown(
        id="tm-filter-domisili",
        options=[{"label": s, "value": s} for s in DOMISILI_OPTIONS],
        placeholder="All locations", clearable=True, style={"minWidth": "150px", "border": "none"},
    ), min_width="170px"),
    filter_control("Tools / Skills", dcc.Dropdown(
        id="tm-filter-tools",
        options=[{"label": s.title(), "value": s} for s in TOOLS_OPTIONS],
        placeholder="Search tools or skills",
        multi=True,
        searchable=True,
        clearable=True,
        style={"minWidth": "200px", "border": "none", "background": "transparent"},
    ), min_width="260px"),
    ipk_slider,
], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["sm"], "flexWrap": "wrap", "alignItems": "flex-start"})

export_button = html.Button(
    "Export PDF",
    id="tm-export-pdf-btn",
    n_clicks=0,
    style={
        "background": COLORS["primary"],
        "color": "#FFFFFF",
        "border": "none",
        "borderRadius": "8px",
        "padding": "10px 16px",
        "fontSize": "13px",
        "fontWeight": "600",
        "cursor": "pointer",
    },
)

layout = html.Div([
    page_header("Talent Matching",
                "Find best-fit candidates with current, complete profiles", export_button),
    html.Div(id="tm-export-pdf-dummy", style={"display": "none"}),
    filter_bar,
    html.Div(id="tm-kpi-row", style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["sm"], "flexWrap": "wrap"}),

    html.Div([
        section_card(
            "Ranked Candidate Matches",
            "Eligible, available candidates only — select, choose a company, then send",
            html.Div([
                html.Div([
                    dcc.Dropdown(
                        id="tm-send-company",
                        options=[{"label": c, "value": c} for c in COMPANY_OPTIONS],
                        placeholder="Select company",
                        clearable=True,
                        style={"minWidth": "260px"},
                    ),
                    html.Button("Send to Company", id="tm-send-btn", n_clicks=0, style={
                        "background": COLORS["primary_dark"], "color": "#fff", "border": "none",
                        "borderRadius": "8px", "padding": "8px 16px", "fontSize": "12px",
                        "fontWeight": "600", "cursor": "pointer",
                    }),
                    html.Div(id="tm-send-feedback", style={"fontSize": "11px", "color": COLORS["muted"],
                                                            "alignSelf": "center"}),
                ], style={"display": "flex", "gap": SPACE["xs"], "alignItems": "center", "marginBottom": SPACE["xs"],
                          "flexWrap": "wrap"}),
                html.Div(id="tm-match-table", style={"maxHeight": "460px", "overflowY": "auto"}),
                dcc.Store(id="tm-selected-store", data=[]),
                dcc.Store(id="tm-sent-store", data=[]),
            ]),
            style_extra={"flex": "1"}),
    ], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["xs"]}),

    # Supporting analysis: pool health at a glance.
    html.Div([
        section_card("Document Completeness", "CV and portfolio submission status",
                     dcc.Graph(id="tm-doc-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card("Tools & Skills Coverage", "Most common skills in the candidate pool",
                     dcc.Graph(id="tm-sync-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": SPACE["xs"], "marginBottom": SPACE["xs"]}),

    html.Div([
        section_card("GPA Distribution", "Spread of student GPAs in the filtered pool",
                     dcc.Graph(id="tm-ipk-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card("Talent Pool Funnel", "Candidate drop-off from active to ready-to-send",
                     dcc.Graph(id="tm-domisili-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": SPACE["xs"]}),
], style=PAGE_STYLE)


dash.clientside_callback(
    "function(n_clicks) { if (n_clicks) { window.print(); } return ''; }",
    Output("tm-export-pdf-dummy", "children"),
    Input("tm-export-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("tm-ipk-value-label", "children"),
    Input("tm-filter-ipk", "value"),
)
def update_ipk_label(ipk_range):
    if not ipk_range:
        return ""
    return f"{ipk_range[0]:.2f} – {ipk_range[1]:.2f}"


@callback(
    Output("tm-kpi-row", "children"),
    Output("tm-match-table", "children"),
    Output("tm-doc-graph", "figure"),
    Output("tm-sync-graph", "figure"),
    Output("tm-ipk-graph", "figure"),
    Output("tm-domisili-graph", "figure"),
    Input("tm-filter-prodi", "value"),
    Input("tm-filter-position", "value"),
    Input("tm-filter-arr", "value"),
    Input("tm-filter-semester", "value"),
    Input("tm-filter-domisili", "value"),
    Input("tm-filter-tools", "value"),
    Input("tm-filter-ipk", "value"),
    Input("tm-sent-store", "data"),
    Input("tm-send-company", "value"),
    State("tm-selected-store", "data"),
)
def update_matching(prodi, position, arr, semester, domisili, tool_search, ipk_range,
                     sent_records, send_company, selected_ids):
    sent_records = sent_records or []
    if send_company:

        sent_records_nims = [r["nim"] for r in sent_records if r.get("company") == send_company]
    else:
        sent_records_nims = [r["nim"] for r in sent_records]
    d, req = filter_students(prodi, position, arr, semester, domisili, ipk_range, tool_search)

    available = int(d["is_eligible"].sum())
    complete_pct = round(100 * d["doc_complete"].mean(), 1) if len(d) else 0
    synced_pct = round(100 * d["sync_bucket"].isin(GOOD_SYNC_BUCKETS).mean(), 1) if len(d) else 0

    kpi_row = [
        kpi_card("Available Students", f"{available}", "Active, documents complete, GPA on file"),
        kpi_card("Documents Complete", f"{complete_pct}%", "CV and portfolio submitted"),
        kpi_card("Sync Status", f"{synced_pct}%",
                 f"Profile synced within {STALE_WEEKS} weeks of last activity",
                 color=COLORS["danger"] if synced_pct < 70 else COLORS["success"],
                 accent=COLORS["danger"] if synced_pct < 70 else COLORS["success"]),
    ]
    if req is not None:
        d = d.copy()
        d["match_score"] = d.apply(lambda r: match_score(r, req), axis=1)
        avg_score = round(d.loc[d["is_eligible"], "match_score"].mean(), 1) if d["is_eligible"].any() else None
        kpi_row.append(kpi_card("Avg. Match Score", f"{avg_score}" if avg_score is not None else "-",
                                 f"Matched against {req.get('nama_posisi', '-')}"))

    if req is not None and len(d):
        dt = d.copy()

        dt = dt[dt["is_eligible"] & dt["is_available"]]

        dt = dt.sort_values("match_score", ascending=False)
        if len(dt):
            match_table = build_match_table(dt, selected_ids, sent_records_nims)
        else:
            match_table = html.Div("No eligible, available candidates for this filter.",
                                    style={"fontSize": "12px", "color": COLORS["muted"]})
    else:
        dt = d[d["is_eligible"] & d["is_available"]].sort_values("ipk", ascending=False) if len(d) else d
        if len(dt):
            match_table = build_match_table(dt, selected_ids, sent_records_nims)
        else:
            match_table = html.Div("Select a position to see match scores, or broaden your filters.",
                                    style={"fontSize": "12px", "color": COLORS["muted"]})

    if len(d):
        doc_counts = d["doc_complete"].map({True: "Complete", False: "Incomplete"}).value_counts()
        doc_fig = go.Figure(go.Pie(
            labels=doc_counts.index, values=doc_counts.values, hole=0.55,
            marker=dict(colors=[COLORS["primary_dark"], CATEGORICAL[0]]),
        ))
        doc_fig.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=True,
                               legend=dict(orientation="h", y=-0.2, font=dict(size=9)))
    else:
        doc_fig = empty_fig()

    if len(d) and "tools" in d.columns and d["tools"].notna().any():
        tool_counts = {}
        for raw in d["tools"].dropna().astype(str):
            for token in re.split(r"\s*[;,/]\s*|\band\b|&", raw.lower()):
                token = token.strip()
                if token:
                    tool_counts[token] = tool_counts.get(token, 0) + 1
        if tool_counts:
            tool_series = pd.Series(tool_counts).sort_values(ascending=True).tail(10)
            sync_fig = go.Figure(go.Bar(
                x=tool_series.values, y=[t.title() for t in tool_series.index], orientation="h",
                marker_color=COLORS["primary"],
            ))
            sync_fig.update_layout(**PLOTLY_LAYOUT, height=240, xaxis_title="Number of Students")
        else:
            sync_fig = empty_fig(240, "No tools data available")
    else:
        sync_fig = empty_fig(240, "Tools data unavailable for this filter")

    ipk_numeric = pd.to_numeric(d["ipk"], errors="coerce").dropna() if len(d) else pd.Series(dtype=float)
    if len(ipk_numeric):
        ipk_fig = go.Figure(go.Histogram(x=ipk_numeric, nbinsx=20, marker_color=COLORS["primary"]))
        if ipk_range:
            ipk_fig.add_vline(x=ipk_range[0], line_dash="dot", line_color=COLORS["primary_dark"])
        ipk_fig.update_layout(**PLOTLY_LAYOUT, height=240, xaxis_title="GPA", yaxis_title="Number of Students")
    else:
        ipk_fig = empty_fig()

    if len(d):
        n_total = len(d)
        n_active = int(d["is_active"].sum())
        n_doc = int((d["is_active"] & d["doc_complete"]).sum())
        n_eligible = int(d["is_eligible"].sum())
        n_ready = int((d["is_eligible"] & d["sync_bucket"].isin(GOOD_SYNC_BUCKETS)).sum())

        funnel_fig = go.Figure(go.Funnel(
            y=["Total Candidates", "Active", "Documents Complete", "Eligible", "Ready to Send"],
            x=[n_total, n_active, n_doc, n_eligible, n_ready],
            textinfo="value+percent initial",
            marker=dict(color=[CATEGORICAL[0], COLORS["primary_soft"], COLORS["primary"],
                                COLORS["primary_dark"], COLORS["success"]]),
        ))
        funnel_fig.update_layout(**PLOTLY_LAYOUT, height=240)
        dom_fig = funnel_fig
    else:
        dom_fig = empty_fig(240, "No data for this filter")

    return kpi_row, match_table, doc_fig, sync_fig, ipk_fig, dom_fig


@callback(
    Output("tm-selected-store", "data", allow_duplicate=True),
    Input("tm-match-datatable", "selected_row_ids"),
    prevent_initial_call=True,
)
def sync_selected_candidates(selected_row_ids):
    return selected_row_ids or []


@callback(
    Output("tm-sent-store", "data"),
    Output("tm-send-feedback", "children"),
    Output("tm-selected-store", "data", allow_duplicate=True),
    Input("tm-send-btn", "n_clicks"),
    State("tm-selected-store", "data"),
    State("tm-send-company", "value"),
    State("tm-sent-store", "data"),
    prevent_initial_call=True,
)
def mock_send_to_company(n_clicks, selected_ids, company_name, sent_records):
    sent_records = list(sent_records or [])
    if not company_name:
        return dash.no_update, "Select a target company first.", dash.no_update
    if not selected_ids:
        return dash.no_update, "Select at least one candidate to send.", dash.no_update

    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    for nim in selected_ids:
        sent_records.append({"nim": nim, "company": company_name, "sent_at": now})

    feedback = f"{len(selected_ids)} candidate(s) sent to {company_name}."
    return sent_records, feedback, []