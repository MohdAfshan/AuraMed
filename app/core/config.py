from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
	DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'auramed.db').as_posix()}"
	SECRET_KEY: str
	OTP_EXPIRY_SECONDS: int = 300
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
	ENVIRONMENT: str = "development"
	DEBUG: bool = True
	SEED_PATIENT_10234_PHONE: str = ""
	SEED_PATIENT_10235_PHONE: str = ""
	SEED_PATIENT_10236_PHONE: str = ""
	SEED_HOSPITAL_AURAMED_GENERAL_KEY: str = ""
	SEED_HOSPITAL_SUNRISE_DIAGNOSTICS_KEY: str = ""

	model_config = SettingsConfigDict(
		env_file=BASE_DIR / ".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)


settings = Settings()
DATABASE_URL = settings.DATABASE_URL
