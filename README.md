# COMP231: Software Development Project I

[![Build & Test](https://github.com/DeathSurvivor02/COMP231-Software-Project-I/actions/workflows/ci.yml/badge.svg)](https://github.com/DeathSurvivor02/COMP231-Software-Project-I/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Institution:** Centennial College - School of Engineering Technology and Applied Science (SETAS)  
**Program:** Information and Communication Engineering Technology (ICET)  
**Course Code:** COMP231  
**Project Title:** Clinical AI Suite: An Enterprise Ambient Intelligence Platform (Group 1)  

---

## Project Team Members, Roles & Subsystem Responsibilities

| Name | Project Role | Subsystem Responsibility | GitHub Handle | Collaborator Status |
| :--- | :--- | :--- | :--- | :--- |
| **Haris Maleji** | Agile Customer / Project Lead | Project Management & Lead Coordination | [`@Haris444-coder`](https://github.com/Haris444-coder) | Invited (Write Access) |
| **Ean Bynoe** | Developer | Clinical Documentation & Ambient NLP | [`@DeathSurvivor02`](https://github.com/DeathSurvivor02) | Owner / Lead Dev |
| **Tanzeef** | Developer | Conversational Intake & Receptionist Bot | [`@TanzeefAhamed`](https://github.com/TanzeefAhamed) | Invited (Write Access) |
| **Joel** | Developer | Patient Experience & Intake Workflows | Pending GitHub handle | Pending invite |
| **Nick** | Developer | Front Desk Operations & Calendar Sync | Pending GitHub handle | Pending invite |
| **Sienna** | Developer | System Administration & RBAC Security | Pending GitHub handle | Pending invite |

*Course Instructor:* **Hao Lac** ([`@haocencol`](https://github.com/haocencol)) - Invited (Write Access)

---

## Project Overview & Architecture

Clinical AI Suite is a clinical workflow and ambient intelligence platform designed to streamline clinical SOAP documentation, patient conversational intake, appointment scheduling, and role-based access control (RBAC).

### Technology Stack
* **Node.js Service:** `src/server.js` with native `node --test` unit tests (`src/server.test.js`)
* **Python / Flask Application:** `clinical-ai-flask/` (`app.py`, `clinical_docs.py`, `appointments.py`, `intake_bot.py`) and root authentication/RBAC modules (`auth.py`, `templates/`, `static/`)
* **Python Testing:** `clinical-ai-flask/test_intake_bot.py`, `test_admin.py`, `test_auth_routes.py`, `test_permissions.py`
* **CI/CD:** GitHub Actions automated build & test pipeline (`.github/workflows/ci.yml`)

---

## Getting Started

### Prerequisites
* Node.js (v18.0.0 or higher)
* Python 3.10+ (for Flask clinical modules)
* Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DeathSurvivor02/COMP231-Software-Project-I.git
   cd COMP231-Software-Project-I
   ```

2. **Install Node.js dependencies & run Node tests:**
   ```bash
   npm install
   npm test
   npm start
   ```

3. **Run the Flask clinical application & Python tests:**
   ```bash
   python clinical-ai-flask/app.py
   ```
   Run Python test suites with `pytest` or `python -m unittest`.

---

## Iteration Progress & Burndown Summary

Refer to our submitted **Progress Monitoring Report (`COMP231_Progress_Monitoring_Report_Group1.docx`)** and **Iteration Planning Report (`COMP231_Iteration_Planning_Report_Group1.docx`)** for complete velocity calculations, footnotes, and the Figure 1 burndown chart.

| Iteration | Start Points | Completed (Velocity) | Changed Estimates | New Stories | End Points | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Iteration 1** | 44 | 20 | 0 | 0 | **24** | Completed |
| **Iteration 2** | 24 | 21 *(target)* | -3 *(scope realignment)* | 0 | **0** | In Progress |

---

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
