# Backend Startup Instructions

## Issue: Frontend getting 500 error on login

### Diagnosis Steps

1. **Start the backend manually:**
   ```bash
   cd backend
   python app.py
   ```

2. **Check if backend is running:**
   - Open browser or use curl: `http://localhost:5000/health`
   - Should return: `{"status": "ok", "message": "PAGMS Backend ili mushe"}`

3. **Test login endpoint:**
   ```bash
   curl -X POST http://localhost:5000/api/login \
        -H "Content-Type: application/json" \
        -d '{"email": "test@example.com", "password": "test"}'
   ```

### Common Issues & Solutions

#### Issue 1: No users in database
**Symptom:** Login returns 401 or 500 error
**Solution:** Create test user
```python
# In Python shell with app context:
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User(name='Test User', email='test@example.com', role='Team')
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
```

#### Issue 2: Database tables missing
**Symptom:** 500 error on any endpoint
**Solution:** Run migration
```bash
cd backend
python migrations/add_nce_burn_forecast_tables.py
```

#### Issue 3: Import errors
**Symptom:** Backend fails to start
**Solution:** Check imports
```bash
cd backend
python -c "from app import create_app; print('OK')"
```

### Frontend Connection

Once backend is running, frontend should connect to:
- Backend: `http://localhost:5000`
- Frontend: `http://localhost:5173` (or whatever Vite uses)

### Test Users

Default test user (if created):
- Email: `test@example.com`
- Password: `test`
- Role: `Team`

### Verification

1. Backend health check: `GET /health`
2. Login test: `POST /api/login`
3. Check new endpoints:
   - `GET /api/rules/burn-rate/summary` (RSU only)
   - `GET /api/amendments/pending` (RSU only)

### If Issues Persist

1. Check backend console output for errors
2. Verify database file exists: `backend/instance/pagms.db`
3. Check all imports are working
4. Ensure all new services can be imported

### New Features Available

Once backend is running:
- ✅ NCE Request workflow
- ✅ Burn Rate Analysis  
- ✅ Budget Forecasting
- ✅ Financial Dashboards
- ✅ 19 new API endpoints
