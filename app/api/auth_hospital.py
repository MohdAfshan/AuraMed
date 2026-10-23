import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.hospital import Hospital
from app.core.audit import log_action

router = APIRouter(prefix="/auth/hospital", tags=["hospital-auth"])

_failed_attempts: dict[str, int] = {}
MAX_ATTEMPTS = 5


class HospitalLoginBody(BaseModel):
    hospital_key: str


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


@router.post("/login")
def hospital_login(body: HospitalLoginBody, db: Session = Depends(get_db)):
    # Use a generic key for attempt-tracking since we don't know the hospital until we match the hash
    attempt_key = body.hospital_key[:8]  # partial, just to bucket repeated identical wrong attempts
    if _failed_attempts.get(attempt_key, 0) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    hashed_input = hash_key(body.hospital_key)
    hospital = db.query(Hospital).filter(Hospital.hashed_key == hashed_input).first()

    if not hospital:
        _failed_attempts[attempt_key] = _failed_attempts.get(attempt_key, 0) + 1
        raise HTTPException(status_code=401, detail="Invalid hospital key")

    _failed_attempts.pop(attempt_key, None)
    log_action(db, actor_type="hospital", actor_id=hospital.name, action="login_success")

    token_payload = {
        "sub": hospital.name,
        "role": "hospital",
        "hospital_id": hospital.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer", "hospital_name": hospital.name}