# Road Accident Data Analysis System

A Flask + MySQL web application for managing anonymized road-accident records and analyzing recorded patterns by date/time, region, vehicle type, severity, and weather.

> **Important:** Use public, synthetic, or properly anonymized records only. The charts show associations in the supplied dataset; they do not prove that a factor causes an accident. Counts can be affected by traffic volume and reporting coverage.

## Features

- Dashboard with total, serious, and fatal record counts.
- Add individual accident records with input validation.
- Import CSV files; invalid rows are rejected and summarized.
- Search and filter the most recent 500 records.
- Monthly, location, severity, and vehicle summaries.
- Matplotlib charts generated as PNG images.
- Missing-value summary for key analysis fields.
- MySQL foreign key, indexes, and unique location constraint.
- `/health` endpoint for a quick database connection check.

## Technology stack

- Python: application logic and validation
- Flask: web routes and responses
- MySQL: persistent relational storage
- Pandas: data loading, cleaning, grouping, and reports
- NumPy: descriptive statistic (mean daily record count)
- Matplotlib: chart generation
- HTML/CSS/Jinja: web interface

## Folder structure

```text
road_accident_data_analysis/
├── app.py
├── config.py
├── database.py
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── sample_accidents.csv
├── services/
│   ├── __init__.py
│   ├── analysis.py
│   └── validation.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── accidents.html
│   ├── accident_form.html
│   ├── upload.html
│   └── reports.html
└── static/
    └── css/
        └── style.css
```

## Requirements

- Python 3.10 or newer
- MySQL Server 8.x (or compatible MySQL server)
- Git (only needed to push to GitHub)

## Run on Windows 10/11

### 1. Install and start MySQL

Install MySQL Server if it is not already installed. Ensure the MySQL service is running. Remember your MySQL username and password.

### 2. Extract the project

Extract the ZIP file. Open Command Prompt or PowerShell in the extracted `road_accident_data_analysis` folder.

### 3. Create and activate a virtual environment

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

### 4. Install Python packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure MySQL credentials

Copy `.env.example` to a new file named `.env` in the project root. Edit `.env` and set the real MySQL password.

PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Example:

```dotenv
SECRET_KEY=use-a-long-random-secret
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=road_accident_db
PORT=5000
FLASK_DEBUG=false
INIT_DB=true
```

Do not put `.env` in GitHub. It is ignored by `.gitignore`.

### 6. Create the database and tables

The application attempts to create the database and tables at startup when `INIT_DB=true`. The MySQL account must have permission to create a database. Alternatively, open MySQL Workbench, open `schema.sql`, and execute it, then set `INIT_DB=false` in `.env`.

### 7. Start the application

```bash
python app.py
```

Open this address in your browser:

```text
http://127.0.0.1:5000
```

To check the database connection, open:

```text
http://127.0.0.1:5000/health
```

A successful health response looks like:

```json
{"database": "connected", "status": "ok"}
```

### 8. Load sample data

On the site, choose **Import CSV**, select `sample_accidents.csv`, and click **Validate and import**. The dashboard should then display records and charts.

You can also add one record using **Add record**.

## CSV format

Required columns:

- `accident_datetime`
- `region`
- `vehicle_type`
- `severity`

Optional columns:

- `road_name`
- `weather`

Example:

```csv
accident_datetime,region,road_name,vehicle_type,severity,weather
2026-01-03 08:15,Central Region,Main Road,Motorcycle,Minor,Clear
```

Accepted severity values are `Minor`, `Serious`, `Fatal`, and `Unknown`. Date/time examples include `2026-01-03 08:15` and `2026-01-03T08:15`.

## Database design

- `locations`: one row per region/road combination.
- `accidents`: one row per recorded accident, linked to `locations.location_id`.
- The foreign key prevents accident rows from referencing a nonexistent location.
- Indexes support common date, severity, and vehicle-type queries.
- `UNIQUE(region, road_name)` reduces duplicate location records.

## Main routes

| Route | Purpose |
|---|---|
| `/` | Dashboard and charts |
| `/accidents` | Search/filter accident records |
| `/accidents/add` | Add a record |
| `/upload` | Import CSV |
| `/reports` | Monthly, location, and severity reports |
| `/charts/daily.png` | Monthly trend chart |
| `/charts/severity.png` | Severity chart |
| `/charts/vehicle.png` | Vehicle-type chart |
| `/health` | Database health check |

## Common errors

- **Access denied for user:** check `DB_USER` and `DB_PASSWORD` in `.env`.
- **Can't connect to MySQL server:** start the MySQL service and confirm `DB_HOST` and `DB_PORT`.
- **Unknown database:** run `schema.sql`, or confirm the account can create databases and `INIT_DB=true`.
- **No module named ...:** activate `.venv` and run `pip install -r requirements.txt`.
- **Port already in use:** change `PORT=5001` in `.env` and restart.
- **Charts show no data:** import `sample_accidents.csv` or add records.

## Push the project to GitHub

1. Create/sign in to your GitHub account and create a **new empty repository** named `road-accident-data-analysis`. Do not add a README or license there because this project already has a README.
2. Open a terminal in the project folder.
3. Initialize Git and commit the source files:

```bash
git init
git add .
git status
git commit -m "Initial commit: road accident data analysis system"
```

4. Set the main branch and connect your GitHub repository. Replace `YOUR-USERNAME` with your GitHub username:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/road-accident-data-analysis.git
git push -u origin main
```

5. Refresh the GitHub repository page. Your source code should be visible.

If Git says `remote origin already exists`, run:

```bash
git remote -v
git remote set-url origin https://github.com/YOUR-USERNAME/road-accident-data-analysis.git
git push -u origin main
```

If Git asks for authentication, follow GitHub's browser sign-in flow or configure a personal access token/Git Credential Manager. Do not paste passwords or tokens into this chat or commit them to the repository.

## Before submission

- [ ] Confirm MySQL starts and `/health` returns `connected`.
- [ ] Import sample CSV and verify dashboard charts.
- [ ] Test invalid date/time and invalid severity.
- [ ] Confirm missing-value counts are visible.
- [ ] Keep `.env` and any private/raw dataset out of Git.
- [ ] State the dataset source, collection period, geographic granularity, and limitations in your project report.
- [ ] Explain that recorded associations are not proof of causation.
