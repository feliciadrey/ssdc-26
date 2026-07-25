from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "dataset"


def load_all():
    company = pd.read_csv(
        DATA_DIR / "company.csv",
        parse_dates=["created_at"],
        encoding="utf-8-sig",
    )
    talent_request = pd.read_csv(
        DATA_DIR / "talent_request.csv",
        parse_dates=["request_date"],
        encoding="utf-8-sig",
    )
    student_all = pd.read_csv(DATA_DIR / "student_all.csv", encoding="utf-8-sig")
    status_student = pd.read_csv(
        DATA_DIR / "status_student.csv",
        sep=";",
        parse_dates=["sync_date"],
        dayfirst=True,
        encoding="utf-8-sig",
    )
    tracking_company = pd.read_csv(
        DATA_DIR / "tracking_company.csv",
        parse_dates=["request_date", "send_date"],
        dayfirst=True,
        encoding="utf-8-sig",
    )
    tracking_student = pd.read_csv(
        DATA_DIR / "tracking_student.csv",
        parse_dates=["last_update"],
        encoding="utf-8-sig",
    )
    return {
        "company": company,
        "talent_request": talent_request,
        "student_all": student_all,
        "status_student": status_student,
        "tracking_company": tracking_company,
        "tracking_student": tracking_student,
    }
