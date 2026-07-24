import dash
from dash import html, dcc, dash_table, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import load_all
from utils.theme import COLORS, CATEGORICAL, PLOTLY_LAYOUT
from utils.components import kpi_card, section_card, page_header, filter_control

dash.register_page(__name__, path="/", name="Executive Summary")

data = load_all()
tracking_company = data["tracking_company"].copy()
tracking_student = data["tracking_student"].copy()
student_all = data["student_all"].copy()
company = data["company"].copy()

company_lookup = (
    company.rename(columns={"company_name": "nama_perusahaan"})[
        ["nama_perusahaan", "industry_sector", "kota"]
    ]
    .drop_duplicates(subset="nama_perusahaan")
)
tc = tracking_company.merge(company_lookup, on="nama_perusahaan", how="left")


def semester_label(d):
    if pd.isna(d):
        return None
    if d.month >= 8:
        return f"Ganjil {d.year}/{d.year + 1}"
    return f"Genap {d.year - 1}/{d.year}"


tc["semester"] = tc["request_date"].apply(semester_label)

SEMESTER_OPTIONS = sorted(s for s in tc["semester"].dropna().unique())
SEKTOR_OPTIONS = sorted(s for s in tc["industry_sector"].dropna().unique())

_valid_dates = tc["request_date"].dropna()
MIN_DATE = _valid_dates.min().date() if len(_valid_dates) else pd.Timestamp("2024-01-01").date()
MAX_DATE = _valid_dates.max().date() if len(_valid_dates) else pd.Timestamp.today().date()

CITY_COORDS = {
    "jakarta": (-6.2088, 106.8456), "dki jakarta": (-6.2088, 106.8456),
    "jakarta selatan": (-6.2615, 106.8106), "jakarta pusat": (-6.1862, 106.8342),
    "jakarta barat": (-6.1352, 106.8133), "jakarta timur": (-6.2250, 106.9004),
    "jakarta utara": (-6.1214, 106.8783),
    "bandung": (-6.9175, 107.6191), "bekasi": (-6.2383, 106.9756),
    "tangerang": (-6.1783, 106.6319), "tangerang selatan": (-6.2884, 106.7180),
    "depok": (-6.4025, 106.7942), "bogor": (-6.5971, 106.8060),
    "surabaya": (-7.2575, 112.7521), "malang": (-7.9666, 112.6326),
    "sidoarjo": (-7.4478, 112.7183), "gresik": (-7.1560, 112.6531),
    "semarang": (-6.9932, 110.4203), "solo": (-7.5755, 110.8243),
    "surakarta": (-7.5755, 110.8243), "yogyakarta": (-7.7956, 110.3695),
    "sleman": (-7.7185, 110.3572), "medan": (3.5952, 98.6722),
    "palembang": (-2.9761, 104.7754), "makassar": (-5.1477, 119.4327),
    "denpasar": (-8.6705, 115.2126), "badung": (-8.5900, 115.1720),
    "balikpapan": (-1.2379, 116.8529), "samarinda": (-0.5022, 117.1536),
    "pekanbaru": (0.5071, 101.4478), "batam": (1.0456, 104.0305),
    "padang": (-0.9471, 100.4172), "banjarmasin": (-3.3186, 114.5944),
    "manado": (1.4748, 124.8421), "pontianak": (-0.0263, 109.3425),
    "jambi": (-1.6101, 103.6131), "bandar lampung": (-5.4292, 105.2610),
    "cirebon": (-6.7063, 108.5571), "cimahi": (-6.8841, 107.5420),
    "karawang": (-6.3227, 107.3376), "purwakarta": (-6.5569, 107.4436),
    "sukabumi": (-6.9250, 106.9271), "serang": (-6.1149, 106.1503),
    "cilegon": (-5.9877, 106.0669), "kudus": (-6.8048, 110.8405),
    "magelang": (-7.4797, 110.2177), "purwokerto": (-7.4218, 109.2340),
    "tasikmalaya": (-7.3274, 108.2207), "mataram": (-8.5833, 116.1167),
    "kupang": (-10.1772, 123.6070), "ambon": (-3.6954, 128.1814),
    "jayapura": (-2.5337, 140.7181), "palu": (-0.8917, 119.8707),
    "kendari": (-3.9450, 122.4989), "gorontalo": (0.5435, 123.0568),
    "bengkulu": (-3.7928, 102.2608), "pangkal pinang": (-2.1316, 106.1169),
    "tegal": (-6.8694, 109.1402), "pekalongan": (-6.8898, 109.6753),
}


