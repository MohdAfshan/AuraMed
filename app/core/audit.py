from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(db: Session, actor_type: str, actor_id: str, action: str, target_patient_id: int | None = None) -> None:
    db.add(AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_patient_id=target_patient_id,
    ))
    db.commit()