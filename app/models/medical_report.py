from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReportType(str, Enum):
    BLOOD = "BLOOD"
    ECG = "ECG"
    XRAY = "XRAY"
    CT = "CT"
    MRI = "MRI"
    PRESCRIPTION = "PRESCRIPTION"
    LAB = "LAB"
    DIAGNOSIS = "DIAGNOSIS"
    OTHER = "OTHER"


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), nullable=False, index=True)
    report_type: Mapped[ReportType] = mapped_column(
        SqlEnum(ReportType, name="report_type"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    patient = relationship("Patient", back_populates="medical_reports")
    hospital = relationship("Hospital", back_populates="medical_reports")
