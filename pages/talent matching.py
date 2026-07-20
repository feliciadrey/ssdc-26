import dash
from dash import html, dcc, dash_table, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT
from utils.components import kpi_card, section_card, page_header, filter_control

dash.register_page(__name__, path="/talent-matching", name="Talent Matching")

TODAY = pd.Timestamp(datetime(2026, 7, 18))

# ----------------------------------------------------------------------------
# Data prep
# ----------------------------------------------------------------------------
data = load_all()
student_all = data["student_all"].copy()
status_student = data["status_student"].copy()
talent_request = data["talent_request"].copy()
company = data["company"].copy()

# Defensive: normalize column names in case the source CSVs use different
# casing (e.g. "NIM" vs "nim") than the lowercase names used throughout
# this app's data_loader / other pages.
for _df in (student_all, status_student, talent_request, company):
    _df.columns = _df.columns.str.strip().str.lower()

# Bring company kota onto talent_request so we can compare domisili mahasiswa
# vs kota perusahaan (fallback to nama_perusahaan join since id_company may
# not always be populated consistently in the source form).
company_lookup = company.rename(columns={"company_name": "nama_perusahaan"})[
    ["nama_perusahaan", "kota"]
].drop_duplicates(subset="nama_perusahaan")
tr = talent_request.merge(company_lookup, on="nama_perusahaan", how="left")

# ---- Unified student profile ------------------------------------------------
# student_all is the full student universe; status_student is the
# self-reported / synced snapshot (semester, ipk, domisili, tools, docs, ...).
# We left-join so students who exist but haven't synced yet still show up
# (and can be flagged as "Belum Sync").
sp = student_all.merge(
    status_student, on="nim", how="left", suffixes=("_all", "_status")
)

sp["program_studi"] = sp["program_studi_status"].fillna(sp["program_studi_all"])
sp["semester"] = pd.to_numeric(sp["semester_status"], errors="coerce").fillna(
    pd.to_numeric(sp["semester_all"], errors="coerce")
)
sp["is_synced"] = sp["sync_date"].notna()

# Reference "now" for freshness = the most recent sync_date actually present
# in the dataset, not the real-world clock. A static/historical snapshot can
# have every sync_date far in the past relative to today's date, which would
# make every row look "Outdated" regardless of how fresh it really was
# relative to the rest of the batch.
_valid_sync = sp["sync_date"].dropna()
REF_SYNC_DATE = _valid_sync.max() if len(_valid_sync) else TODAY
sp["days_since_sync"] = (REF_SYNC_DATE - sp["sync_date"]).dt.days

# cv / portofolio are status strings ("Ada" / "Tidak Ada"), not file paths —
# per dataset docs (Sec. 5.4). A non-empty "Tidak Ada" is NOT complete.
sp["doc_complete"] = (
    sp["cv"].astype(str).str.strip().str.lower().eq("ada")
    & sp["portofolio"].astype(str).str.strip().str.lower().eq("ada")
)

# status values are "Active", "Inactive", "Cuti", "Lulus" per dataset docs
# (Sec. 5.4) — not the Indonesian "Aktif".
sp["is_active"] = sp["status"].astype(str).str.strip().str.lower().eq("active")
sp["is_eligible"] = sp["is_active"] & sp["doc_complete"] & sp["ipk"].notna()


def sync_bucket(row):
    if not row["is_synced"]:
        return "Belum Sync"
    if row["days_since_sync"] <= 7:
        return "Up to Date"
    if row["days_since_sync"] <= 30:
        return "Perlu Update"
    return "Outdated"


sp["sync_bucket"] = sp.apply(sync_bucket, axis=1)

PRODI_OPTIONS = sorted(s for s in sp["program_studi"].dropna().unique())
POSITION_OPTIONS = sorted(s for s in tr["nama_posisi"].dropna().unique())
WORKING_ARR_OPTIONS = sorted(s for s in tr["working_arrangement"].dropna().unique()) if "working_arrangement" in tr else []
SEMESTER_OPTIONS = sorted(int(s) for s in sp["semester"].dropna().unique())
DOMISILI_OPTIONS = sorted(s for s in sp["domisili"].dropna().unique()) if "domisili" in sp else []

