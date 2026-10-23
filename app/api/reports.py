import logging
from datetime import datetime
from pathlib import Path
from shutil import copyfileobj

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    TokenPayload,
    bearer_scheme,
    get_current_hospital,
    get_current_patient,
)
from app.core.audit import log_action
from app.core.config import BASE_DIR
from app.db.session import get_db
from app.models import MedicalReport, Patient
from app.models.medical_report import ReportType
from app.rag.chunking import chunk_text
from app.rag.extraction import extract_text_from_file
from app.rag.llm import extract_structured_data, generate_summary
from app.rag.vector_store import add_chunks, query_chunks
from app.schemas.medical_report import MedicalReportResponse

router = APIRouter(tags=["reports"])
logger = logging.getLogger(__name__)


class MedicalReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: ReportType
    title: str
    created_at: datetime


class HospitalPatientLookup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: str
    full_name: str


class RetrieveQuery(BaseModel):
    query: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    try:
        return get_current_patient(credentials)
    except HTTPException as patient_error:
        try:
            return get_current_hospital(credentials)
        except HTTPException:
            raise patient_error


@router.get(
    "/patients/me/reports",
    response_model=list[MedicalReportSummary],
)
def get_my_reports(
    current: TokenPayload = Depends(get_current_patient),
    db: Session = Depends(get_db),
) -> list[MedicalReport]:
    return list(
        db.scalars(
            select(MedicalReport)
            .where(MedicalReport.patient_id == current.patient_id)
            .order_by(MedicalReport.created_at.desc())
        ).all()
    )


@router.get("/patients/me/summary")
def get_my_summary(
    current: TokenPayload = Depends(get_current_patient),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    patient = db.scalar(select(Patient).where(Patient.id == current.patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    chunks = query_chunks(
        patient.patient_code,
        "patient medical history conditions medications allergies findings",
        top_k=10,
    )
    if not chunks:
        return {
            "summary": "There isn't enough report data yet to generate a summary.",
            "based_on_reports": 0,
        }

    return {
        "summary": generate_summary(
            patient.full_name,
            [chunk["text"] for chunk in chunks],
        ),
        "based_on_reports": len({chunk["report_id"] for chunk in chunks}),
    }


@router.get("/patients/me/extracted-data")
def get_my_extracted_data(
    current: TokenPayload = Depends(get_current_patient),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.scalar(select(Patient).where(Patient.id == current.patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    chunks = query_chunks(
        patient.patient_code,
        "patient medical history conditions medications allergies findings",
        top_k=10,
    )
    if not chunks:
        data = {
            "allergies": [],
            "conditions": [],
            "medications": [],
            "history": [],
            "vitals": [],
        }
    else:
        data = extract_structured_data([chunk["text"] for chunk in chunks])

    return {"ai_extracted": True, "data": data}


@router.get(
    "/reports/{report_id}",
    response_model=MedicalReportResponse,
)
def get_report(
    report_id: int,
    current: TokenPayload = Depends(get_current_patient),
    db: Session = Depends(get_db),
) -> MedicalReport:
    report = db.scalar(
        select(MedicalReport).where(
            MedicalReport.id == report_id,
            MedicalReport.patient_id == current.patient_id,
        )
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return report


@router.get(
    "/hospitals/patients/{patient_code}",
    response_model=HospitalPatientLookup,
)
def get_hospital_patient(
    patient_code: str,
    current: TokenPayload = Depends(get_current_hospital),
    db: Session = Depends(get_db),
) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.patient_code == patient_code))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient


@router.post(
    "/hospitals/patients/{patient_code}/reports",
    response_model=MedicalReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_report(
    patient_code: str,
    report_type: ReportType = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    current: TokenPayload = Depends(get_current_hospital),
    db: Session = Depends(get_db),
) -> MedicalReport:
    patient = db.scalar(select(Patient).where(Patient.patient_code == patient_code))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    filename = Path(file.filename or "").name
    if not filename or filename in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid file name is required",
        )

    upload_directory = BASE_DIR / "uploads" / patient.patient_code
    upload_directory.mkdir(parents=True, exist_ok=True)
    upload_path = upload_directory / filename
    with upload_path.open("wb") as destination:
        copyfileobj(file.file, destination)

    report = MedicalReport(
        patient_id=patient.id,
        hospital_id=current.hospital_id,
        report_type=report_type,
        title=title,
        file_path=upload_path.relative_to(BASE_DIR).as_posix(),
    )
    db.add(report)
    db.flush()

    log_action(
        db,
        actor_type="hospital",
        actor_id=str(current.sub),
        action="report_upload",
        target_patient_id=patient.id,
    )
    db.refresh(report)

    try:
        extracted_text = extract_text_from_file(str(upload_path))
        if extracted_text:
            chunks = chunk_text(extracted_text)
            add_chunks(
                patient.patient_code,
                report.id,
                report.title,
                chunks,
                report.created_at,
            )
    except Exception:
        logger.exception("Failed to ingest report %s", report.id)

    return report


@router.post("/patients/{patient_code}/retrieve")
def retrieve_patient_chunks(
    patient_code: str,
    body: RetrieveQuery,
    current: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    patient = db.scalar(select(Patient).where(Patient.patient_code == patient_code))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    if current.role == "patient" and current.patient_id != patient.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access denied",
        )

    return query_chunks(patient_code, body.query)