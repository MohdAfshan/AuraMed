# AuraMed — Full Build Roadmap
## Working order across Android Studio, VS Code, and Postman

This replaces the earlier generic phase list with the **actual sequence you'll work in**, given your two-app split:

- **Android Studio** → AuraMed Android app (Kotlin, UI, NFC later)
- **VS Code** → FastAPI backend, database, auth logic, RAG, LLM
- **Postman** → testing backend APIs before/while wiring them into the app
- **Git/GitHub** → used throughout both sides; commit at the end of every stage below

General rhythm you'll notice: **build a backend piece in VS Code → test it in Postman → go to Android Studio and replace the matching mock data with a real API call.** This keeps the app always running end-to-end instead of building both sides in isolation and integrating at the very end.

---

## Stage 1 — Android App Skeleton/UI ✅ (already done)
**Tool:** Android Studio
Covered in the previous doc (`AuraMed_Phase5_Android_Skeleton_Prompts.md`) — full navigable UI with mock data, no backend yet.

---

## Stage 2 — Backend Project Foundations
**Tool:** VS Code

**What this stage is:** Stand up the FastAPI project itself — structure, config, and a running "hello world" server — before any real feature is built.

**Your part:** Install Python (3.11+ recommended), create a virtual environment, install FastAPI + Uvicorn, decide on Postgres vs SQLite for now (SQLite is fine for local dev, Postgres if you want it production-realistic from day one). Have Postman installed and ready.

**Stepwise prompts (Claude Code in VS Code):**
```
Step 1: Set up a new FastAPI project called "auramed-backend" with a virtual environment. Create this folder structure: app/main.py, app/api/ (routers), app/models/ (DB models), app/schemas/ (Pydantic schemas), app/core/ (config, security), app/db/ (database session setup). Add a requirements.txt with fastapi, uvicorn, sqlalchemy, pydantic, python-dotenv. Create a basic health-check endpoint GET /health returning {"status": "ok"}. Confirm the server runs with uvicorn and the endpoint responds.
```
```
Step 2: Set up SQLAlchemy database configuration in app/db/. Use SQLite for local development (file-based, e.g. auramed.db) with an easy switch to Postgres later via an environment variable DATABASE_URL. Create a base declarative model class and a get_db dependency for FastAPI routes. Confirm the app still starts cleanly with this DB layer wired in but no tables yet.
```
```
Step 3: Set up a .env file and app/core/config.py using pydantic-settings to load environment variables (DATABASE_URL, SECRET_KEY, OTP_EXPIRY_SECONDS, etc. — add placeholders for values we'll need later). Add .env to .gitignore. Initialize a git repository if not already done, and make an initial commit.
```

**What to expect after this stage:** A running FastAPI server on localhost with a health-check endpoint, proper folder structure, DB connection ready but empty, and a git repo. Nothing in the Android app changes yet.

---

## Stage 3 — Core Database Models
**Tool:** VS Code

**What this stage is:** Define the actual data models the whole system will hinge on — before writing any endpoint logic.

**Your part:** Review the schema Claude Code proposes and confirm it matches the field lists from your project description (medical record types, patient/hospital fields, etc.) before moving on.

**Stepwise prompts:**
```
Step 1: In app/models/, create SQLAlchemy models for: Patient (id, patient_code e.g. "AURAMED-P-10234", full_name, phone_number, created_at), Hospital (id, name, hashed_key, created_at), MedicalReport (id, patient_id FK, hospital_id FK, report_type enum [BLOOD, ECG, XRAY, CT, MRI, PRESCRIPTION, LAB, DIAGNOSIS, OTHER], title, file_path, created_at), AuthOtp (id, patient_id FK, otp_code, expires_at, verified boolean). Create the corresponding Pydantic schemas in app/schemas/ for request/response bodies. Do not create any API routes yet — just models and schemas. Generate a script or use Alembic to create these tables in the local database, and confirm the tables exist.
```
```
Step 2: Write a small seed script (app/db/seed.py) that inserts 2-3 mock patients, 1-2 mock hospitals (with a known plaintext key for testing, stored hashed), and a few mock medical reports linking them. Run it and confirm the data is in the database via a quick query or DB browser.
```

**What to expect after this stage:** A real local database with realistic test data — patients, hospitals, and reports — ready for the API layer to query.

---

## Stage 4 — Patient Identification API
**Tool:** VS Code → test in Postman

**What this stage is:** The first real endpoint — given a Patient ID (what would come from the NFC card), look up the patient.

**Your part:** Test the endpoint in Postman with the mock Patient IDs from your seed data (valid and invalid) before moving to Android.

