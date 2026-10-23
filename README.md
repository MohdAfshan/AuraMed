# AuraMed

Privacy-focused medical records platform (FastAPI backend + Android app).

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Kotlin](https://img.shields.io/badge/Kotlin-Android-7F52FF?logo=kotlin&logoColor=white)](https://kotlinlang.org/)
[![Jetpack Compose](https://img.shields.io/badge/Jetpack%20Compose-UI-4285F4?logo=jetpackcompose&logoColor=white)](https://developer.android.com/compose)

## Overview

AuraMed is a local-first medical-records platform for patients and hospitals. Patients can authenticate with a patient code, phone number, and one-time password, then view their own reports and AI-generated views of the information in those reports. Hospitals can authenticate with a hospital key, look up patients, and upload reports.

The backend stores records in a local SQLite database and keeps report retrieval scoped to a patient. PDF extraction, embeddings, vector search, and language-model generation are designed to run locally; patient data is not sent to third-party AI APIs.

The repository currently contains the FastAPI backend and its local development data/scripts. The Android client is described in the project planning documents but its Kotlin/Gradle source is not present in this checkout.

## Features

### Patient

- OTP login using a patient code and the phone number stored for that patient.
- View the authenticated patient's report list and individual report metadata.
- Access report files served by the backend.
- Generate a local-LLM summary from retrieved report excerpts.
- Retrieve AI-extracted allergies, conditions, medications, history, and vitals. These results are labelled as AI-extracted and are not verified.

### Hospital

- Authenticate with a hospital key.
- Look up a patient by patient code.
- Upload a report for a patient as a multipart form submission.

### AI/RAG

- Extract text from PDF reports with `pypdf`.
- Split extracted text into overlapping word chunks.
- Create local embeddings with `all-MiniLM-L6-v2`.
- Persist and query report chunks in ChromaDB, filtered by patient code.
- Apply recency-aware retrieval: results are sorted newest first, and the LLM prompt instructs the model to prefer the most recent value when reports conflict.
- Generate summaries and structured clinical data with a locally running Ollama model.

### Security

- JWT bearer authentication with separate patient and hospital roles.
- Patient report queries are restricted to the authenticated patient's ID.
- Hospital keys are stored as SHA-256 hashes.
- Basic failed-attempt throttling is applied to OTP and hospital-key authentication.
- Authentication and report-upload actions are recorded in an audit-log table.

## Known limitations / mocked

- OTPs are not sent through an SMS gateway. In development, the generated OTP is printed to the backend console and must be copied from there.
- No AI chat-assistant endpoint is implemented. The current AI surface is report retrieval, summaries, and structured extraction.
- The backend has no age, date-of-birth, or blood-type fields; those profile values cannot be treated as verified data.
- The Android client is not included in this repository, so the Android badges and planned client stack do not represent buildable source in this checkout.
- The default development secret in `app/core/config.py` must be replaced through environment configuration before deployment.
- Local in-memory attempt counters and SQLite are development-oriented and are not a production authentication or scaling design.

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.10 (current virtual environment), FastAPI, Uvicorn | HTTP API and development server |
| Backend data | SQLAlchemy, SQLite | ORM and local persistence in `auramed.db` |
| Backend auth | `python-jose` JWT, Pydantic Settings | Bearer tokens, role claims, and environment configuration |
| AI/RAG | `pypdf` | PDF text extraction |
| AI/RAG | `sentence-transformers` with `all-MiniLM-L6-v2` | Local text embeddings |
| AI/RAG | ChromaDB | Persistent local vector collection |
| AI/RAG | Ollama with `llama3.1:8b` by default | Local summary and structured-data generation |
| Android (planned/not present here) | Kotlin, Jetpack Compose, Retrofit, OkHttp, Navigation Compose | Planned mobile UI and API client |
| Tools | Postman, Android Studio, VS Code, `adb` | Planned/manual API, Android, and development workflows |

The backend dependencies are listed in [`requirements.txt`](./requirements.txt). No Gradle files or Kotlin sources are present in this checkout to verify Android dependency versions.

## Architecture

The current backend flow is local-first:

```text
+-----------------------+
| Android app           |
| (planned client)      |
+-----------+-----------+
            | HTTP / JSON / multipart
            v
+-----------------------+
| FastAPI + JWT         |
| app/main.py + routers |
+-----+-----------+-----+
      |           |
      v           v
  SQLite       ChromaDB
 auramed.db   patient-filtered
      |       report chunks
      |           |
      +-----+-----+
            v
       Ollama
     llama3.1:8b
```

Uploaded and seeded PDF files are stored under `uploads/` and `reports/`. The backend exposes these directories as static mounts at `/uploads` and `/reports`.

## Project structure

```text
AuraMed/
├── app/
│   ├── main.py                 # FastAPI application and static-file mounts
│   ├── api/                    # Health, authentication, patient, and report routers
│   ├── core/                   # Settings, JWT security, and audit logging
│   ├── db/                     # Session plus table, seed, reset, and RAG scripts
│   ├── models/                 # SQLAlchemy patient, hospital, report, OTP, and audit models
│   ├── rag/                    # PDF extraction, chunking, embeddings, retrieval, and LLM calls
│   └── schemas/                # Pydantic request and response schemas
├── reports/                    # Seeded report PDFs (created by seed scripts)
├── uploads/                    # Hospital-uploaded report files
├── chroma_db/                  # Persistent ChromaDB data (ignored by Git)
├── auramed.db                 # Local SQLite database (ignored by Git)
├── requirements.txt            # Python dependencies
├── AuraMed_Full_Build_Roadmap.md
└── AuraMed_Phase5_Android_Skeleton_Prompts.md
```

## Getting started

### Prerequisites

- Python 3.10 or newer. The checked-in development environment currently uses Python 3.10.11.
- Ollama installed and available on `PATH`.
- The local model downloaded:

  ```powershell
  ollama pull llama3.1:8b
  ```

- Android Studio if working on the planned Android client.
- Postman is useful for exercising the API manually.

### Backend setup

From the repository root, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` from [`.env.example`](./.env.example) and replace the JWT, seeded
hospital-key, and seeded phone-number placeholders with local development
values. `.env` is ignored by Git.

Create the tables and seed the development patients, hospitals, and reports:

```powershell
python -m app.db.create_tables
python -m app.db.seed
python -m app.db.seed_patient_reports
```

Start the API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To build or rebuild the RAG index from report files already referenced by the database:

```powershell
python -m app.db.backfill_rag
```

To generate a new hospital key, do not place a plaintext key in source control. Run the reset script with an exact hospital name or numeric ID and store the one-time output securely:

```powershell
python -m app.db.reset_hospital_key --name "AuraMed General Hospital"
# or
python -m app.db.reset_hospital_key --id 1
```

### Android setup

The Android source is not included in this checkout. When the separate Android project is available, open it in Android Studio and run it on an emulator. For a local backend, reverse the port after every emulator restart:

```powershell
adb reverse tcp:8000 tcp:8000
```

### Development test credentials

The seed script creates these patient codes:

- `AURAMED-P-10234`
- `AURAMED-P-10235`
- `AURAMED-P-10236`

Use the phone number associated with each seeded patient when calling `POST /auth/user/request-otp`. The development OTP is printed to the Uvicorn/backend console; it is not delivered by SMS. Hospital keys are generated or replaced with `app.db.reset_hospital_key` as described above.

## API overview

All protected endpoints use `Authorization: Bearer <JWT>`. The patient and hospital role required for each endpoint is shown below.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check. |
| `POST` | `/auth/user/request-otp` | None | Validate patient code and phone number, create a development OTP, and print it to the server console. |
| `POST` | `/auth/user/verify-otp` | None | Verify the latest OTP and issue a patient JWT. |
| `POST` | `/auth/hospital/login` | None | Validate a hospital key and issue a hospital JWT. |
| `GET` | `/patients/me` | Patient | Return the authenticated patient's basic identity. |
| `GET` | `/patients/{patient_code}` | None | Look up a patient and return a masked name. |
| `GET` | `/patients/me/reports` | Patient | List the authenticated patient's reports, newest first. |
| `GET` | `/patients/me/summary` | Patient | Generate a local-LLM summary from that patient's retrieved report chunks. |
| `GET` | `/patients/me/extracted-data` | Patient | Return AI-extracted allergies, conditions, medications, history, and vitals. |
| `GET` | `/reports/{report_id}` | Patient | Return one report's metadata when it belongs to the authenticated patient. |
| `GET` | `/hospitals/patients/{patient_code}` | Hospital | Look up a patient for hospital workflows. |
| `POST` | `/hospitals/patients/{patient_code}/reports` | Hospital | Upload a report using multipart `report_type`, `title`, and `file` fields; ingest PDF text into the RAG index when possible. |
| `POST` | `/patients/{patient_code}/retrieve` | Patient or Hospital | Run a patient-scoped vector search with JSON body `{"query": "..."}`. Patients may retrieve only their own chunks. |
| `GET` | `/reports/...` | None | Static access to files under the `reports/` directory. |
| `GET` | `/uploads/...` | None | Static access to files under the `uploads/` directory. |

## Roadmap

### Done in the current backend

- FastAPI service with health, patient, hospital, report, and authentication routers.
- SQLite/SQLAlchemy persistence and development seed scripts.
- Patient and hospital JWT role separation.
- PDF ingestion, local embeddings, ChromaDB retrieval, recency-aware prompting, summaries, and structured extraction.
- Report upload and audit logging.

### Planned

- Android client integration and replacement of mock UI flows with API calls.
- AI chat assistant.
- Security hardening and production-grade rate limiting/secrets management.
- Automated unit, integration, and end-to-end testing.
- Demo deployment and production readiness work.
- NFC patient-card integration.
- A real SMS gateway for OTP delivery.

## Disclaimer

AuraMed's AI output is not medical advice and is not a substitute for a qualified clinician. Always verify extracted information and summaries with an appropriate healthcare professional. All sample patient and report data in the development fixtures is fictional.
