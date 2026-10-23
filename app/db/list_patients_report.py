from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models import Patient


def print_patient_report() -> None:
    with SessionLocal() as db:
        patients = db.scalars(
            select(Patient)
            .options(selectinload(Patient.medical_reports))
            .order_by(Patient.id)
        ).all()

    patient_rows = [
        (str(patient.id), patient.patient_code, patient.full_name, str(len(patient.medical_reports)))
        for patient in patients
    ]
    report_rows = [
        (
            str(patient.id),
            str(report.id),
            report.title,
            report.file_path,
        )
        for patient in patients
        for report in sorted(patient.medical_reports, key=lambda item: item.id)
    ]

    print("PATIENTS")
    print_table(
        ("ID", "PATIENT CODE", "FULL NAME", "REPORT COUNT"),
        patient_rows,
    )
    print("\nMEDICAL REPORTS")
    print_table(
        ("PATIENT ID", "REPORT ID", "TITLE", "FILE PATH"),
        report_rows or [("-", "-", "No reports", "-")],
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
    print_patient_report()
