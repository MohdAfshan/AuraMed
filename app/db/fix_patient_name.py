from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Patient


PATIENT_CODE = "AURAMED-P-10234"
CURRENT_NAME = "Aisha Rahman"
UPDATED_NAME = "Amara Patel"


def fix_patient_name() -> None:
    with SessionLocal() as db:
        patient = db.scalar(
            select(Patient).where(
                Patient.patient_code == PATIENT_CODE,
                Patient.full_name == CURRENT_NAME,
            )
        )
        if patient is None:
            raise SystemExit(
                f'No patient found with code "{PATIENT_CODE}" and name "{CURRENT_NAME}".'
            )

        patient.full_name = UPDATED_NAME
        db.commit()
        db.refresh(patient)
        print(
            f"Updated patient {patient.patient_code}: "
            f"{CURRENT_NAME} -> {patient.full_name}"
        )


if __name__ == "__main__":
    fix_patient_name()