def city_coord(name):
    if pd.isna(name):
        return None
    key = str(name).strip().lower()
    return CITY_COORDS.get(key)


def empty_fig(height=260, message="Tidak ada data untuk filter ini"):
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=COLORS["muted"], size=12))
    return fig


def filter_tc(semester, start_date, end_date, sektor):
    d = tc.copy()
    if semester:
        d = d[d["semester"] == semester]
    if start_date:
        d = d[d["request_date"] >= pd.Timestamp(start_date)]
    if end_date:
        d = d[d["request_date"] <= pd.Timestamp(end_date)]
    if sektor:
        d = d[d["industry_sector"] == sektor]
    return d


def matching_students(d):
    if not len(d):
        return tracking_student.iloc[0:0].copy()
    if "id_tracking_company" in d.columns and "id_tracking_company" in tracking_student.columns:
        ids = set(d["id_tracking_company"])
        return tracking_student[tracking_student["id_tracking_company"].isin(ids)].copy()
    # fallback for datasets missing the FK column - can over-match on recurring postings
    pairs = set(zip(d["nama_perusahaan"], d["posisi"]))
    mask = list(zip(tracking_student["company"], tracking_student["position"]))
    mask = [p in pairs for p in mask]
    return tracking_student[mask].copy()


filter_bar = html.Div([
    filter_control("Semester", dcc.Dropdown(
        id="ov-filter-semester",
        options=[{"label": s, "value": s} for s in SEMESTER_OPTIONS],
        placeholder="Semua semester",
        clearable=True,
        style={"minWidth": "180px", "border": "none"},
    )),
    filter_control("Date range", dcc.DatePickerRange(
        id="ov-filter-daterange",
        min_date_allowed=MIN_DATE,
        max_date_allowed=MAX_DATE,
        start_date=MIN_DATE,
        end_date=MAX_DATE,
        display_format="D MMM YYYY",
    ), min_width="240px"),
    filter_control("Sektor Perusahaan", dcc.Dropdown(
        id="ov-filter-sektor",
        options=[{"label": s, "value": s} for s in SEKTOR_OPTIONS],
        placeholder="Semua sektor",
        clearable=True,
        style={"minWidth": "200px", "border": "none"},
    )),
], style={"display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap", "alignItems": "flex-start"})

