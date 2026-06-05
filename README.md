<div align="center">

<img src="edvronix/public/images/edvronix-logo.svg" width="100" alt="Edvronix Logo" />

# Edvronix

**School Management System for Pakistani K-12 Institutions**

Built on [Frappe](https://frappeframework.com) · Powered by [ERPNext](https://erpnext.com) · by [Solvronix](https://solvronix.com)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Frappe](https://img.shields.io/badge/Frappe-v16%2B-0089FF)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v16%2B-0F9D58)](https://erpnext.com)
[![Education](https://img.shields.io/badge/Education-v17%2B-orange)](https://github.com/frappe/education)

</div>

---

## Overview

**Edvronix** is a production-ready Frappe application that extends ERPNext and the Education module for K-12 schools in Pakistan. It provides fee management, student admission workflows, guardian tracking, bulk voucher printing, and detailed analytics — all configured through a single settings doctype with no code changes required.

> Designed for schools like Al-Faisal School System, Lahore — Edvronix handles hundreds of students across multiple programs with gender-based fee structures and cost centers.

---

## Features

### Fee Management
- **Auto fee rate override** on Sales Invoice based on the student's latest Program Enrollment tuition fee
- **Gender-based cost center** assignment (Boys / Girls) — fully configurable, no hardcoding
- **Bulk fee voucher printing** — print multiple fee slips in one click with bank details, T&C, and branding
- **Parent-wise** and **bank-wise** voucher grouping
- **Late fee policy** — configurable late fee after 10th and 20th of the month

### Admissions
- **Automatic student email generation** on applicant save — format: `firstname+lastname+number@school.edu.pk`
- **Admission Form** print format (A4) — student info, guardian details, document checklist, office-use section
- **Workflow state tracking** on Student Applicant with CNIC field

### Student & Guardian Management
- **Student graduation workflow** — single-click graduation with certificate number and date, prevents accidental re-activation
- **B-Form image** attachment on Student record
- **Guardian CNIC** and CNIC image storage
- **Guardian-child linking** with program, category, and fee details in reports

### Analytics Dashboard
- **6 live number cards** — Total Students, Fee Collected This Month, Outstanding Fees, Total Staff, Present Today, Registered Guardians
- **3 dashboard charts** — Monthly Fee Collection, Fee Collection Status, Students by Program
- **Edvronix workspace** with quick-action shortcuts for daily operations

### Reports (14 Script Reports)

| Category | Report |
|---|---|
| **Fee** | School Fee Summary |
| **Fee** | Student Fee Collection Report |
| **Fee** | Fee Voucher in Bulk with Bank |
| **Fee** | Monthly Outstanding / Dues Report |
| **Fee** | Sales Invoice Item Report |
| **Fee** | Student Advance Payments |
| **Fee** | Journal Entry Report |
| **Fee** | One Click Report |
| **Student** | Student Strength Report |
| **Student** | Student Stuck-Off Report |
| **Student** | Graduated Students Report |
| **Admission** | Admission Summary Report |
| **Guardian** | Guardian Contact Details |
| **Guardian** | Guardian with Child Details Report |

### Print Formats (2)

| Print Format | Doctype | Description |
|---|---|---|
| **Fee Voucher** | Sales Invoice | School-branded fee slip with Parent + Office copy, T&C footer, scissor divider |
| **Admission Form** | Student Applicant | A4 admission form with student info, guardian details, document checklist |

---

## Requirements

| App | Minimum Version |
|---|---|
| Frappe | `>= 16.0.0` |
| ERPNext | `>= 16.0.0` |
| Education | `>= 17.0.0` |
| Python | `>= 3.14` |

> All version-16+ and onward releases of Frappe / ERPNext / Education are supported.

---

## Installation

```bash
# Step 1 — Get the app
cd /path/to/your/bench
bench get-app https://github.com/solvronix/edvronix --branch version-16

# Step 2 — Install on your site
bench --site your-site.com install-app edvronix

# Step 3 — Run migrations
bench --site your-site.com migrate
```

> **Note:** ERPNext and Education must be installed on the site before installing Edvronix.
> The app enforces this at install time via `required_apps` in `hooks.py`.

---

## Configuration

After installation, go to **Edvronix App → Edvronix Settings** and fill in:

### School Information

| Field | Description |
|---|---|
| School Name | Used for email domain generation and print formats |
| School Logo | Appears on all print formats |
| Watermark Text | Watermark on fee vouchers |
| Address / Phone / Email / Website | Shown on vouchers and admission forms |
| Student Email Domain | TLD for auto-generated emails (default: `edu.pk`) |
| Primary Brand Color | Accent color for printed documents |

### Bank Details

| Field | Description |
|---|---|
| Bank Name | Shown on fee vouchers |
| Account Title / Number / IBAN | Bank account info for fee collection |
| Branch Name / Swift Code | Additional bank details |

### Cost Center Settings

| Field | Description |
|---|---|
| Boys / Male Cost Center | Auto-assigned on Sales Invoice for male students |
| Girls / Female Cost Center | Auto-assigned on Sales Invoice for female students |

### Late Fee Policy

Configure the late fee text and fee amounts applied after the 10th and 20th of each month.

### Item Abbreviations

Map full fee item names (e.g., "Monthly Tuition Fee") to short labels used in bulk voucher printing.

### Terms & Conditions Templates

Create reusable T&C blocks per fee type (All / Tuition / Transport / Hostel / Exam) that appear on fee vouchers.

---

## Custom Fields Added

Edvronix adds the following fields to core doctypes (managed as fixtures — safe to migrate):

| Doctype | Field | Description |
|---|---|---|
| Program Enrollment | `custom_tuition_fee` | Monthly tuition fee amount |
| Program Enrollment | `custom_monthy_fee_` | Monthly total fee |
| Student Applicant | `custom_cnic_no` | Applicant CNIC number |
| Student Applicant | `custom_remarks` | Admission remarks |
| Student | `custom_bform_image` | Child B-Form image |
| Guardian | `custom_cnic_no` | Guardian CNIC |
| Guardian | `custom_cnic_img` | Guardian CNIC image |
| Sales Invoice / Order | `student`, `fee_schedule` | Student link and fee schedule |

---

## Architecture

```
edvronix/
├── edvronix_app/
│   ├── api/
│   │   └── student_applicant.py        # generate_email_now (whitelisted API)
│   ├── doctype/
│   │   ├── edvronix_settings/          # Single doctype — school-wide config
│   │   ├── edvronix_item_abbreviation/ # Child table — fee item short labels
│   │   └── edvronix_terms_template/   # Child table — T&C templates
│   ├── report/                         # 14 Script Reports
│   └── print_format/                   # Fee Voucher + Admission Form
├── events.py                           # Document event hooks
├── workspace_utils.py                  # Workspace save/export override
├── fixtures/                           # Auto-imported via bench migrate
│   ├── client_script.json              # 3 client scripts (Student, Student Applicant)
│   └── property_setter.json
└── public/
    ├── css/edvronix_desk.css           # Desk theme and logo overrides
    ├── js/edvronix_desk.js             # Desk JS utilities
    └── images/edvronix-logo.svg        # Brand logo asset
```

### Key Event Hooks

| Doctype | Event | Handler |
|---|---|---|
| Sales Invoice | `before_insert` | Override tuition fee rate + assign gender-based cost center |
| Student Applicant | `before_insert`, `before_save` | Auto-generate student email address |
| Student | `validate` | Block re-enabling graduated students |
| Workspace | `on_update` | Export workspace JSON back to app fixtures |

---

## Development

### Local Setup

```bash
# Clone into your bench apps directory
cd apps
git clone https://github.com/solvronix/edvronix
cd ..

# Install in developer mode
bench --site your-site.com install-app edvronix
bench --site your-site.com migrate
```

### Pre-commit Hooks

```bash
cd apps/edvronix
pip install pre-commit
pre-commit install
```

Configured linters: **ruff**, **eslint**, **prettier**, **pyupgrade**

### Exporting Fixtures

After making changes to settings, client scripts, or custom fields in the UI:

```bash
bench --site your-site.com export-fixtures --app edvronix
```

---

## CI / CD

| Workflow | Trigger | Description |
|---|---|---|
| **CI** | Push to `develop` | Installs app and runs unit tests |
| **Linters** | Pull Request | Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) + [pip-audit](https://pypi.org/project/pip-audit/) |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with care by **[Solvronix](https://solvronix.com)** · Lahore, Pakistan

*Empowering schools with modern ERP tools*

</div>
# Edvronix-App
