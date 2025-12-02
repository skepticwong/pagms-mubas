# PAGMS Backend

Post-Award Grant Management System - Backend (Flask + SQLite)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

- `GET /api/me` - Get current user information
- `GET /api/health` - Health check endpoint

## Database

The SQLite database is stored in `./instance/pagms.db` and is automatically created on first run.

