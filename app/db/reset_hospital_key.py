import argparse
import hashlib
import secrets

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Hospital


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and store a new key for a hospital."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--name", help="Exact hospital name")
    target.add_argument("--id", type=int, dest="hospital_id", help="Hospital ID")
    return parser.parse_args()


def reset_hospital_key(*, hospital_id: int | None, name: str | None) -> None:
    new_key = secrets.token_urlsafe(32)

    with SessionLocal() as db:
        if hospital_id is not None:
            hospital = db.scalar(select(Hospital).where(Hospital.id == hospital_id))
        else:
            hospital = db.scalar(select(Hospital).where(Hospital.name == name))

        if hospital is None:
            target = f"id {hospital_id}" if hospital_id is not None else f'name "{name}"'
            raise SystemExit(f"No hospital found with {target}.")

        hospital.hashed_key = hash_key(new_key)
        db.commit()
        print(f"NEW KEY for {hospital.name}: {new_key}")


if __name__ == "__main__":
    args = parse_args()
    reset_hospital_key(hospital_id=args.hospital_id, name=args.name)