**Stepwise prompts:**
```
Step 1: Create an API router app/api/patients.py with GET /patients/{patient_code}. It should look up the patient by patient_code and return basic non-sensitive identification info (id, patient_code, full_name masked or partial) if found, or a 404 with a clear error message if not. Wire this router into main.py. Confirm it works by calling it manually.
```

**Your part now:** Open Postman, create a collection "AuraMed API", add a GET request to `http://localhost:8000/patients/AURAMED-P-10234` (use your real seeded code) and confirm you get a valid response, then test a nonexistent code and confirm the 404.

**What to expect after this stage:** A working, testable Patient ID lookup endpoint. Still no connection to the Android app yet.

---

## Stage 5 — Connect Android Patient ID Screen to Real Backend
**Tool:** Android Studio

**What this stage is:** Replace the mock "accept any ID" logic in the PatientIdEntry screen with a real network call to Stage 4's endpoint.

**Your part:** Make sure your phone/emulator can reach your laptop's server (same Wi-Fi network, use your laptop's local IP, not localhost, when testing on a real device; 10.0.2.2 for emulator). Have the FastAPI server running while testing.

**Stepwise prompts:**
```
Step 1: Add Retrofit and OkHttp dependencies to the Android app. Create a network package with an ApiService interface declaring GET patients/{patientCode}, a Retrofit instance builder with a configurable base URL, and a repository class wrapping the call with basic error handling (network error, 404, success).
```
```
Step 2: Update the PatientIdEntry screen's ViewModel to call this repository instead of accepting any input. Show a loading state while the call is in flight, an inline error message on 404/network failure, and navigate to AuthSelection with the confirmed patient info only on success.
```

**What to expect after this stage:** Scanning/entering a real seeded Patient ID in the app now actually validates against your backend. Invalid IDs correctly show an error instead of proceeding.

---

## Stage 6 — User Authentication Backend (Phone + OTP)
**Tool:** VS Code → test in Postman

**What this stage is:** The patient login flow's backend half.

**Your part:** Since you don't have a real SMS gateway yet, decide now: print the OTP to the server console/logs for dev testing (recommended for now), or stub in a free-tier SMS API later. Test the whole request-OTP → verify-OTP cycle in Postman first.

**Stepwise prompts:**
```
Step 1: Create app/api/auth_user.py with POST /auth/user/request-otp (body: patient_code, phone_number). It should verify the phone number matches the patient's registered number, generate a 6-digit OTP, store it in AuthOtp with an expiry (use OTP_EXPIRY_SECONDS from config), and for now print it to the console/logs instead of sending a real SMS. Return a generic success message without leaking the OTP in the response.
```
```
Step 2: Add POST /auth/user/verify-otp (body: patient_code, otp_code). It should check the OTP matches, hasn't expired, and hasn't been used, then mark it verified and issue a JWT access token scoped to that patient with a "role: patient" claim. Return the token. Add basic rate-limiting or attempt-counting so repeated wrong OTPs are throttled.
```

**Your part:** In Postman, call request-otp, check your server console for the printed OTP, then call verify-otp with that code and confirm you get back a JWT token. Also test a wrong OTP and confirm it's rejected.

**What to expect after this stage:** A working, console-logged OTP login flow returning real auth tokens, fully testable without needing a real SMS provider yet.

---

## Stage 7 — Hospital Authentication Backend (Key-Based)
**Tool:** VS Code → test in Postman

**What this stage is:** The hospital login flow's backend half.

**Your part:** After Claude Code creates a hospital, note down the plaintext key it gives you once (mirroring your real design — key is issued once) so you can use it in Postman/Android testing.

**Stepwise prompts:**
```
Step 1: Create app/api/auth_hospital.py with POST /auth/hospital/login (body: hospital_key). It should compare the provided key against stored hashed keys (using a secure comparison, e.g. bcrypt or argon2 verify), and if valid, issue a JWT with "role: hospital" and the hospital's id. Return 401 with no detail on mismatch (don't reveal whether the key format was wrong vs. not found).
```
```
Step 2: Create an admin-only script or endpoint (not exposed to the public app) to generate a new hospital + a one-time plaintext key, print the plaintext key once, and store only its hash. Run it to create a test hospital and note the printed key.
```

**Your part:** Test /auth/hospital/login in Postman with the noted key, confirm you get a JWT, and confirm a wrong key is rejected.

**What to expect after this stage:** Both auth paths (patient OTP, hospital key) are fully working and testable via Postman, independent of the Android app.

---

## Stage 8 — Connect Android Auth Screens to Real Backend
**Tool:** Android Studio

