import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.patient import Patient
from app.models.auth_otp import AuthOtp
from app.core.audit import log_action

router = APIRouter(prefix="/auth/user", tags=["user-auth"])

_failed_attempts: dict[str, int] = {}
MAX_ATTEMPTS = 5


class RequestOtpBody(BaseModel):
    patient_code: str
    phone_number: str


class VerifyOtpBody(BaseModel):
    patient_code: str
    otp_code: str


@router.post("/request-otp")
def request_otp(body: RequestOtpBody, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_code == body.patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.phone_number != body.phone_number:
        raise HTTPException(status_code=400, detail="Phone number does not match our records")

    otp_code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

    otp_entry = AuthOtp(
        patient_id=patient.id,
        otp_code=otp_code,
        expires_at=expires_at,
        verified=False,
    )
    db.add(otp_entry)
    db.commit()

    print(f"\n>>> OTP for {patient.patient_code} ({patient.phone_number}): {otp_code}\n")

    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
def verify_otp(body: VerifyOtpBody, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.patient_code == body.patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    attempt_key = body.patient_code
    if _failed_attempts.get(attempt_key, 0) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    otp_entry = (
        db.query(AuthOtp)
        .filter(AuthOtp.patient_id == patient.id, AuthOtp.verified == False)  # noqa: E712
        .order_by(AuthOtp.id.desc())
        .first()
    )

    now = datetime.now(timezone.utc)

    if (
        not otp_entry
        or otp_entry.otp_code != body.otp_code
        or otp_entry.expires_at.replace(tzinfo=timezone.utc) < now
    ):
        _failed_attempts[attempt_key] = _failed_attempts.get(attempt_key, 0) + 1
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp_entry.verified = True
    db.commit()
    log_action(db, actor_type="patient", actor_id=patient.patient_code, action="login_success", target_patient_id=patient.id)
    _failed_attempts.pop(attempt_key, None)

    token_payload = {
        "sub": patient.patient_code,
        "role": "patient",
        "patient_id": patient.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer"}