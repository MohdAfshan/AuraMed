from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
	DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'auramed.db').as_posix()}"
	SECRET_KEY: str = "replace-this-development-secret"
	OTP_EXPIRY_SECONDS: int = 300
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
	ENVIRONMENT: str = "development"
	DEBUG: bool = True

	model_config = SettingsConfigDict(
		env_file=BASE_DIR / ".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)


settings = Settings()
DATABASE_URL = settings.DATABASE_URL
