# Student Placement System

A dashboard for monitoring student placements (internships and jobs) at partner companies, built by team **Clushthree** for SSDC 2026 (`SSDC2026018`).

It helps a university placement team track placement performance, monitor ongoing recruitment, and match students to talent requests from companies.

## Pages

| Page | Path | What it shows |
|---|---|---|
| **Performance Overview** | `/` | KPIs for fulfillment rate, total placements, conversion rate and average time to placement; monthly requests vs. placements; placement type distribution; placement map; top recruiting companies and success rates; placements by study program (click a bar to list the students). Filters: semester, industry sector. |
| **Recruitment Operations** | `/operational` | KPIs for open requests, average processing time, candidates needing follow-up and ghosting cases; request status breakdown; recruitment funnel; ghosting trend; priority requests. Filters: minimum semester, position, working arrangement, field of study. |
| **Talent Matching** | `/talent-matching` | KPIs for available students, document completeness, sync status and average match score; candidate table scored against a talent request; CV/portfolio completeness, tools & skills coverage, GPA distribution, talent pool funnel. Filters: study program, position, arrangement, semester, domicile, GPA range, tools search. |

Every page has an **Export PDF** button.

## Tech stack

- [Dash](https://dash.plotly.com/) (multi-page, `use_pages=True`) + [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)
- Plotly for charts, pandas/numpy for data processing

## Project structure

```
ssdc-26/
├── app.py               # entry point: main layout, sidebar, navigation
├── pages/               # one file per page (registered with dash.register_page)
│   ├── overview.py
│   ├── operational.py
│   └── talent matching.py
├── utils/
│   ├── data_loader.py   # loads every CSV in dataset/
│   ├── components.py    # UI components: kpi_card, section_card, page_header, filter_control
│   └── theme.py         # colors, spacing, Plotly layout
├── assets/              # style.css and logo (loaded automatically by Dash)
├── dataset/             # CSV data
└── requirements.txt
```

## Dataset

All data lives in `dataset/` and is loaded by [utils/data_loader.py](utils/data_loader.py).

| File | Contents | Notes |
|---|---|---|
| `company.csv` | Partner companies (~1,500 rows) | |
| `talent_request.csv` | Talent requests from companies (~12,000 rows) | |
| `student_all.csv` | Student master data (~25,000 rows) | |
| `status_student.csv` | Student status, GPA, documents, availability and tools | `;` separator, `DD/MM/YYYY` dates |
| `tracking_company.csv` | Progress of each request and the students sent | `DD/MM/YYYY` dates |
| `tracking_student.csv` | Progress of each student through recruitment (~41,600 rows) | |

## Running locally

Requires Python 3.11 or newer.

```bash
git clone https://github.com/feliciadrey/ssdc-26.git
cd ssdc-26

python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:8050.
