# SIMAD oLearn: Product Requirements Document (PRD) & Core Scope

**Version:** 1.0  
**Status:** Draft  
**Confidentiality:** Internal Use Only - SIMAD University  

---

## 1. Vision & Goals

### Vision
To establish **SIMAD oLearn** as a premier distance learning ecosystem that seamlessly integrates flexible, accessible education with rigorous, uncompromising academic integrity standard, enabling SIMAD University to deliver trusted credentials globally.

### Strategic Goals
1.  **Credible Integrity:** Ensure high-stakes online examinations are secure, defensible, and recognized by accreditation bodies.
2.  **Scalable Quality:** Support 10,000+ simultaneous learners across blended, hybrid, and fully online modalities without performance degradation.
3.  **Inclusive Accessibility:** Provide an equitable learning experience for students with variable internet connectivity and diverse accessibility needs.
4.  **Data-Driven Student Success:** Utilize ethical telemetry to identify at-risk students early and intervene proactively.

---

## 2. Target Users & Personas

| Role | Persona | Key Needs |
| :--- | :--- | :--- |
| **Student** | *Amina, 21, Business Undergrad* | Reliable mobile access, clear deadlines, fair exams without technical stress, quick support. |
| **Lecturer** | *Prof. Hassan, Computer Science* | Easy content upload, automated grading tools, cheating alerts, insights into student engagement. |
| **Program Director** | *Dr. Lul, Faculty of Medicince* | Oversight of course quality, accreditation data compliance, cohort performance reports. |
| **Exam Officer** | *Mr. Abdi, Central Exam Office* | Security auditing, exam scheduling, proctoring incident review, result validation. |
| **Proctor** | *Sarah, Integrity Reviewer* | clear interfaces to monitor live feeds, flagged incident timelines, robust evidence logging. |
| **System Admin** | *Ali, IT Operations* | Uptime monitoring, integration management, role-based access control (RBAC). |

---

## 3. Use Cases

*   **UC-01 Blended Learning:** Students attend physical lectures but submit assignments and take quizzes on SIMAD oLearn.
*   **UC-02 Fully Online Certification:** A professional takes a 3-month certification entirely remote, including final secure exams.
*   **UC-03 Make-up Examination:** A student misses a physical exam due to illness and takes a secure, proctored equivalent online.
*   **UC-04 Capstone Project:** Final year students submit large files and portfolio links for multi-stage review and external examiner grading.
*   **UC-05 Low-Bandwidth Mode:** Rural students download encrypted content for offline study and sync progress when connectivity returns.

---

## 4. Requirements

### Functional Requirements (FR)
*   **FR-1:** Platform must support granular Role-Based Access Control (RBAC) dependent on faculty and department hierarchy.
*   **FR-2:** The "SIMAD oLearn Exam Shield" must prevent copying, pasting, printing, and application switching during high-stakes exams.
*   **FR-3:** System must support offline-first mobile app usage with encrypted content syncing.
*   **FR-4:** All assessments must support rubrics and blind grading workflows.
*   **FR-5:** Proctoring system must flag "multiple faces detected" and "focus loss" events automatically.

### Non-Functional Requirements (NFR)
*   **NFR-1 (Scalability):** Support 2,000 concurrent exam takers with <200ms transaction latency.
*   **NFR-2 (Privacy):** All proctoring video data must be encrypted at rest (AES-256) and strictly access-logged.
*   **NFR-3 (Availability):** 99.9% uptime during designated exam periods.
*   **NFR-4 (Accessibility):** WCAG 2.1 AA compliance for the learner interface.

### Assumptions & Risks
*   **Assumption:** Students have access to a device with a working camera/microphone for high-stakes exams.
*   **Risk:** False positives in AI proctoring causing student anxiety.
    *   *Mitigation:* AI flags are *never* automated verdicts; human review is mandatory for sanctions.
*   **Risk:** Internet instability during exams.
    *   *Mitigation:* "Graceful resume" logic in Exam Shield allows re-entry within a strict time window with audit logging.

### Acceptance Criteria & Definition of Done
*   **DoD:** Feature developed, unit tested (>80% coverage), QA verified, accessibility checked, security scanned, documented, and signed off by Product Owner.

---

## 5. Core Feature Scope

### B. Learning Delivery (LMS Core)

