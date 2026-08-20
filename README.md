# Diversio — HRIS CSV Analyzer

A Django web application that lets authenticated users upload an HRIS (Human Resource Information System) CSV file and instantly see a detailed analysis dashboard — all without writing any data to a database.

---

## Features

- **Secure login** with Django's built-in authentication (demo credentials pre-filled)
- **CSV upload** via drag-and-drop or file picker
- **In-memory analysis** — no employee data is persisted to the database
- **Row-level validation** with source row numbers for easy tracing:
  - Missing required fields (`employee_id`, `employee_name`, `email`)
  - Duplicate employee IDs
  - Dangling manager references (manager ID not found in dataset)
  - Self-referencing managers
- **Org-tree insights**:
  - Root employees (no manager assigned)
  - Managers ranked by direct-report count
  - Reporting cycle detection (e.g. A → B → A)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 6.1 |
| Database | SQLite (auth only) |
| Frontend | HTML, vanilla CSS, vanilla JS |
| Analysis | Pure Python (`csv` + `io` — no external libraries) |

---

## Quick Start

### 1. Clone & set up the virtual environment

```bash
git clone <repo-url>
cd Diversio
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install django
```

### 2. Run migrations & create the demo user

```bash
python manage.py migrate

python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
```

### 3. Start the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 4. Log in & upload

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

After logging in you'll be redirected to the upload page. Upload the included `sample_hris.csv` (or any CSV with the expected columns) to see the analysis dashboard.

---

## Expected CSV Format

The CSV must contain these columns (header names are case-insensitive, whitespace is trimmed):

| Column | Required | Description |
|--------|----------|-------------|
| `employee_id` | ✅ | Unique identifier for the employee |
| `employee_name` | ✅ | Full name |
| `email` | ✅ | Employee email address |
| `manager_id` | — | The `employee_id` of this employee's manager (blank = root) |
| `manager_email` | — | Manager's email (informational, not used for tree analysis) |
| `department` | — | Department name |

A sample file is included at [`sample_hris.csv`](sample_hris.csv).

---

## Project Structure

```
Diversio/
├── config/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── hriscsv/                 # Main application
│   ├── analyzer.py          # CSV parsing, validation & analysis engine
│   ├── views.py             # Upload & results views
│   ├── urls.py              # App-level URL routes
│   └── ...
├── templates/
│   ├── registration/
│   │   └── login.html       # Login page
│   └── hriscsv/
│       ├── upload.html      # File upload page
│       └── results.html     # Analysis results dashboard
├── sample_hris.csv          # Example HRIS data file
├── manage.py
└── README.md
```

---

## Analysis Dashboard Sections

| Section | What it shows |
|---------|---------------|
| **Summary Cards** | Total source rows · Accepted employees · Error count · Root count · Cycle count |
| **Validation Errors** | Table with Row #, Employee ID, Field, and Error Message |
| **Root Employees** | Employees with no `manager_id` — the top of the org tree |
| **Managers & Direct Reports** | Every referenced manager and how many employees report to them |
| **Reporting Cycles** | Employees caught in circular reporting chains (e.g. A manages B, B manages A) |

---

## License

This project is for demonstration purposes.
