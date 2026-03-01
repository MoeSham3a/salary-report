# جدول رواتب و أجور — Salary Report

Arabic payroll web application built with Flask + SQLite. Supports multiple companies, per-quarter employee data, and dynamic Lebanese labor law brackets.

## Features

- **Multi-company** — manage multiple companies from a single dashboard
- **Per-quarter payroll** — each quarter stores independent employee data with copy-from-previous option
- **Auto-calculations** — end of service (8.5%), family allowance (6%), sickness & maternity (11%), tax deductions, transport
- **Dynamic brackets** — all rates follow Lebanese labor law schedules (minimum wage, family allowance caps, transport, deductions)
- **Minimum wage warnings** — amber ⚠️ alert when salary is below legal minimum
- **Excel reports** — download quarterly payroll reports as formatted `.xlsx` files
- **Arabic RTL** — full right-to-left interface with dark premium theme

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/MoeSham3a/salary-report.git
cd salary-report
```

### 2. Install Python

Download Python 3.10+ from [python.org](https://www.python.org/downloads/) and make sure to check **"Add Python to PATH"** during installation.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Project Structure

```
├── app.py                 # Flask routes & API
├── database.py            # SQLite database layer
├── salary_engine.py       # Calculation engine + bracket lookups
├── report_generator.py    # Excel report generation
├── requirements.txt       # Python dependencies
├── static/
│   ├── style.css          # Premium dark theme + RTL
│   └── app.js             # Frontend logic
└── templates/
    ├── home.html           # Company list page
    └── payroll.html        # Per-quarter payroll page
```

## Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Reports:** openpyxl