_ipk_valid = pd.to_numeric(sp["ipk"], errors="coerce").dropna()
IPK_MIN = float(_ipk_valid.min()) if len(_ipk_valid) else 2.0
IPK_MAX = float(_ipk_valid.max()) if len(_ipk_valid) else 4.0


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def empty_fig(height=240, message="Tidak ada data untuk filter ini"):
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=COLORS["muted"], size=12))
    return fig


def filter_students(prodi, position, arr, semester, domisili, ipk_range):
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
    """Weighted match score (0-100) of a student against a target request.
    Weights: prodi 30, semester 20, IPK 20, domisili vs kota perusahaan 15,
    ketersediaan 10, tools overlap up to 5."""
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


# ----------------------------------------------------------------------------
# Static shell
# ----------------------------------------------------------------------------
filter_bar = html.Div([
    filter_control("Program Studi", dcc.Dropdown(
        id="tm-filter-prodi",
        options=[{"label": s, "value": s} for s in PRODI_OPTIONS],
        placeholder="Semua prodi", clearable=True, style={"minWidth": "160px", "border": "none"},
    ), min_width="180px"),
    filter_control("Position", dcc.Dropdown(
        id="tm-filter-position",
        options=[{"label": s, "value": s} for s in POSITION_OPTIONS],
        placeholder="Pilih posisi target", clearable=True, style={"minWidth": "170px", "border": "none"},
    ), min_width="190px"),
    filter_control("Working Arr.", dcc.Dropdown(
        id="tm-filter-arr",
        options=[{"label": s, "value": s} for s in WORKING_ARR_OPTIONS],
        placeholder="Semua tipe", clearable=True, style={"minWidth": "140px", "border": "none"},
    ), min_width="160px"),
    filter_control("Semester (min)", dcc.Dropdown(
        id="tm-filter-semester",
        options=[{"label": str(s), "value": s} for s in SEMESTER_OPTIONS],
        placeholder="Semua semester", clearable=True, style={"minWidth": "130px", "border": "none"},
    ), min_width="150px"),
    filter_control("Domisili", dcc.Dropdown(
        id="tm-filter-domisili",
        options=[{"label": s, "value": s} for s in DOMISILI_OPTIONS],
        placeholder="Semua domisili", clearable=True, style={"minWidth": "150px", "border": "none"},
    ), min_width="170px"),
    filter_control("Slider IPK", dcc.RangeSlider(
        id="tm-filter-ipk",
        min=round(IPK_MIN, 1), max=round(IPK_MAX, 1), step=0.05,
        value=[round(IPK_MIN, 1), round(IPK_MAX, 1)],
        marks=None, tooltip={"placement": "bottom", "always_visible": False},
    ), min_width="220px"),
], style={"display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap"})

