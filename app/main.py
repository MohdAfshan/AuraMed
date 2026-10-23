from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.patients import router as patients_router
from app.api.auth_user import router as auth_user_router
from app.api.auth_hospital import router as auth_hospital_router
from app.api.reports import router as reports_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AuraMed API")
app.include_router(health_router)
app.include_router(patients_router)
app.include_router(auth_user_router)
app.include_router(auth_hospital_router)
app.include_router(reports_router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")