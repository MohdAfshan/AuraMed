from app.db.session import Base, engine
from app.models import AuthOtp, Hospital, MedicalReport, Patient, AuditLog


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")