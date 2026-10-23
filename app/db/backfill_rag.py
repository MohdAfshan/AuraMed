import logging
from pathlib import Path

from sqlalchemy import select

from app.core.config import BASE_DIR
from app.db.session import SessionLocal
from app.models import MedicalReport, Patient
from app.rag.chunking import chunk_text
from app.rag.extraction import extract_text_from_file
from app.rag.vector_store import add_chunks

logger = logging.getLogger(__name__)


def main() -> None:
    processed = 0
    succeeded = 0
    failed_extraction = 0

    with SessionLocal() as db:
        reports = db.scalars(
            select(MedicalReport).join(Patient)
        ).all()

        for report in reports:
            processed += 1
            file_path = Path(report.file_path)
            if not file_path.is_absolute():
                file_path = BASE_DIR / file_path

            try:
                text = extract_text_from_file(str(file_path))
                if not text.strip():
                    failed_extraction += 1
                    continue

                chunks = chunk_text(text)
                add_chunks(
                    report.patient.patient_code,
                    report.id,
                    report.title,
                    chunks,
                    report.created_at,
                )
                succeeded += 1
            except Exception:
                failed_extraction += 1
                logger.exception("Failed to backfill report %s", report.id)

    print(f"Reports processed: {processed}")
    print(f"Reports succeeded: {succeeded}")
    print(f"Reports failed extraction: {failed_extraction}")


if __name__ == "__main__":
    main()
