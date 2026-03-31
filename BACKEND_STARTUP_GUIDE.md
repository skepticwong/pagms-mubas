# PAGMS Backend Startup Guide

## Problem
The frontend is getting a 500 Internal Server Error when trying to check authentication at `/api/me`. This happens because the backend server is not running.

## Solution

### Step 1: Start the Backend Server

Open a **new terminal/command prompt** and run:

```bash
cd "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"
python app.py
```

You should see output like:
```
* Serving Flask app 'app'
* Debug mode: on
* Running on http://0.0.0.0:5000
```

### Step 2: Verify Backend is Working

Open another terminal and test:
```bash
curl http://localhost:5000/health
```

Should return:
```json
{"status": "ok", "message": "PAGMS Backend ili mushe"}
```

### Step 3: Test Auth Endpoint

Test the auth endpoint (should return 401 when not logged in):
```bash
curl http://localhost:5000/api/me
```

Should return:
```json
{"error": "Not authenticated"}
```

### Step 4: Start Frontend

In another terminal, start the frontend:
```bash
cd "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\frontend"
npm run dev
```

### Step 5: Test in Browser

1. Open http://localhost:5173
2. The auth check should now work (no more 500 error)
3. You can register/login with:
   - Email: pi@mubas.ac.mw
   - Password: mubas123
   - Role: PI

## Quick Start Script

You can also use the provided startup script:

```bash
cd "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas"
python start_server.py
```

## Troubleshooting

If you still get 500 errors:

1. **Check if backend is running**: `netstat -an | findstr :5000`
2. **Check dependencies**: `pip install -r backend/requirements.txt`
3. **Check database**: Make sure `backend/instance/pagms.db` exists
4. **Check logs**: Look at the backend terminal output for errors

## Important

- **Backend must run on port 5000**
- **Frontend runs on port 5173** 
- **Both need to be running simultaneously**
- **Keep both terminals open** while working
