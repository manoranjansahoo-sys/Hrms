<<<<<<< HEAD
# Company HRMS – Enterprise Human Resource Management System

A modern, secure, responsive, full-stack enterprise Human Resource Management System (HRMS) built with **Python, Django, Bootstrap 5, Chart.js, and ReportLab**.

The system centralizes employee management, live attendance tracking with self-service punch-in/out, multi-level leave approvals, attendance correction requests, automated monthly payroll with downloadable PDF payslips, official events, holidays, employee recognition, IT helpdesk tickets, and audit trails.

---

## 🏛️ The Four Authority System (Role-Based Access Control)

The system implements strict backend permission validation (RBAC) across four distinct authorities:

| Authority | Role Code | Responsibilities & Modules |
| :--- | :--- | :--- |
| **Authority 1: Employee** | `employee` | Self-service attendance punches, leave applications, personal compensation, downloadable PDF payslips, goals tracking, document requests, and helpdesk tickets. |
| **Authority 2: HR Administrator** | `hr` | Employee onboarding, directory administration, attendance registers, multi-level leave approvals, monthly payroll calculation based on loss-of-pay, profile updates, and document issuance. |
| **Authority 3: Site Manager** | `site_manager` | Supervision of assigned site/campus, daily team attendance monitoring, attendance correction sign-offs, and first-level leave recommendation. |
| **Authority 4: Head / Super Admin** | `head` | Organization-wide executive analytics, workforce distributions across departments/sites, financial payroll authorization, and system security audit trail. |

---

## 🔑 Pre-Seeded Demo Test Accounts

The database comes pre-seeded with realistic data across all four roles:

| Authority | Username | Password | Role Description |
| :--- | :--- | :--- | :--- |
| **Head / Super Admin** | `admin` | `admin123` | Executive Head of Company (Vikramaditya Singhania) |
| **HR Administrator** | `hr_admin` | `hr123` | HR Operations Lead (Pooja Menon) |
| **Site Manager** | `site_manager` | `mgr123` | Bangalore HQ Site Operations Manager (Rajesh Verma) |
| **Employee** | `john_doe` | `emp123` | Senior Full-Stack Engineer (John Doe - EMP101) |

> 💡 **Instant Authority Switcher:** When logged in, click the **"Switch Authority"** dropdown in the top navigation bar to seamlessly switch between roles with a single click during demonstrations.

---

## 🚀 Key Modules & Capabilities

1. **Company Home Portal:**
   - Personalized welcome banner with employee designation, department, and site.
   - Real-time punch card showing today's punch-in/out times and live working hours.
   - Pinned company announcements with urgency indicators and attachments.
   - Upcoming company-declared holidays calendar.
   - Official celebrations, hackathons, and town hall event registration.
   - Birthday and work anniversary reminders with employee privacy controls (`show_birthday_publicly`).
   - Employee of the Month and corporate excellence recognitions.

2. **Attendance Management:**
   - Self-service Punch In & Punch Out with server timestamps and client IP recording.
   - Grace-period aware late arrival detection (General Shift 09:00 - 18:00 with 15-min grace).
   - Overtime and half-day hours auto-calculation.
   - Monthly attendance calendar with status badges (Present, Late, Half-Day, On Leave, Week Off).
   - Attendance Correction & Missing Punch workflow with manager/HR approvals.
   - Master daily attendance register filterable by date, department, and campus.

3. **Leave Management:**
   - Configurable leave categories: Casual Leave (CL), Sick Leave (SL), Earned Leave (EL), and Loss of Pay (LOP).
   - Real-time leave quota balance validation preventing over-drafts.
   - Half-day session support (First Half / Second Half).
   - Multi-tier approval workflow: Employee &rarr; Site Manager (Recommendation) &rarr; HR / Head (Final Approval).
   - Automated deduction from balance and attendance status synchronization.

4. **Payroll & Compensation:**
   - Configurable salary structures: Basic, HRA, Conveyance, Medical, Special Allowances, PF, Professional Tax, and TDS.
   - Monthly payroll generation computing payable days based on verified attendance and Loss of Pay (LOP).
   - Executive payroll approval by Head of Company prior to disbursement.
   - Professional PDF Payslip generation using ReportLab with company watermarks and breakdown tables.
   - Strict confidentiality: Employees can only view and download their own payslips.

5. **Performance & Goals:**
   - OKR and goal milestone tracking with dynamic progress bars (0-100%).
   - Performance evaluation reviews with 5-star ratings, strengths, improvement areas, and promotion recommendations.
   - Corporate honors, spot awards, and Hall of Fame showcase.

6. **Employee Services & Workplace Helpdesk:**
   - Official document requests: Experience letters, Employment certificates, ID card re-issuance, and Visa salary certificates.
   - IT support tickets & confidential grievances with conversation threads and priority tagging.
   - Corporate asset tracking: Barcode asset tags, serial numbers, and equipment allocation.
   - Company policies with mandatory employee acknowledgement.

7. **System Security & Audit Log:**
   - Immutable security audit log tracking user logins, data modifications, approvals, and payroll runs.
   - CSRF protection, session timeouts, and backend permission verification on every endpoint.

---

## 🛠️ Installation & Setup Instructions

### Prerequisites
- Python 3.10+ (Python 3.13 supported)
- Git (optional)

### Step 1: Clone or Navigate to the Project
```bash
cd c:\Users\sahoo\Desktop\dev\Hrms1
```

### Step 2: Activate the Virtual Environment
**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
**On macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Migrations
```bash
python manage.py migrate
```

### Step 5: Seed Enterprise Demo Data
Populate the database with the pre-configured four authorities, employee profiles, attendance records, leaves, announcements, holidays, and payslips:
```bash
python manage.py seed_hrms_data
```

### Step 6: Run Automated Tests
Execute the comprehensive test suite verifying RBAC permissions, attendance calculations, leave workflows, and PDF payslip generation:
```bash
python manage.py test
```

### Step 7: Launch the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open your browser and navigate to:
**`http://127.0.0.1:8000/`**

---

## 🎨 Design System & Palette

- **Primary:** `#1B5E20` (Forest Green)
- **Secondary:** `#2E7D32` (Emerald Green)
- **Accent:** `#F59E0B` (Amber Gold)
- **Background:** `#F6FAF5` (Subtle Mint White)
- **Dark Mode:** `#0F1713` (Obsidian Charcoal)
- **Typography:** `Inter` for clean corporate text, `Roboto Mono` for numbers and timestamps.
- **Visuals:** Responsive sidebar, breadcrumbs, Chart.js interactive charts, live real-time clock.

=======
# Hrms
>>>>>>> 4728e6e58c83747f04605fe48a8a8a10d267ea18
