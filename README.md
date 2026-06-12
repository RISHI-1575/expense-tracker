# Smart Expense Tracker

A web-based expense tracking application built with **Flask** and **MySQL**. Lets you log, categorize, and analyze your spending with interactive charts and monthly trend reports.

## Features

- Add, edit, and delete expense entries
- Filter by date range and category
- **Reports dashboard** — total spending, category breakdown, monthly trends
- Visualizations powered by Plotly
- Responsive Bootstrap 5 UI

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** MySQL
- **Frontend:** HTML, Bootstrap 5, Flatpickr, DataTables
- **Charts:** Plotly

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install flask mysql-connector-python plotly pandas python-dotenv
```

### 2. Configure the database

Create a `.env` file in the project root:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=expense_tracker
```

The app automatically creates the database and tables on first run.

### 3. Run the app
```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/expenses` | Fetch all expenses |
| POST | `/api/expenses` | Add a new expense |
| PUT | `/api/expenses/<id>` | Update an expense |
| DELETE | `/api/expenses/<id>` | Delete an expense |
| GET | `/api/reports/total` | Total spending report |
| GET | `/api/reports/category` | Category-wise breakdown |
| GET | `/api/reports/monthly-trend` | Monthly trend data |

## Requirements

- Python 3.8+
- MySQL 5.7+
