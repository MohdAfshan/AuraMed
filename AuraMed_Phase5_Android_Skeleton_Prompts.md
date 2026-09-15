# AuraMed — Phase 5: Android App Skeleton/UI
## Stepwise Prompts for Claude Code (Android Studio)

**How to use this doc:** Work top to bottom. Copy each "Prompt" block as-is into Claude Code inside Android Studio, let it complete the step, verify the build runs, then move to the next. Don't skip ahead — each step assumes the previous ones exist. No backend calls yet in this phase; everything is UI + navigation skeleton with mock/hardcoded data, since backend (FastAPI) comes in a later phase.

Stack assumed: Kotlin, Jetpack Compose, single-activity architecture, Navigation-Compose.

---

### Step 1 — Project Setup & Package Structure

**Goal:** Clean Kotlin/Compose project with the right module structure before any screens exist.

**Prompt:**
```
Set up a new Android project (or configure the existing one) called "AuraMed" using Kotlin and Jetpack Compose. Use single-activity architecture with Navigation-Compose for screen navigation. Create the following package structure under the app module:
- ui.screens (for each screen's Composable)
- ui.components (shared reusable Composables)
- ui.theme (colors, typography, shapes)
- navigation (NavHost + route definitions)
- model (data classes, no backend logic yet)
- viewmodel (empty ViewModel classes, one per screen, no logic yet)

Set minSdk to 26, targetSdk to latest stable. Add dependencies for Navigation-Compose, Material3, and lifecycle-viewmodel-compose. Do not add networking or NFC dependencies yet. Confirm the project builds and runs showing a blank default screen.
```

---

### Step 2 — Navigation Graph (Route Skeleton)

**Goal:** Define all screen routes and wire an empty NavHost before building any screen content.

**Prompt:**
```
In the navigation package, define a sealed class or enum "AuraMedRoute" listing all screens: Landing, PatientIdEntry, AuthSelection, UserAuthPhone, UserAuthOtp, HospitalAuthKey, Dashboard, ReportViewer, HospitalPatientLookup, HospitalUploadReport. Create a NavHost composable wiring these routes to placeholder Composables (each just a Text() showing the screen name for now). Set Landing as the start destination. Confirm navigation between all placeholder screens works via simple "Next" buttons for now.
```

---

### Step 3 — Landing Screen

**Goal:** First screen shown on app open — entry point into the "scan card" flow (simulated NFC).

**Prompt:**
```
Build the Landing screen composable. It should show the AuraMed app name/logo placeholder, a short tagline, and a single primary button labeled "Scan Patient Card". Tapping it navigates to the PatientIdEntry screen. Keep styling simple and centered using Material3 components. No logic beyond navigation.
```

---

### Step 4 — Simulated NFC / Patient ID Entry Screen

**Goal:** Stand-in for the real NFC scan (added in the hardware phase later). For now, manual entry simulates reading a card.

**Prompt:**
```
Build the PatientIdEntry screen composable. It should simulate an NFC scan since real NFC hardware isn't integrated yet. Show a text field for entering a Patient ID manually (placeholder text "e.g. AURAMED-P-10234"), and a button "Continue". For now, accept any non-empty input as valid and navigate to AuthSelection, passing the entered Patient ID forward via the nav back stack's SavedStateHandle or a shared ViewModel. Add a small note on screen: "NFC scanning will be added later — enter ID manually for testing."
```

---

### Step 5 — Auth Selection Screen (User vs Hospital)

**Goal:** Branch point between the two authentication flows.

**Prompt:**
```
Build the AuthSelection screen composable. Display the Patient ID received from the previous screen (read-only, for context). Show two large buttons: "I'm the Patient" and "I'm a Hospital". Tapping "I'm the Patient" navigates to UserAuthPhone. Tapping "I'm a Hospital" navigates to HospitalAuthKey. No backend logic — just navigation and passing the Patient ID forward.
```

---

### Step 6 — User Auth: Phone Number Entry

**Goal:** First step of patient authentication.

**Prompt:**
```
Build the UserAuthPhone screen composable. Show a text field for entering a phone number (numeric keyboard, basic format validation for length only), and a button "Send OTP". On tap, since there's no backend yet, just navigate to UserAuthOtp and pass the phone number forward via shared ViewModel state. Show a loading spinner placeholder state (not wired to real logic yet) to represent where the OTP-request API call will go later.
```

---

### Step 7 — User Auth: OTP Entry

**Goal:** Second step of patient authentication.

**Prompt:**
```
Build the UserAuthOtp screen composable. Show a 6-digit OTP input (individual boxes or a single text field, your choice), a "Verify" button, and a "Resend OTP" text link (non-functional placeholder for now). On tapping "Verify", navigate to the Dashboard screen — no real verification logic yet, just accept any 6-digit input for skeleton purposes. Add a comment in the code marking where the real OTP verification API call will be inserted later.
```

---

### Step 8 — Hospital Auth: Key Entry

**Goal:** Authentication path for hospital staff.

**Prompt:**
```
Build the HospitalAuthKey screen composable. Show a secure text field (password-style masking) for entering the hospital's unique authentication key, and a "Authenticate" button. On tap, navigate to a hospital-specific landing point — for now route to HospitalPatientLookup. No real validation yet; mark with a code comment where the backend key-verification call will go later.
```

---

### Step 9 — Dashboard Shell (Layout Skeleton)

**Goal:** The three-zone dashboard layout structure, before filling in real content.