**What this stage is:** Wire the UserAuthPhone/OTP screens and HospitalAuthKey screen to Stages 6 & 7.

**Your part:** Keep the FastAPI server console visible while testing so you can read the printed OTP and type it into the app manually.

**Stepwise prompts:**
```
Step 1: Extend the ApiService and repository from Stage 5 with the request-otp, verify-otp, and hospital-login endpoints. Add a secure local token store (EncryptedSharedPreferences or DataStore) to hold the JWT once issued, plus the "role" it corresponds to.
```
```
Step 2: Wire UserAuthPhone's "Send OTP" button to the request-otp call (with loading/error states), and UserAuthOtp's "Verify" button to the verify-otp call, storing the returned token and navigating to Dashboard only on success. Wire HospitalAuthKey's "Authenticate" button the same way against hospital-login.
```
```
Step 3: Add an authenticated HTTP client (Retrofit with an auth interceptor) that automatically attaches the stored JWT as a Bearer token to all future API calls, so later stages don't need to repeat this wiring.
```

**What to expect after this stage:** Real login works end to end — enter a seeded Patient ID, request an OTP, read it from your server console, verify it, and land on the Dashboard with a real session. Hospital login works the same way with a real key.

---

## Stage 9 — Authorization & Access Control
**Tool:** VS Code

**What this stage is:** Backend-side enforcement so tokens actually restrict what each role can do — this is invisible in the UI but critical.

**Your part:** Try to "break" it afterward — attempt a patient-token request against a hospital-only endpoint via Postman and confirm it's rejected.

**Stepwise prompts:**
```
Step 1: Create a reusable FastAPI dependency (e.g. get_current_patient, get_current_hospital) that decodes the JWT from the Authorization header, validates it, and returns the associated identity — raising 401/403 on invalid, expired, or wrong-role tokens.
```
```
Step 2: Retrofit the patient lookup endpoint (and any future patient/hospital endpoints) to require the appropriate dependency, and add a check that a patient token can only access that same patient's own data (never another patient's), and a hospital token's write operations are scoped to hospitals only.
```
```
Step 3: Add an audit log table/model that records every access/modification event (who, what, when, which patient record) for later review.
```

**Your part:** In Postman, try calling a protected endpoint with no token, an expired token, and a token for the wrong role — confirm each is correctly rejected.

**What to expect after this stage:** The backend now actively enforces the "patient reads own data only, hospital writes only" rule at the API layer, not just hidden in the UI. Nothing visibly changes in the app yet.

---

## Stage 10 — Medical Records Management API
**Tool:** VS Code → test in Postman

**What this stage is:** Real endpoints for listing, viewing, and (for hospitals) uploading medical reports.

**Your part:** Have a couple of sample files (PDF/image) ready to test file upload in Postman.

**Stepwise prompts:**
```
Step 1: Create app/api/reports.py with GET /patients/me/reports (patient-only, returns list of the authenticated patient's reports) and GET /reports/{report_id} (patient-only, returns full report metadata + file path/URL, only if it belongs to them).
```
```
Step 2: Add POST /hospitals/patients/{patient_code}/reports (hospital-only) accepting multipart form data: report_type, title, and a file upload. Store the file to a local "uploads/" directory (organized by patient_code) and create the corresponding MedicalReport row.
```
```
Step 3: Add GET /hospitals/patients/{patient_code} (hospital-only) for the hospital's patient lookup screen, returning basic patient identification info if the hospital is authorized to view them.
```

**Your part:** In Postman, using the hospital token, upload a test report for a seeded patient; then using that patient's token, call the list/view endpoints and confirm the uploaded report appears.

**What to expect after this stage:** Full read/write cycle for medical reports works via API, independent of the app UI.

---

## Stage 11 — Connect Android Dashboard & Hospital Screens to Real Backend
**Tool:** Android Studio

**What this stage is:** Replace all remaining mock data in the Dashboard, ReportViewer, HospitalPatientLookup, and HospitalUploadReport screens with real API calls from Stage 10.

**Stepwise prompts:**
```
Step 1: Extend the repository/API service with the reports-list, report-detail, hospital-patient-lookup, and hospital-upload-report endpoints (multipart request for the upload).
```
```
Step 2: Wire the Dashboard's left ReportsListPanel to fetch and display the authenticated patient's real reports instead of the mock list, with loading and empty states. Wire ReportViewer to fetch real report details/content by id.
```
```
Step 3: Wire HospitalPatientLookup to call the real lookup endpoint, and HospitalUploadReport's Submit button (including the file picker, which now needs real Android file/image picking logic) to call the real multipart upload endpoint, showing success/error feedback.
```

