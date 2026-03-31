#!/usr/bin/env python3
"""
Start PAGMS Backend Server with Output
"""

import os
import sys
import subprocess
import time

def main():
    print("[START] Starting PAGMS Backend Server...")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"
    os.chdir(backend_dir)
    print(f"[DIR] Directory: {os.getcwd()}")
    
    # Check Python version
    print(f"[PYTHON] Python: {sys.version}")
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("[ERROR] app.py not found!")
        return
    
    print("[OK] Found app.py")
    
    # Install dependencies if needed
    print("[DEPS] Checking dependencies...")
    try:
        import flask
        print(f"[OK] Flask {flask.__version__}")
    except ImportError:
        print("[INSTALL] Flask not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask'])
    
    try:
        import flask_cors
        print("[OK] Flask-CORS")
    except ImportError:
        print("[INSTALL] Flask-CORS not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask-cors'])
    
    try:
        import jwt
        print("[OK] PyJWT")
    except ImportError:
        print("[INSTALL] PyJWT not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyjwt'])
    
    print("\n[SERVER] Starting Flask server...")
    print("[URL] URL: http://localhost:5000")
    print("[HEALTH] Health: http://localhost:5000/health")
    print("[AUTH] Auth: http://localhost:5000/api/me")
    print("=" * 50)
    
    # Start the server
    try:
        # Run app.py directly
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Server failed with code {e.returncode}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == '__main__':
    main()
