#!/usr/bin/env python3
"""
Test backend connectivity
"""

import requests
import time
import sys

def test_backend():
    print("[TEST] Testing backend connectivity...")
    
    # Test health endpoint
    for i in range(10):
        try:
            response = requests.get('http://localhost:5000/health', timeout=2)
            print(f"[OK] Health check: {response.status_code} - {response.json()}")
            break
        except requests.exceptions.ConnectionError:
            print(f"[FAIL] Attempt {i+1}: Backend not responding on port 5000")
            if i < 9:
                print("[WAIT] Waiting 2 seconds...")
                time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            break
    else:
        print("[ERROR] Backend server is not running!")
        print("\n[START] To start the backend server:")
        print("1. Open a new terminal")
        print("2. Run: cd \"e:\\Post-Award-Grant-Management-System-MUBAS (PAGMS)\\pagms-mubas\\backend\"")
        print("3. Run: python app.py")
        return False
    
    # Test auth endpoint
    try:
        response = requests.get('http://localhost:5000/api/me', timeout=2)
        print(f"[OK] Auth endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"[ERROR] Auth endpoint error: {e}")
    
    print("\n[SUCCESS] Backend server is running and accessible!")
    return True

if __name__ == '__main__':
    test_backend()
