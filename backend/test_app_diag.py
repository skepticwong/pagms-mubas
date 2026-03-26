from app import create_app
from models import db
import os

app = create_app()
app.config['TESTING'] = True

with app.test_client() as client:
    print("Testing /api/me (expect 401)...")
    try:
        res = client.get('/api/me')
        print(f"Status: {res.status_code}")
        print(f"Data: {res.get_json()}")
        
        print("\nTesting /api/expenses (expect 401 or 200)...")
        res = client.get('/api/expenses')
        print(f"Status: {res.status_code}")
        print(f"Data: {res.get_json()}")
    except Exception as e:
        print(f"Error during internal test: {e}")
