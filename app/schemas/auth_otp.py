from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthOtpBase(BaseModel):
    patient_id: int
    otp_code: str
    expires_at: datetime
    verified: bool = False


class AuthOtpCreate(AuthOtpBase):
    pass


class AuthOtpResponse(AuthOtpBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
