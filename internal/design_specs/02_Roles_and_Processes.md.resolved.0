# SIMAD oLearn: Operational Framework (Roles & Processes)

**Version:** 1.0  
**Status:** Draft  
**Confidentiality:** Internal Use Only - SIMAD University  

---

## 3. Roles & Permissions (Mandatory)

### Roles Definition
1.  **Student:** Learner enrolled in degree or certificate programs.
2.  **Instructor:** Primary teacher responsible for content, live sessions, and grading.
3.  **Course Coordinator:** Senior faculty overseeing multiple sections of a course.
4.  **Program Director (QA):** Responsible for curriculum alignment and quality assurance.
5.  **Exam Office:** High-stakes assessment governance, scheduling, and validation.
6.  **Proctor/Integrity Reviewer:** Operational staff monitoring live exams and reviewing flags.
7.  **Support Agent:** Tier 1 technical assistance for students/faculty.
8.  **System Admin:** Full technical control (infrastructure, integrations).
9.  **External Examiner:** Temporary accredited access for independent audit/review.

### Permission Matrix (RACI Style)

| Action | Student | Instructor | Prg. Director | Exam Office | Proctor | Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **View Content** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Create Course** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Publish Content** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Set Exam Rules** | ❌ | ✅ | 👁️ | ✅ | 👁️ | ✅ |
| **Override Grade** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Review Integrity Flag** | ❌ | ❌ | 👁️ | ✅ | ✅ | 👁️ |
| **Purge Data** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **View Audit Logs** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |

*Legend: ✅ = Allow, ❌ = Deny, 👁️ = View Only*

---

## 4. End-to-End Work Processes

### 1. Course Lifecycle
1.  **Creation:** Program Director requests course shell via SIS → Admin/API auto-provisions shell.
2.  **Build:** Instructor populates modules, quizzes, and resources (Draft Mode).
3.  **QA Review:** Program Director reviews alignment with detailed syllabus/CLOs.
4.  **Publish:** Course set to "Active" on Semester Start Date.
5.  **Delivery:** 12-16 weeks of engagement, live sessions, and assignments.
6.  **Evaluations:** End-of-course student surveys triggered automatically at 90% completion.
7.  **Archiving:** Course becomes "Read Only" 2 weeks after final grades; contents moved to "Past Courses".

### 2. Assessment Lifecycle
1.  **Design:** Instructor creates assignment/quiz with specific rubric.
2.  **Moderation (Internal):** Course Coordinator approves difficulty and topic coverage.
3.  **Release:** Item becomes visible at scheduled time.
4.  **Submission:** Student uploads work before deadline (late penalties auto-applied).
5.  **Processing:** Turnitin/AI scan runs immediately upon upload.
6.  **Grading:** Instructor scores via SpeedGrader with inline feedback.
7.  **Moderation (External):** Sample of High/Low/Median grades reviewed by External Examiner.
8.  **Result Release:** Grades posted to student gradebook.
9.  **Appeals:** 3-day window for student to formally contest grade via "Appeal" button.

### 3. High-Stakes Exam Lifecycle (Secure)
1.  **Eligibility:** Student clears financial hold + Attendance threshold check.
2.  **Identity Verification:** Student logs in → Biometric snapshot (face match against ID on file).
3.  **Readiness Check:** Exam Shield tests Bandwidth, Webcam, Microphone, and kills prohibited apps.
4.  **Secure Launch:** Browser locks down (kiosk mode). Exam password auto-injected.
5.  **Proctoring:** 
    *   *Live Phase:* Proctor monitors grid view. AI flags suspicious movements.
    *   *Intervention:* Proctor can Pause/Chat/Terminate session if violation is confirmed.
6.  **Submission:** Student clicks "Submit" → Data encrypted and uploaded.
7.  **Integrity Review:** Flagged sessions enter "Review Queue". Human reviewer confirms/dismisses flags.
8.  **Certification:** Grade is "Pending" until Integrity Status = "Cleared".
9.  **Reporting:** Final score sent to Registrar.

### 4. Academic Misconduct Workflow
1.  **Detection:** 
    *   *Automated:* Plagiarism report > 25% OR Proctoring Red Flag confirmed.
    *   *Manual:* Instructor notices drastic writing style shift.
2.  **Evidence Collection:** System packages logs, video clips, and similarity reports into a "Case File".
3.  **Notification:** Student receives formal notice: "Assessment under review for potential policy violation".
4.  **Hearing:** Student submits defense statement (optional video interview).
5.  **Decision:** Discipline Committee reviews Case File (blinded name).
6.  **Sanction:** 
    *   *Level 1:* Warning + Retake capped at 50%.
    *   *Level 2:* Zero on assignment.
    *   *Level 3:* Failure of course + Academic Probation.
7.  **Recordkeeping:** Violation logged in "Student Conduct Registry" (internal only).

### 5. Support & Incident Management
1.  **Intake:** User reports issue via Chat/Ticket/Phone.
2.  **Triage:** 
    *   *P1 (Critical):* Exam outage/crash (Response < 5 mins).
    *   *P2 (Major):* Feature broken for many users.
    *   *P3 (Minor):* Login help/Typo.
3.  **Resolution:** Support Agent fixes or escalates to Admin/Vendor.
4.  **Post-Incident:** Logging logic captures "Time to Resolve".
5.  **Preventive Action:** Weekly review of top ticket drivers prevents recurring issues.
