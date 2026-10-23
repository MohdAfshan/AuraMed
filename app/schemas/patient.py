from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientBase(BaseModel):
    patient_code: str
    full_name: str
    phone_number: str


class PatientCreate(PatientBase):
    pass


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PatientLookupResponse(BaseModel):
    id: int
    patient_code: str
    full_name_masked: str
