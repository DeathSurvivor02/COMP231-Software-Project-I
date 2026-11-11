# COMP231: Software Development Project I

[![Build & Test](https://github.com/DeathSurvivor02/COMP231-Software-Project-I/actions/workflows/ci.yml/badge.svg)](https://github.com/DeathSurvivor02/COMP231-Software-Project-I/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Institution:** Centennial College — School of Engineering Technology and Applied Science (SETAS)  
**Program:** Information and Communication Engineering Technology (ICET)  
**Course Code:** COMP231  
**Project:** Clinical Workflow & Documentation Assistant (*ScribeFlow*)  

---

## 👥 Project Team & Roles

| Member | Role | Primary Responsibilities |
| :--- | :--- | :--- |
| **Ean Bynoe** (`DeathSurvivor02`) | Scrum Master & Lead Architect | System architecture, sprint management, backend API orchestration, CI/CD |
| **Team Member 2** | Full-Stack Developer | Client UI/UX, forms, API integration, front-end validation |
| **Team Member 3** | Backend & Database Engineer | Data modeling, migrations, authentication & security middleware |
| **Team Member 4** | QA & Test Automation Specialist | Unit testing, integration suites, burndown velocity tracking |

*Instructor Collaborator:* **Hao Lac** ([@haocencol](https://github.com/haocencol))

---

## 📋 Project Overview & Architecture

ScribeFlow is an enterprise clinical documentation and workflow tool developed as part of COMP231. The solution streamlines outpatient documentation, structured clinical record generation, and billing compliance.

### Tech Stack
- **Frontend:** React / Vite / TypeScript with Tailwind CSS
- **Backend:** Node.js / Express REST API with TypeScript
- **Database:** PostgreSQL (with Prisma ORM)
- **CI/CD:** GitHub Actions (automated linting, test validation, code scanning)
- **Agile Management:** GitHub Issues, Story Point Labels, Projects Kanban, Milestone Tracking

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18.0.0 or higher)
- npm (v9.0.0 or higher)
- Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DeathSurvivor02/COMP231-Software-Project-I.git
   cd COMP231-Software-Project-I
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment Configuration:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

4. **Run Development Server:**
   ```bash
   npm run dev
   ```

5. **Execute Test Suite:**
   ```bash
   npm test
   ```

---

## 🔄 Agile Workflow & Collaboration Standards

To satisfy the COMP231 collaborative engineering requirements:
1. **Branching Strategy:** Direct commits to `main` are restricted. All features are developed on feature branches: `feature/issue-<number>-short-description`.
2. **Pull Requests (PRs):** Every PR must reference an open GitHub Issue, pass automated CI checks, and obtain at least one peer approval before merging.
3. **Estimation:** Backlog user stories are estimated using Wide-Band Delphi with Fibonacci story points (`1`, `2`, `3`, `5`, `8`, `13`).
4. **Issue Tracking:** Issues are categorized using labels (`user-story`, `bug`, `spike`, `enhancement`, `documentation`) and assigned to active milestones.

---

## 📊 Iteration Progress & Burndown Summary

Refer to our submitted **Progress Monitoring Report (`COMP231_Progress_Monitoring_Report.docx`)** for complete velocity calculations, footnotes, and the Figure 1 burndown chart.

| Iteration | Start Points | Completed (Velocity) | Changed Estimates | New Stories | End Points |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **Iteration 1** | 120 | 35 | +5 | +8 | **98** |
| **Iteration 2** | 98 | 42 | -3 | +4 | **61** |
| **Iteration 3** | 61 | 40 *(proj)* | 0 | +3 | **24** |
| **Iteration 4** | 24 | 24 *(proj)* | 0 | 0 | **0** |

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
