#!/usr/bin/env python3
"""
Comprehensive API and database test
"""

import os
import subprocess
import sys
import time
import requests
import sqlite3

def check_database():
    """Check database state"""
    print("🔍 Checking database...")
    
    db_path = os.path.join('instance', 'pagms.db')
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📊 Tables: {len(tables)} found")
    
    # Check required tables
    required = ['users', 'grants', 'tasks', 'deliverable_submissions', 'expense_claims', 'grant_team']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"❌ Missing tables: {missing}")
        return False
    
    # Check data
    cursor.execute('SELECT COUNT(*) FROM users')
    users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM grants')
    grants = cursor.fetchone()[0]
    
    print(f"👥 Users: {users}")
    print(f"💰 Grants: {grants}")
    
    conn.close()
    return users > 0 and grants > 0

def start_server():
    """Start the server"""
    print("🚀 Starting server...")
    
    # Kill any existing python processes
    try:
        subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                      capture_output=True, text=True)
    except:
        pass
    
    # Start new server
    proc = subprocess.Popen([sys.executable, 'start_app.py'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(5)
    return proc

def test_server():
    """Test server endpoints"""
    print("🧪 Testing server...")
    
    try:
        # Health check
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        print("✅ Health check passed")
        
        # Login
        login_response = requests.post('http://localhost:5000/api/login',
                                     json={'email': 'admin@pagms.com', 'password': 'admin123'},
                                     timeout=5)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text[:300]}")
            return False
        print("✅ Login successful")
        
        # Test with authenticated session
        session = requests.Session()
        session.post('http://localhost:5000/api/login',
                    json={'email': 'admin@pagms.com', 'password': 'admin123'})
        
        # Test each endpoint
        endpoints = [
            ('/api/me', 'User info'),
            ('/api/grants', 'Grants'),
            ('/api/deliverables?status=pending', 'Deliverables'),
            ('/api/expenses', 'Expenses'),
            ('/api/tasks', 'Tasks'),
            ('/api/pi-dashboard/action-items', 'Action items')
        ]
        
        all_good = True
        for endpoint, name in endpoints:
            try:
                response = session.get(f'http://localhost:5000{endpoint}', timeout=5)
                status = "✅" if response.status_code == 200 else "❌"
                print(f"{status} {name}: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"    Error: {response.text[:200]}")
                    all_good = False
                    
            except Exception as e:
                print(f"❌ {name}: {e}")
                all_good = False
        
        return all_good
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 PAGMS Backend Diagnostic Tool")
    print("=" * 40)
    
    # 1. Check database
    if not check_database():
        print("❌ Database check failed")
        return False
    
    # 2. Start server
    proc = start_server()
    
    try:
        # 3. Test server
        if test_server():
            print("\n🎉 All tests passed!")
            return True
        else:
            print("\n💥 Some tests failed")
            return False
    finally:
        proc.terminate()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
