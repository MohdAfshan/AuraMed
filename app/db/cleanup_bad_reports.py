from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import MedicalReport, Patient
from app.rag.extraction import extract_text_from_file


BASE_DIR = Path(__file__).resolve().parents[2]


def print_report_extraction_status() -> None:
    with SessionLocal() as db:
        report_patients = db.execute(
            select(MedicalReport, Patient)
            .join(Patient, MedicalReport.patient_id == Patient.id)
            .order_by(MedicalReport.id)
        ).all()

    rows = []
    for report, patient in report_patients:
        path = Path(report.file_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        extracted_text = extract_text_from_file(str(path))
        result = f"OK - {len(extracted_text)} chars" if extracted_text else "EMPTY/FAILED"
        rows.append(
            (
                str(report.id),
                patient.patient_code,
                patient.full_name,
                report.title,
                report.file_path,
                result,
            )
        )

    print_table(
        ("REPORT ID", "PATIENT CODE", "PATIENT NAME", "TITLE", "FILE PATH", "EXTRACTION"),
        rows or [("-", "-", "-", "No reports", "-", "-")],
    )


def print_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    separator = "-+-".join("-" * width for width in widths)

    print(" | ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print(separator)
    for row in rows:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))


if __name__ == "__main__":
    print_report_extraction_status()
