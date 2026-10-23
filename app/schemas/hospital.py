from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HospitalBase(BaseModel):
    name: str
    hashed_key: str


class HospitalCreate(HospitalBase):
    pass


class HospitalResponse(HospitalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
