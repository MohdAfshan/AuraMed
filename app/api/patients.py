from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Patient
from app.schemas.patient import PatientLookupResponse
from app.core.security import get_current_patient, TokenPayload

router = APIRouter(prefix="/patients")


def mask_name(full_name: str) -> str:
    return " ".join(
        f"{part[0]}{'*' * max(len(part) - 1, 1)}" for part in full_name.split()
    )


@router.get("/me")
def get_my_patient_info(
    current: TokenPayload = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == current.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "full_name": patient.full_name,
    }


@router.get(
    "/{patient_code}",
    response_model=PatientLookupResponse,
)
def get_patient(patient_code: str, db: Session = Depends(get_db)) -> PatientLookupResponse:
    patient = db.scalar(select(Patient).where(Patient.patient_code == patient_code))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient not found: {patient_code}",
        )

    return PatientLookupResponse(
        id=patient.id,
        patient_code=patient.patient_code,
        full_name_masked=mask_name(patient.full_name),
    )