**What to expect after this stage:** The entire records flow is real — a hospital can log in, look up a patient, upload a report; the patient can log in and immediately see it in their dashboard and open it. The AI summary panel and chat are still mock at this point — that's the next stage.

---

## Stage 12 — RAG Pipeline (Document Processing & Retrieval)
**Tool:** VS Code

**What this stage is:** The infrastructure that turns uploaded reports into retrievable knowledge, built and tested independently before wiring it to any user-facing endpoint.

**Your part:** Decide on a vector DB now if you haven't — Chroma is the easiest to run fully local with no extra server. Decide on an embedding model (an API-based embedding model, or a local sentence-transformers model if you want to avoid API costs during dev).

**Stepwise prompts:**
```
Step 1: Add a RAG module (app/rag/) with: a text-extraction function that pulls text from uploaded report files (PDF text extraction, OCR fallback for images using a library like pytesseract), and a chunking function that splits extracted text into overlapping chunks suitable for embedding.
```
```
Step 2: Set up Chroma (or your chosen vector DB) running locally, with a collection-per-patient or a metadata field for patient_id so retrieval can be filtered per patient. Write an embedding function (via your chosen embedding model) and a function to upsert chunks into the vector DB whenever a new report is processed.
```
```
Step 3: Hook this pipeline into the report upload flow from Stage 10: after a hospital uploads a report, automatically run extraction → chunking → embedding → vector DB upsert as a background step (can be synchronous for now, async/queued later).
```
```
Step 4: Write a standalone retrieval function retrieve_relevant_chunks(patient_id, query, top_k) that queries the vector DB filtered to that patient only, and returns the matching chunks with their source report id. Test this directly (a quick script or a temporary debug endpoint) with a sample query against your seeded/uploaded reports.
```

**What to expect after this stage:** You can feed the pipeline a natural-language query plus a patient id and get back relevant, correctly-isolated chunks from that patient's reports — verified independent of any LLM or UI. This is the riskiest technical stage; expect to iterate on chunking/retrieval quality here.

---

## Stage 13 — AI Summary Generation API
**Tool:** VS Code → test in Postman

**What this stage is:** Wrap the RAG retrieval with an LLM call to produce the dashboard's auto-summary.

**Your part:** Decide which LLM API you're calling and get an API key set up in your .env.

**Stepwise prompts:**
```
Step 1: Create app/api/summary.py with GET /patients/me/summary (patient-only). It should retrieve a broad set of relevant chunks across the patient's reports (e.g. a fixed set of retrieval queries like "conditions", "medications", "allergies", "recent results", or a single broad retrieval call), pass them to an LLM with a system prompt instructing it to produce a concise, clearly-sourced clinical summary and explicitly avoid unsupported claims, and return the generated summary text plus which report ids it drew from.
```
```
Step 2: Add basic caching (store the generated summary with a timestamp, regenerate only when a new report is added for that patient rather than on every request) to avoid unnecessary LLM calls.
```

**Your part:** Test in Postman with a patient token and confirm the summary reads sensibly and references your seeded/uploaded report content.

**What to expect after this stage:** A real, grounded AI summary endpoint, independently testable.

---

## Stage 14 — AI Assistant (Chat) API
**Tool:** VS Code → test in Postman

**What this stage is:** The conversational Q&A endpoint behind the chat icon.

**Stepwise prompts:**
```
Step 1: Create app/api/assistant.py with POST /patients/me/assistant/chat (patient-only, body: message, optional conversation history). It should retrieve relevant chunks for that specific query (using the retrieval function from Stage 12), construct a prompt that includes the retrieved context, the conversation history, and a system prompt establishing the clinical-decision-support framing (no autonomous diagnosis, flag uncertainty, cite which report information came from), call the LLM, and return the response plus source report references.
```
```
Step 2: Add guardrail handling for safety-sensitive query patterns (e.g. medication/allergy conflict questions) — instruct the LLM explicitly in the system prompt to be conservative and recommend consulting a clinician for anything beyond what the records directly support.
```

**Your part:** Test several of the example queries from your original spec in Postman (conditions, medications, allergies, emergency-relevant questions) against a patient with real seeded/uploaded data, and sanity-check the tone and groundedness of responses.

**What to expect after this stage:** A working, source-grounded chat endpoint, independently testable before the UI is wired to it.

---

## Stage 15 — Connect Android AI Summary & Assistant to Real Backend
**Tool:** Android Studio

**What this stage is:** Final mock-data removal — the centre summary panel and chat screen go live.

