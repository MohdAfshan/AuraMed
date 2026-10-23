from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload:
    def __init__(self, sub: str, role: str, patient_id: int | None = None, hospital_id: int | None = None):
        self.sub = sub
        self.role = role
        self.patient_id = patient_id
        self.hospital_id = hospital_id


def _decode_token(credentials: HTTPAuthorizationCredentials | None) -> TokenPayload:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return TokenPayload(
        sub=payload.get("sub"),
        role=payload.get("role"),
        patient_id=payload.get("patient_id"),
        hospital_id=payload.get("hospital_id"),
    )


def get_current_patient(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenPayload:
    token_data = _decode_token(credentials)
    if token_data.role != "patient" or token_data.patient_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient access required")
    return token_data


def get_current_hospital(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenPayload:
    token_data = _decode_token(credentials)
    if token_data.role != "hospital" or token_data.hospital_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")
    return token_data