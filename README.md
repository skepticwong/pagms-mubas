# Post-Award Grant Management System (PAGMS) - MUBAS

A comprehensive grant management system for managing post-award grants at MUBAS.

## Project Structure

```
pagms-mubas/
├── frontend/          # Svelte + Vite + Tailwind CSS
└── backend/           # Flask + SQLite
```

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`

## Features

- **Role-based Access**: PI, Team Member, Finance Officer, RSU Admin
- **Responsive Dashboard**: Tailwind CSS with custom color palette
- **RESTful API**: Flask backend with SQLAlchemy ORM
- **Accessible UI**: Semantic HTML and proper ARIA labels

## Color Palette

- Primary: `#2563eb`
- Success: `#16a34a`
- Warning: `#d97706`
- Danger: `#dc2626`
- Background: `#f8fafc`
- Text: `#1e293b`