**Prompt:**
```
Build the Dashboard screen composable with a layout skeleton matching this structure:
- Left side (roughly 30% width or a collapsible panel): a placeholder list area labeled "Medical Reports"
- Centre (main remaining space): a placeholder card labeled "AI Medical Summary"
- Bottom-right corner: a floating action button (chat/robot icon) labeled conceptually as the "AI Assistant" entry point
Use a Scaffold with the FAB in the bottomEnd position. For now, each zone just shows static placeholder text/mock data (e.g. 3 fake report names in the left list, a lorem-ipsum style paragraph in the centre summary card). Tapping the FAB should navigate to a not-yet-built "AssistantChat" placeholder screen (add this route now). Tapping a report in the left list should navigate to ReportViewer.
```

---

### Step 10 — Reports List (Left Panel) with Mock Data

**Goal:** Flesh out the left panel as its own reusable component with a mock data model.

**Prompt:**
```
Create a data class "MedicalReportSummary" in the model package with fields: id, title, type (enum: BLOOD, ECG, XRAY, CT, MRI, PRESCRIPTION, LAB, DIAGNOSIS, OTHER), date. Create a mock list of 5-6 sample reports covering different types. Build a reusable Composable "ReportsListPanel" that takes this list and an onReportClick callback, rendering each as a clickable card/row with an icon representing its type, title, and date. Wire this into the Dashboard's left panel, replacing the earlier static placeholder, using the mock list. Clicking a report navigates to ReportViewer passing the report id.
```

---

### Step 11 — AI Summary Panel (Centre) with Mock Data

**Goal:** Visual placeholder for the future RAG-generated summary.

**Prompt:**
```
Build a reusable Composable "AiSummaryPanel" that displays a card with a header "AI-Generated Summary" and a body of mock summary text (a realistic-looking but clearly fake paragraph about a patient's conditions, medications, and allergies). Include a small "Generated from N reports" caption at the bottom and a placeholder timestamp. Wire this into the Dashboard's centre area, replacing the earlier static placeholder. Leave a comment marking where the real RAG/LLM call will replace the mock text later.
```

---

### Step 12 — Report Viewer Screen

**Goal:** Screen to view an individual report's content.

**Prompt:**
```
Build the ReportViewer screen composable. It should receive a report id argument via navigation, look it up in the same mock report list (move the mock list to a shared location like a fake repository object if needed), and display: the report title, type, date, and a placeholder content area (mock text or a placeholder image depending on type) representing where the real report content/file will render later. Add a back button to return to the Dashboard.
```

---

### Step 13 — AI Assistant Chat Screen (Placeholder)

**Goal:** Chat UI skeleton for the future LLM-backed assistant.

**Prompt:**
```
Build the AssistantChat screen composable (the destination from the Dashboard's FAB). Create a basic chat UI: a scrollable list of message bubbles (user messages right-aligned, assistant messages left-aligned), a text input field at the bottom with a send button. On send, for now just echo the user's message back as a hardcoded canned assistant reply (e.g. "This is a placeholder response — AI integration comes later.") so the UI is testable without a backend. Use local Compose state to hold the message list; no persistence needed yet.
```

---

### Step 14 — Hospital-Side Screens: Patient Lookup

**Goal:** Entry screen for hospital staff to find a patient after authenticating.

**Prompt:**
```
Build the HospitalPatientLookup screen composable. Show a search field to enter a Patient ID, a "Search" button, and (using mock data) display a simple result card showing the patient's name and ID if it matches a hardcoded mock patient list, or a "Not found" message otherwise. Add a button "Upload New Report" on the result card that navigates to HospitalUploadReport, passing the patient id forward.
```

---

### Step 15 — Hospital-Side Screens: Upload Report Form

**Goal:** Form skeleton for hospitals adding a new medical report.

**Prompt:**
```
Build the HospitalUploadReport screen composable. Show a form with: a dropdown/selector for report type (reuse the MedicalReportSummary type enum), a text field for report title, a date picker for report date, and a file/image picker placeholder button (just a button labeled "Attach File" that doesn't need real file-picking logic yet). Add a "Submit" button that, for now, just shows a success Snackbar/Toast and navigates back to HospitalPatientLookup — no real upload logic yet. Leave a comment marking where the backend upload API call will be inserted later.
```

---

### Step 16 — Shared ViewModel & State Wiring Pass

**Goal:** Consolidate the ad-hoc state passed between screens into proper ViewModels before moving to backend integration.

**Prompt:**
```
Review all screens built so far (Landing through HospitalUploadReport) and refactor state management: create a shared "SessionViewModel" (scoped to the nav graph) holding the current Patient ID, auth role (User/Hospital), and auth status as StateFlow. Replace any ad-hoc SavedStateHandle passing between screens with reads/writes to this shared ViewModel where appropriate. Keep screen-local form state (like text field values) in per-screen ViewModels or local remember state as appropriate. Confirm the full navigation flow still works end to end after refactoring: Landing → PatientIdEntry → AuthSelection → (User or Hospital path) → Dashboard → sub-screens.
```

---

### Step 17 — Visual Pass (Theming & Polish)

**Goal:** Make the skeleton look like a coherent app, not a wireframe, before backend work begins.

**Prompt:**
```
Apply a consistent Material3 theme across the app: define a color scheme (light + dark) appropriate for a medical/clinical app (calming blues/teals, clear contrast for readability), consistent typography scale, and consistent spacing/padding across all screens built so far. Do not change any navigation logic or data flow — this is a visual-only pass. Confirm all screens still function identically after the styling pass.
```

---

## End of Phase 5

At this point you should have a fully navigable, visually coherent Android app skeleton with mock data throughout — no backend, no NFC, no real AI. This becomes the shell that Phase 6 (RAG pipeline) and later backend-integration phases will plug real functionality into.

Next up when you're ready: **Phase 0/backend** — setting up the FastAPI server, database schema, and the API contract this app will eventually call (replacing the mock data step by step).