export_button = html.Button(
    "Export as PDF",
    id="ov-export-pdf-btn",
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
    page_header("Executive Summary", "Ringkasan Performa Placement · Seluruh Program Studi", export_button),
    html.Div(id="ov-export-pdf-dummy", style={"display": "none"}),
    filter_bar,
    html.Div(id="ov-kpi-row", style={"display": "flex", "gap": "12px", "marginBottom": "16px", "flexWrap": "wrap"}),

    html.Div([
        section_card("Trend: Placement vs Request", "Per bulan",
                     dcc.Graph(id="ov-trend-graph", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Placement by Jenis Penempatan", "Magang / Part-time / Full-time",
                     dcc.Graph(id="ov-jenis-pie", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Demografik placement by kota", "Ukuran titik = jumlah kandidat dikirim",
                     html.Div([
                         dcc.Graph(id="ov-kota-map", config={"displayModeBar": False}),
                         html.Div(id="ov-kota-caption", style={"fontSize": "10px", "color": COLORS["muted"],
                                                                "marginTop": "4px"}),
                     ]),
                     style_extra={"flex": "4"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),

    html.Div([
        section_card("Top recruiting companies", "Permintaan terbanyak",
                     dcc.Graph(id="ov-top-companies-bar", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Placement success rate", "Placed / dikirim, top 10",
                     dcc.Graph(id="ov-success-rate-bar", config={"displayModeBar": False}),
                     style_extra={"flex": "4"}),
        section_card("Placement by program studi", "Klik bar untuk detail mahasiswa",
                     html.Div([
                         dcc.Graph(id="ov-prodi-bar", config={"displayModeBar": False}),
                         html.Div(id="ov-prodi-detail",
                                   style={"marginTop": "8px", "maxHeight": "180px", "overflowY": "auto"}),
                     ]),
                     style_extra={"flex": "4"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
], style={"padding": "24px", "background": COLORS["bg"], "minHeight": "100vh"})


dash.clientside_callback(
    "function(n_clicks) { if (n_clicks) { window.print(); } return ''; }",
    Output("ov-export-pdf-dummy", "children"),
    Input("ov-export-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("ov-kpi-row", "children"),
    Output("ov-trend-graph", "figure"),
    Output("ov-jenis-pie", "figure"),
    Output("ov-kota-map", "figure"),
    Output("ov-kota-caption", "children"),
    Output("ov-top-companies-bar", "figure"),
    Output("ov-success-rate-bar", "figure"),
    Output("ov-prodi-bar", "figure"),
    Input("ov-filter-semester", "value"),
    Input("ov-filter-daterange", "start_date"),
    Input("ov-filter-daterange", "end_date"),
    Input("ov-filter-sektor", "value"),
)
def update_overview(semester, start_date, end_date, sektor):
    d = filter_tc(semester, start_date, end_date, sektor)
    ts = matching_students(d)

    total_requested = int(d["jumlah_permintaan"].sum()) if len(d) else 0
    total_placed = int((ts["progress_student"] == "Placement").sum())
    fulfillment_rate = min(round(100 * total_placed / total_requested, 1), 100.0) if total_requested else 0
    placement_rate = round(100 * total_placed / len(ts), 1) if len(ts) else 0

    ts_placed = ts[ts["progress_student"] == "Placement"]
    avg_time = None
    if len(ts_placed):
        merged = ts_placed.merge(
            d[["nama_perusahaan", "posisi", "request_date"]],
            left_on=["company", "position"], right_on=["nama_perusahaan", "posisi"],
            how="left",
        )
        deltas = (merged["last_update"] - merged["request_date"]).dt.days.dropna()
        if len(deltas):
            avg_time = round(deltas.mean(), 1)

    kpi_row = [
        kpi_card("Fulfillment rate", f"{fulfillment_rate}%", "Posisi terisi VS Total headcount diminta",
                 color=COLORS["success"] if fulfillment_rate >= 80 else COLORS["warning"],
                 accent=COLORS["success"] if fulfillment_rate >= 80 else COLORS["warning"]),
        kpi_card("Total placement", f"{total_placed}", "Kandidat berhasil ditempatkan",
                 color=COLORS["success"], accent=COLORS["success"]),
        kpi_card("Conversion rate", f"{placement_rate}%", "Placement dari kandidat yang diproses",
                 color=COLORS["success"] if placement_rate >= 40 else COLORS["warning"],
                 accent=COLORS["success"] if placement_rate >= 40 else COLORS["warning"]),
        kpi_card("Avg time to placement", f"{avg_time} hari" if avg_time is not None else "-",
                 "Request date -> Placement update"),
    ]

    if len(d):
        req_by_month = (
            d.dropna(subset=["request_date"])
             .groupby(d["request_date"].dt.to_period("M"))["jumlah_permintaan"]
             .sum()
        )
    else:
        req_by_month = pd.Series(dtype=float)
    if len(ts_placed):
        placed_by_month = (
            ts_placed.dropna(subset=["last_update"])
                      .groupby(ts_placed["last_update"].dt.to_period("M"))
                      .size()
        )
    else:
        placed_by_month = pd.Series(dtype=float)

    months = sorted(set(req_by_month.index) | set(placed_by_month.index))
    trend_fig = go.Figure()
    if months:
        month_labels = [str(m) for m in months]
        trend_fig.add_trace(go.Scatter(
            x=month_labels, y=[req_by_month.get(m, 0) for m in months],
            mode="lines+markers", name="Request",
            line=dict(color=COLORS["primary_dark"], width=2),
        ))
        trend_fig.add_trace(go.Scatter(
            x=month_labels, y=[placed_by_month.get(m, 0) for m in months],
            mode="lines+markers", name="Placement",
            line=dict(color=COLORS["primary_soft"], width=2),
        ))
        trend_fig.update_layout(**PLOTLY_LAYOUT, height=280, legend=dict(orientation="h", y=-0.25))
    else:
        trend_fig = empty_fig(280)

    if len(ts) and ts["jenis_penempatan"].notna().any():
        jenis_counts = ts["jenis_penempatan"].value_counts()
        jenis_fig = go.Figure(go.Pie(
            labels=jenis_counts.index, values=jenis_counts.values,
            marker=dict(colors=CATEGORICAL), hole=0.4,
        ))
        jenis_fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=True,
                               legend=dict(orientation="h", y=-0.15, font=dict(size=10)))
    else:
        jenis_fig = empty_fig(280)

    kota_caption = ""
    if len(d) and d["kota"].notna().any():
        kota_counts = (
            d.dropna(subset=["kota"])
             .groupby("kota")["jumlah_dikirimkan"].sum()
             .sort_values(ascending=False)
        )
        coords = kota_counts.index.to_series().apply(city_coord)
        mapped = kota_counts[coords.notna()]
        unmapped = kota_counts[coords.isna()]

        if len(mapped):
            lats = [city_coord(c)[0] for c in mapped.index]
            lons = [city_coord(c)[1] for c in mapped.index]
            sizes = mapped.values
            max_size = sizes.max() if sizes.max() else 1
            marker_sizes = 10 + 30 * (sizes / max_size)

            kota_fig = go.Figure(go.Scattergeo(
                lat=lats, lon=lons,
                text=[f"{c}: {v} kandidat" for c, v in zip(mapped.index, mapped.values)],
                hoverinfo="text",
                marker=dict(
                    size=marker_sizes,
                    color=CATEGORICAL[1],
                    opacity=0.75,
                    line=dict(width=1, color=COLORS["primary_dark"]),
                ),
            ))
            kota_fig.update_geos(
                scope="asia",
                center=dict(lat=-2.5, lon=118),
                projection_scale=1,
                lataxis_range=[-11, 7],
                lonaxis_range=[94, 142],
                showland=True, landcolor=COLORS["bg"],
                showocean=True, oceancolor=COLORS["surface"],
                showcountries=True, countrycolor=COLORS["border"],
                showsubunits=False,
                bgcolor=COLORS["surface"],
                resolution=110,
            )
            kota_fig.update_layout(
                paper_bgcolor=COLORS["surface"],
                font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
                margin=dict(l=0, r=0, t=10, b=0),
                height=280,
            )
        else:
            kota_fig = empty_fig(280, "Kota tidak dikenali koordinatnya")

        if len(unmapped):
            kota_caption = "Belum ada koordinat untuk: " + ", ".join(unmapped.index[:6])
            if len(unmapped) > 6:
                kota_caption += f", +{len(unmapped) - 6} lainnya"
    else:
        kota_fig = empty_fig(280)

    if len(d):
        top_companies = (
            d.groupby("nama_perusahaan")["jumlah_permintaan"].sum()
             .sort_values(ascending=True)
             .tail(10)
        )
        top_fig = go.Figure(go.Bar(
            x=top_companies.values, y=top_companies.index, orientation="h",
            marker_color=CATEGORICAL[0],
        ))
        top_fig.update_layout(**PLOTLY_LAYOUT, height=280, xaxis_title="Total permintaan")
    else:
        top_fig = empty_fig(280)

    if len(d):
        comp_summary = d.groupby("nama_perusahaan").agg(dikirim=("jumlah_dikirimkan", "sum")).reset_index()
        placed_counts = (
            ts_placed.groupby("company").size().reset_index(name="placed")
            if len(ts_placed) else pd.DataFrame(columns=["company", "placed"])
        )
        comp_summary = comp_summary.merge(placed_counts, left_on="nama_perusahaan", right_on="company", how="left")
        comp_summary["placed"] = comp_summary["placed"].fillna(0)
        comp_summary["rate"] = pd.to_numeric(
            100 * comp_summary["placed"] / comp_summary["dikirim"].replace(0, pd.NA), errors="coerce"
        ).round(0).fillna(0)
        comp_summary = comp_summary[comp_summary["dikirim"] > 0].sort_values("rate", ascending=True).tail(10)
        rate_fig = go.Figure(go.Bar(
            x=comp_summary["rate"], y=comp_summary["nama_perusahaan"], orientation="h",
            marker_color=COLORS["success"],
        ))
        rate_fig.update_layout(**PLOTLY_LAYOUT, height=280, xaxis_title="Success rate (%)")
    else:
        rate_fig = empty_fig(280)

    if len(ts):
        ts_prodi = ts.merge(student_all[["NIM", "program_studi"]], on="NIM", how="left")
        prodi_counts = (
            ts_prodi[ts_prodi["progress_student"] == "Placement"]
            .groupby("program_studi").size()
            .sort_values(ascending=True)
        )
        if len(prodi_counts):
            prodi_fig = go.Figure(go.Bar(
                x=prodi_counts.values, y=prodi_counts.index, orientation="h",
                marker_color=CATEGORICAL[2],
            ))
            prodi_fig.update_layout(**PLOTLY_LAYOUT, height=280, xaxis_title="Total placement")
        else:
            prodi_fig = empty_fig(280)
    else:
        prodi_fig = empty_fig(280)

    return kpi_row, trend_fig, jenis_fig, kota_fig, kota_caption, top_fig, rate_fig, prodi_fig


@callback(
    Output("ov-prodi-detail", "children"),
    Input("ov-prodi-bar", "clickData"),
    Input("ov-filter-semester", "value"),
    Input("ov-filter-daterange", "start_date"),
    Input("ov-filter-daterange", "end_date"),
    Input("ov-filter-sektor", "value"),
)
def update_prodi_detail(click_data, semester, start_date, end_date, sektor):
    if not click_data:
        return html.Div(
            "Klik salah satu bar di atas untuk melihat daftar mahasiswa per program studi.",
            style={"fontSize": "12px", "color": COLORS["muted"]},
        )

    prodi = click_data["points"][0]["y"]
    d = filter_tc(semester, start_date, end_date, sektor)
    ts = matching_students(d)
    ts_prodi = ts.merge(student_all[["NIM", "program_studi"]], on="NIM", how="left")
    sub = ts_prodi[
        (ts_prodi["program_studi"] == prodi) & (ts_prodi["progress_student"] == "Placement")
    ]

    if not len(sub):
        return html.Div(f"Tidak ada data placement untuk {prodi} pada filter ini.",
                         style={"fontSize": "12px", "color": COLORS["muted"]})

    table = dash_table.DataTable(
        columns=[
            {"name": "NIM", "id": "NIM"},
            {"name": "Nama", "id": "student_name"},
            {"name": "Company", "id": "company"},
            {"name": "Posisi", "id": "position"},
            {"name": "Update terakhir", "id": "last_update"},
        ],
        data=sub.assign(
            last_update=sub["last_update"].dt.date.astype(str)
        )[["NIM", "student_name", "company", "position", "last_update"]].to_dict("records"),
        style_as_list_view=True,
        page_size=8,
        style_header={"backgroundColor": COLORS["surface"], "fontWeight": "600", "fontSize": "11px",
                      "borderBottom": f"1px solid {COLORS['border']}"},
        style_cell={"fontSize": "12px", "padding": "6px 8px", "fontFamily": "Inter, sans-serif"},
    )
    return html.Div([
        html.Div(f"Mahasiswa placement — {prodi}", style={"fontSize": "12px", "fontWeight": "600",
                                                            "color": COLORS["text"], "marginBottom": "6px"}),
        table,
    ])