#### 1. User Onboarding & Identity
*   **Features:** SSO via University Portal (Google/Microsoft Workspace); Manual fallback for external guests.
*   **Workflow:** New Student → SSO Login → Terms of Service Acceptance → Dashboard.
*   **Edge Case:** Name change in Registrar system must propagate to LMS within 24h.
*   **Telemetry:** Login success rate, time-to-first-course-access.

#### 2. Course & Content Management
*   **Features:** Drag-and-drop course builder; "Drip" release settings (Date-based or Criteria-based); Alignment to PLOs/CLOs.
*   **Content Types:** Embedded PDF, H.264 Video (adaptive streaming), LTI 1.3 Tools, HTML5 assignments.
*   **Workflow:** Faculty creates Draft → Uploads Content → Adds Release Conditions → Publishes.

#### 3. Live & Asynchronous Learning
*   **Features:** "Launch Live Class" button (Zoom/Teams integration); Threaded discussion boards with "post-first" privacy.
*   **Workflow:** Scheduled event triggers notification → One-click join → Attendance auto-logged.

#### 4. Accessibility & Inclusive Design
*   **Features:** System-wide high contrast toggle; Screen reader aria-labels on all navigation; Transcript upload required for video content.
*   **Constraint:** Assessments must allow "Extra Time" overrides per student ID (ADA/Accommodation compliance).

### C. Assessment & Evaluation

#### 1. Assessment Types
*   **Scope:** Assignments (File upload, Text); Quizzes (Auto-graded); Workshops (Peer review); Oral Exams (Video submission).

#### 2. Assessment Authoring
*   **Question Bank:** Hierarchical tagging (Subject > Topic > Difficulty > Bloom’s Taxonomy).
*   **Rules:** Randomize question order; Randomize variables within questions (Math); "Backtracking Prohibited" option.

#### 3. Submission & Grading
*   **Workflow:** Student uploads → Plagiarism Check (Turnitin API) → Similarity Score Generated → Instructor Notified.
*   **Grading:** SpeedGrader interface; Annotation tools (highlight, strikeout); Audio feedback recording.

#### 4. Integrity Controls (Standard)
*   **Authorship Signals:** Analyzing typing velocity and patterns (keystroke dynamics) for long-form text (privacy notice required).
*   **Plagiarism:** Auto-check against institutional repo and internet sources.
*   **AI Detection:** Integration with detection providers to flag "Likely AI" for human review.

### D. Secure High-Stakes Examination (SIMAD oLearn Exam Shield)

#### 1. Locked Exam Delivery
*   **Secure Browser:** Custom binary (Windows/macOS).
*   **Restrictions:**
    *   Kill list: TeamViewer, Discord, Skype, Browser DevTools.
    *   Clipboard cleared on launch.
    *   Single monitor enforcement (disconnect external output).
*   **Edge Case:** Power failure. *Response:* Local encrypted cache saves answers every 10s. Resume requires admin OTP if >5 mins offline.

#### 2. Remote Proctoring
*   **Environment Scan:** 360-degree room pan required before start.
*   **Monitoring:**
    *   *Primary:* Webcam face tracking (Looking away, multiple faces, too dark).
    *   *Secondary (Optional):* Mobile phone camera QR-linked as side-view proctor.
*   **Privacy:** "Blur background" option NOT available for high-stakes; recording indicator always active.

#### 3. Exam Integrity Decisioning
*   **Auto-Gating:** Exam won't launch if microphone volume < 10% or webcam covered.
*   **Live Integrity Dashboard:** Proctors see grid view of active students with "Risk Traffic Lights" (Green/Yellow/Red).
*   **Workflow:** Flagged Incident → Timestamp Marker → Post-Exam Queue → Reviewer Verdict (Clear/Warning/Fail).

### E. Student Services & Academic Administration

*   **Support:** "Panic Button" in Exam Shield opens chat with priority support (no exam content discussion allowed).
*   **Misconduct Workflow:**
    *   Instructor reports incident → Evidence attached → Student notified (generic "Under Review") → Integrity Committee Dashboard.
*   **Administration:** Bulk action tools for semester rollover, user enrollment, and archive retrieval.

### F. Analytics & Quality Assurance

#### 1. Analytics
*   **Student:** "My Progress" radar chart vs class average (anonymized).
*   **Instructor:** "At-Risk" identification (Low login frequency + Missed assignments).

#### 2. Operational Monitoring
*   **Exam Health:** Real-time graph of "Active Sessions", "Dropped Connections", "Server Load".
*   **Alerts:** Slack/SMS hook for 5% exam failure rate (system-wide issue).
