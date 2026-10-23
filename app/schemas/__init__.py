from app.schemas.auth_otp import AuthOtpCreate, AuthOtpResponse
from app.schemas.hospital import HospitalCreate, HospitalResponse
from app.schemas.medical_report import MedicalReportCreate, MedicalReportResponse
from app.schemas.patient import PatientCreate, PatientLookupResponse, PatientResponse

__all__ = [
	"AuthOtpCreate",
	"AuthOtpResponse",
	"HospitalCreate",
	"HospitalResponse",
	"MedicalReportCreate",
	"MedicalReportResponse",
	"PatientCreate",
	"PatientLookupResponse",
	"PatientResponse",
]
