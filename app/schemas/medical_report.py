from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.medical_report import ReportType


class MedicalReportBase(BaseModel):
    patient_id: int
    hospital_id: int
    report_type: ReportType
    title: str
    file_path: str


class MedicalReportCreate(MedicalReportBase):
    pass


class MedicalReportResponse(MedicalReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