**Stepwise prompts:**
```
Step 1: Wire the Dashboard's AiSummaryPanel to fetch from the real summary endpoint instead of showing mock text, with a loading state and a fallback message if no reports exist yet.
```
```
Step 2: Wire the AssistantChat screen's send action to call the real chat endpoint instead of echoing a canned reply, sending along conversation history, and rendering the returned source references (e.g. small "from: Blood Report, 12 Jan" tags under assistant messages).
```

**What to expect after this stage:** The app has zero mock data left. Every screen is now backed by the real FastAPI system end to end — this is your first fully-functional version of AuraMed (software-only, no real NFC/SMS yet).

---

## Stage 16 — Security Hardening
**Tool:** VS Code (+ Android Studio for a couple of client-side items)

**What this stage is:** A dedicated pass to tighten what was left loose for speed during earlier stages.

**Your part:** This stage is more review/decision-making than pure code generation — read through what Claude Code changes carefully, since it touches auth and data protection.

**Stepwise prompts:**
```
Step 1: Enforce HTTPS/TLS for all API traffic (self-signed cert acceptable for local dev, with a plan to swap in a real cert later), review JWT expiry times and add refresh-token handling if access tokens are short-lived, and confirm all sensitive config (secret keys, DB credentials, LLM API keys) is only in .env / environment variables, never hardcoded.
```
```
Step 2: Add server-side input validation and rate-limiting across all auth endpoints (OTP request/verify, hospital login) to prevent brute-force attempts. Review file upload handling for basic safety (file type/size limits).
```
```
Step 3: In the Android app, confirm the JWT is stored using EncryptedSharedPreferences/DataStore (not plain SharedPreferences), and that no sensitive data is logged (remove or guard any Log.d calls printing tokens, OTPs, or patient data).
```

**What to expect after this stage:** The same functionality as Stage 15, but noticeably more resistant to casual attack — appropriate before you'd trust it with any real personal data, even in testing.

---

## Stage 17 — End-to-End Testing & QA
**Tool:** Android Studio + VS Code + Postman

**What this stage is:** Systematic testing rather than ad-hoc manual checks.

**Your part:** Actually run through the test scenarios yourself at least once manually, in addition to what Claude Code automates — this is where you'll catch UX issues no automated test will flag.

**Stepwise prompts:**
```
Step 1 (VS Code): Write backend unit tests (pytest) covering: OTP generation/expiry/verification logic, hospital key hashing/verification, patient data isolation (a token for Patient A cannot fetch Patient B's reports/summary), and the retrieval function's per-patient filtering.
```
```
Step 2 (VS Code): Write integration tests hitting the FastAPI test client for the full flows: patient lookup → OTP login → fetch reports → fetch summary → chat; and hospital login → patient lookup → upload report → confirm it appears for the patient.
```
```
Step 3 (Android Studio): Add basic instrumented/UI tests for the critical navigation path (Landing → PatientIdEntry → Auth → Dashboard) and for form validation on the OTP and upload screens.
```

**Your part:** Manually run through: a full patient session, a full hospital session, and at least one deliberate "wrong password/OTP/ID" path per screen, noting anything that feels off.

**What to expect after this stage:** Confidence the system behaves correctly and isolates data properly, backed by a real (if modest) automated test suite.

---

## Stage 18 — Demo & Local Deployment Packaging
**Tool:** VS Code (+ Android Studio for a release build)

**What this stage is:** Making the whole thing easy to spin up and show, not adding new features.

**Stepwise prompts:**
```
Step 1: Add a README to the backend repo with setup instructions (env vars needed, how to run migrations/seed data, how to start the server), and optionally a docker-compose.yml if you want one-command startup for the DB + backend.
```
```
Step 2: Write a short demo script/checklist (which patient/hospital test accounts to use, in what order) that walks through the full flow for a live demo.
```
```
Step 3 (Android Studio): Build a debug/release APK configured to point at your laptop's local IP for the demo, and confirm it installs and runs on a physical device on the same network.
```

**What to expect after this stage:** A repeatable, presentable, fully-working local demo of the entire software system — this is the natural point to pause and show the project to others before touching hardware.

---

## Stage 19 (Later) — Hardware / Physical NFC Integration
**Tool:** Android Studio

Deferred as agreed. When you're ready, this stage will cover: Android NFC API integration to replace the manual Patient ID entry screen, programming physical NFC tags with the Patient ID format, and real-world read-reliability testing. We'll write its stepwise prompts when you get here.

## Stage 20 (Future) — Production Readiness
**Tool:** Both

Deferred. Covers moving off your laptop to real hosting, a real SMS gateway for OTP, scaling considerations, and formal compliance review — only relevant once you're past a working local prototype.

---

**You are here:** Stage 1 is complete. Stage 2 (backend project foundations, VS Code) is next.
