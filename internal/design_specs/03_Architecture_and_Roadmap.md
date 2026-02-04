# SIMAD oLearn: System Architecture & Roadmap

**Version:** 1.0  
**Status:** Draft  
**Confidentiality:** Internal Use Only - SIMAD University  

---

## 5. High-Level System Architecture

### Conceptual Framework
The system is built on a **Microservices Architecture** to ensure independent scalability of the Learning core and the Proctoring engine.

### Component Diagram

1.  **Frontends (Client Layer)**
    *   **Web App (React/Next.js):** Primary interface for Students, Faculty, and Admins.
    *   **Secure Exam Client (Electron + Native Modules):** The "Exam Shield" desktop application for locked-down high-stakes testing.
    *   **Mobile Companion (Flutter):** For checking grades, offline content access, and notifications.

2.  **API Gateway Layer**
    *   Routes requests, handles Rate Limiting (DDoS protection), and authenticates via JWT.

3.  **Core Microservices**
    *   **Identity Service:** Handles SSO (Auth0/SAML) with SIMAD University Directory.
    *   **Course Service:** Manages syllabi, modules, and content metadata.
    *   **Assessment Engine:** Handles quiz rendering, submission acceptance, and auto-grading logic.
    *   **Proctoring Service:** Real-time WebSocket connection handling video streams and flagging events.
    *   **Gradebook Service:** Calculation engine for weighted grades and rubric scoring.
    *   **Notification Service:** Multi-channel dispatcher (Email, SMS, Push).

4.  **Data Persistence Layer**
    *   **Relational DB (PostgreSQL):** User data, course structures, grades.
    *   **NoSQL (MongoDB):** Submission logs, student activity events (telemetry).
    *   **Object Store (S3-Compatible):** Course files, video submissions, proctoring evidence recordings.
    *   **Cache (Redis):** Session management, real-time exam status.

5.  **Integration Hub**
    *   **Turnitin/Unicheck API:** Plagiarism detection.
    *   **Zoom/Teams API:** Live classroom generation.
    *   **SIS/ERP Sync:** Rostering and final grade export.

6.  **Reliability Targets**
    *   **RTO (Recovery Time Obj):** < 15 minutes.
    *   **RPO (Recovery Point Obj):** < 5 minutes (DB transaction logs).
    *   **Scalability:** Auto-scaling groups trigger at 60% CPU utilization.

---

## 6. Security, Privacy & Compliance

### Security Standards
*   **Encryption:** 
    *   *Transit:* TLS 1.3 enforced on all endpoints.
    *   *Rest:* Database and Object Store volumes encrypted via AES-256.
*   **Access Control:**
    *   Least Privilege Principle applied to all Admin accounts.
    *   MFA enforced for all Staff (Faculty/Admins).
*   **Threat Mitigation:**
    *   *Impersonation:* Biometric check at exam start + random intervals.
    *   *Tampering:* Hashed checksums for all exam logs to detect record alteration.

### Privacy & Consent (GDPR/Data Protection Aligned)
*   **Consent Flow:** Explicit "Opt-in" required for webcam enabling before every proctored session.
*   **Data Minimization:** Proctoring video is deleted automatically after 90 days unless part of an active investigation.
*   **Reviewer Safeguards:** 
    *   Proctors cannot see student surnames (blind proctoring).
    *   Proctors cannot download video feeds; "View Only" stream.

---

## 7. Strategic Roadmap

### Phase 1: MVP (Semester-Ready) - Month 0-4
*   **Goal:** Launch core learning and low-stakes assessment.
*   **Deliverables:**
    *   Web Portal (LMS Core) with SSO.
    *   Mobile App (Basic View).
    *   Standard Assessments (Quizzes/Files).
    *   Basic "Exam Shield" (Browser Lockdown only, no AI).
*   **Risk:** Adoption resistance. *Mitigation:* Extensive faculty training workshops.

### Phase 2: V1 (Institution-Wide Rollout) - Month 5-8
*   **Goal:** Enable high-stakes remote exams quality assurance.
*   **Deliverables:**
    *   Full "Exam Shield" with AI Proctoring (Face tracking).
    *   Plagiarism API integration.
    *   Advanced Gradebook with Mediation.
    *   Integrity Dashboard for Exam Office.
*   **Risk:** False positive flags overload. *Mitigation:* Tweak sensitivity threshold + Hire dedicated review staff.

### Phase 3: V2 (Advanced Ecosystem) - Month 9-12+
*   **Goal:** Deep analytics and automated interventions.
*   **Deliverables:**
    *   "At-Risk" Prediction Models.
    *   Offline-First Mobile App Sync.
    *   Adaptive Learning Paths (Content released based on quiz score).
    *   Automated SIS Grade Push.

---

## Top Risks & Mitigations Summary
1.  **Video Bandwidth Strain:** Thousands of video feeds crushing the network.
    *   *Mitigation:* Adaptive bitrate streaming; server-side processing pipeline offloads client.
2.  **Device Compatibility:** Students with old laptops.
    *   *Mitigation:* Lean client optimization (Chromium based); Device Loaner program (Operational policy).
3.  **Data Leakage:** Student data exposed.
    *   *Mitigation:* Regular Penetration Testing (Quarterly) + Data Loss Prevention (DLP) rules.