layout = html.Div([
    page_header("Talent Matching Management",
                "Cari kandidat paling sesuai kebutuhan perusahaan & pastikan data mahasiswa sinkron"),
    filter_bar,
    html.Div(id="tm-kpi-row", style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),

    # Row 1: Ranked candidate matches
    html.Div([
        section_card("Ranked Candidate Matches", "Skor = prodi + semester + IPK + domisili + ketersediaan + tools",
                     html.Div(id="tm-match-table"),
                     style_extra={"flex": "1"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),

    # Row 2: Document completeness / Sync freshness / Ketersediaan
    html.Div([
        section_card("Document Completeness", "CV + portofolio lengkap vs kurang",
                     dcc.Graph(id="tm-doc-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Sync Freshness", "STUDENT ALL vs STATUS STUDENT (sync_date)",
                     dcc.Graph(id="tm-sync-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Ketersediaan", "Status kesiapan mahasiswa",
                     dcc.Graph(id="tm-ketersediaan-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),

    # Row 3: IPK distribution / Domisili distribution
    html.Div([
        section_card("IPK Distribution", "Sebaran IPK pool mahasiswa hasil filter",
                     dcc.Graph(id="tm-ipk-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
        section_card("Domisili Distribution", "Top domisili kandidat eligible",
                     dcc.Graph(id="tm-domisili-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "6"}),
    ], style={"display": "flex", "gap": "12px"}),
], style={"padding": "24px", "background": COLORS["bg"], "minHeight": "100vh"})


# ----------------------------------------------------------------------------
# Main callback
# ----------------------------------------------------------------------------
@callback(
    Output("tm-kpi-row", "children"),
    Output("tm-match-table", "children"),
    Output("tm-doc-graph", "figure"),
    Output("tm-sync-graph", "figure"),
    Output("tm-ketersediaan-graph", "figure"),
    Output("tm-ipk-graph", "figure"),
    Output("tm-domisili-graph", "figure"),
    Input("tm-filter-prodi", "value"),
    Input("tm-filter-position", "value"),
    Input("tm-filter-arr", "value"),
    Input("tm-filter-semester", "value"),
    Input("tm-filter-domisili", "value"),
    Input("tm-filter-ipk", "value"),
)
def update_matching(prodi, position, arr, semester, domisili, ipk_range):
    d, req = filter_students(prodi, position, arr, semester, domisili, ipk_range)

    # ---- KPIs ----
    available = int(d["is_eligible"].sum())
    complete_pct = round(100 * d["doc_complete"].mean(), 1) if len(d) else 0
    synced_pct = round(100 * (d["sync_bucket"] == "Up to Date").mean(), 1) if len(d) else 0

    kpi_row = [
        kpi_card("Available Students", f"{available}", "Aktif, dokumen lengkap, IPK terisi"),
        kpi_card("% Complete Documents", f"{complete_pct}%", "CV + portofolio terisi"),
        kpi_card("Sync Status", f"{synced_pct}%",
                 "Up to date (<= 7 hari sejak sync_date)",
                 color=COLORS["danger"] if synced_pct < 70 else COLORS["success"],
                 accent=COLORS["danger"] if synced_pct < 70 else COLORS["success"]),
    ]
    if req is not None:
        d = d.copy()
        d["match_score"] = d.apply(lambda r: match_score(r, req), axis=1)
        avg_score = round(d.loc[d["is_eligible"], "match_score"].mean(), 1) if d["is_eligible"].any() else None
        kpi_row.append(kpi_card("Avg Match Score", f"{avg_score}" if avg_score is not None else "-",
                                 f"vs posisi: {req.get('nama_posisi', '-')}"))

    # ---- Ranked candidate match table ----
    if req is not None and len(d):
        dt = d.copy()
        dt = dt[dt["is_eligible"]]
        dt = dt.sort_values("match_score", ascending=False).head(15)
        if len(dt):
            match_table = dash_table.DataTable(
                columns=[
                    {"name": "NIM", "id": "nim"},
                    {"name": "Nama", "id": "nama_status"},
                    {"name": "Prodi", "id": "program_studi"},
                    {"name": "Semester", "id": "semester"},
                    {"name": "IPK", "id": "ipk"},
                    {"name": "Domisili", "id": "domisili"},
                    {"name": "Ketersediaan", "id": "ketersediaan"},
                    {"name": "Match Score", "id": "match_score"},
                ],
                data=dt[["nim", "nama_status", "program_studi", "semester", "ipk",
                         "domisili", "ketersediaan", "match_score"]].fillna("-").to_dict("records"),
                style_as_list_view=True,
                style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                              "borderBottom": f"1px solid {COLORS['border']}"},
                style_cell={"fontSize": "11px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
                style_data_conditional=[
                    {"if": {"filter_query": "{match_score} >= 70"}, "backgroundColor": COLORS["success_bg"]},
                    {"if": {"filter_query": "{match_score} < 40"}, "backgroundColor": COLORS["warning_bg"]},
                ],
            )
        else:
            match_table = html.Div("Tidak ada kandidat eligible untuk filter ini.",
                                    style={"fontSize": "12px", "color": COLORS["muted"]})
    else:
        # No target position selected: show top eligible students by IPK instead.
        dt = d[d["is_eligible"]].sort_values("ipk", ascending=False).head(15)
        if len(dt):
            match_table = dash_table.DataTable(
                columns=[
                    {"name": "NIM", "id": "nim"},
                    {"name": "Nama", "id": "nama_status"},
                    {"name": "Prodi", "id": "program_studi"},
                    {"name": "Semester", "id": "semester"},
                    {"name": "IPK", "id": "ipk"},
                    {"name": "Domisili", "id": "domisili"},
                    {"name": "Ketersediaan", "id": "ketersediaan"},
                ],
                data=dt[["nim", "nama_status", "program_studi", "semester", "ipk",
                         "domisili", "ketersediaan"]].fillna("-").to_dict("records"),
                style_as_list_view=True,
                style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                              "borderBottom": f"1px solid {COLORS['border']}"},
                style_cell={"fontSize": "11px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
            )
        else:
            match_table = html.Div("Pilih Position untuk melihat skor kecocokan, atau tidak ada data untuk filter ini.",
                                    style={"fontSize": "12px", "color": COLORS["muted"]})

    # ---- Document completeness donut ----
    if len(d):
        doc_counts = d["doc_complete"].map({True: "Lengkap", False: "Kurang Lengkap"}).value_counts()
        doc_fig = go.Figure(go.Pie(
            labels=doc_counts.index, values=doc_counts.values, hole=0.55,
            marker=dict(colors=[COLORS["primary_dark"], CATEGORICAL[0]]),
        ))
        doc_fig.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=True,
                               legend=dict(orientation="h", y=-0.2, font=dict(size=9)))
    else:
        doc_fig = empty_fig()

    # ---- Sync freshness ----
    if len(d):
        sync_counts = d["sync_bucket"].value_counts()
        order = ["Up to Date", "Perlu Update", "Outdated", "Belum Sync"]
        sync_counts = sync_counts.reindex(order).dropna()
        sync_colors = {"Up to Date": COLORS["success"], "Perlu Update": COLORS["primary_soft"],
                       "Outdated": COLORS["primary_dark"], "Belum Sync": CATEGORICAL[0]}
        sync_fig = go.Figure(go.Bar(
            x=sync_counts.index, y=sync_counts.values,
            marker_color=[sync_colors.get(s, CATEGORICAL[0]) for s in sync_counts.index],
        ))
        sync_fig.update_layout(**PLOTLY_LAYOUT, height=240, yaxis_title="Jumlah mahasiswa")
    else:
        sync_fig = empty_fig()

    # ---- Ketersediaan ----
    if len(d) and "ketersediaan" in d.columns and d["ketersediaan"].notna().any():
        ket_counts = d["ketersediaan"].value_counts()
        ket_fig = go.Figure(go.Bar(
            x=ket_counts.values, y=ket_counts.index, orientation="h",
            marker_color=CATEGORICAL[0],
        ))
        ket_fig.update_layout(**PLOTLY_LAYOUT, height=240, xaxis_title="Jumlah mahasiswa")
    else:
        ket_fig = empty_fig(240, "Kolom ketersediaan tidak tersedia / kosong")

    # ---- IPK distribution ----
    ipk_numeric = pd.to_numeric(d["ipk"], errors="coerce").dropna() if len(d) else pd.Series(dtype=float)
    if len(ipk_numeric):
        ipk_fig = go.Figure(go.Histogram(x=ipk_numeric, nbinsx=20, marker_color=COLORS["primary"]))
        if ipk_range:
            ipk_fig.add_vline(x=ipk_range[0], line_dash="dot", line_color=COLORS["primary_dark"])
        ipk_fig.update_layout(**PLOTLY_LAYOUT, height=240, xaxis_title="IPK", yaxis_title="Jumlah mahasiswa")
    else:
        ipk_fig = empty_fig()

    # ---- Domisili distribution (eligible pool) ----
    dom_pool = d[d["is_eligible"]] if len(d) else d
    if len(dom_pool) and "domisili" in dom_pool.columns and dom_pool["domisili"].notna().any():
        dom_counts = dom_pool["domisili"].value_counts().sort_values(ascending=True).tail(10)
        dom_fig = go.Figure(go.Bar(
            x=dom_counts.values, y=dom_counts.index, orientation="h",
            marker_color=COLORS["primary_soft"],
        ))
        dom_fig.update_layout(**PLOTLY_LAYOUT, height=240, xaxis_title="Jumlah mahasiswa eligible")
    else:
        dom_fig = empty_fig(240, "Kolom domisili tidak tersedia / kosong")

    return kpi_row, match_table, doc_fig, sync_fig, ket_fig, ipk_fig, dom_fig