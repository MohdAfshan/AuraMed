from pathlib import Path

from sqlalchemy import select

from app.core.config import BASE_DIR
from app.db.session import SessionLocal
from app.models import MedicalReport
from app.rag.vector_store import collection


REPORT_IDS_TO_DELETE = [1, 2, 3, 4, 5]


def delete_bad_reports() -> None:
    deleted_rows: list[int] = []
    deleted_files: list[str] = []
    kept_shared_files: list[str] = []
    missing_files: list[str] = []
    removed_vectors: dict[int, int] = {}

    with SessionLocal() as db:
        for report_id in REPORT_IDS_TO_DELETE:
            report = db.scalar(
                select(MedicalReport).where(MedicalReport.id == report_id)
            )
            if report is None:
                raise SystemExit(f"MedicalReport {report_id} was not found.")

            shared_report = db.scalar(
                select(MedicalReport.id).where(
                    MedicalReport.file_path == report.file_path,
                    MedicalReport.id.not_in(REPORT_IDS_TO_DELETE),
                )
            )
            report_path = Path(report.file_path)
            if not report_path.is_absolute():
                report_path = BASE_DIR / report_path

            if shared_report is not None:
                kept_shared_files.append(
                    f"{report.file_path} (shared with report {shared_report})"
                )
            elif report_path.exists():
                report_path.unlink()
                deleted_files.append(str(report_path))
            else:
                missing_files.append(str(report_path))

            vector_entries = collection.get(
                where={"report_id": report_id},
                include=["metadatas"],
            )
            vector_count = len(vector_entries["ids"])
            if vector_count:
                collection.delete(where={"report_id": report_id})
            removed_vectors[report_id] = vector_count

            db.delete(report)
            deleted_rows.append(report_id)

        db.commit()

    print("Deleted database rows:", ", ".join(map(str, deleted_rows)) or "none")
    print("Deleted files:")
    for file_path in deleted_files:
        print(f"  - {file_path}")
    if not deleted_files:
        print("  - none")
    print("Kept shared files:")
    for file_path in kept_shared_files:
        print(f"  - {file_path}")
    if not kept_shared_files:
        print("  - none")
    print("Missing files:")
    for file_path in missing_files:
        print(f"  - {file_path}")
    if not missing_files:
        print("  - none")
    print("Removed vector entries:")
    for report_id in REPORT_IDS_TO_DELETE:
        print(f"  - report {report_id}: {removed_vectors[report_id]}")


if __name__ == "__main__":
    delete_bad_reports()
