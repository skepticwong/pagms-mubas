import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app import app
from backend.models import db, User, Grant

def test_finance_dashboard():
    with app.test_client() as client:
        # 1. Create a Finance user if not exists
        with app.app_context():
            finance_user = User.query.filter_by(role='Finance').first()
            if not finance_user:
                finance_user = User(name='Test Finance', email='finance@test.com', role='Finance')
                finance_user.set_password('password')
                db.session.add(finance_user)
                db.session.commit()
            
            user_id = finance_user.id

        # 2. Simulate login session
        with client.session_transaction() as sess:
            sess['user_id'] = user_id

        # 3. Test Finance Dashboard (500 fix)
        print("Testing Finance Dashboard /api/finance/dashboard...")
        resp = client.get('/api/finance/dashboard')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS: Finance Dashboard loaded.")
        else:
            print(f"FAILURE: {resp.data.decode()}")

        # 4. Test Budget Data (403 fix)
        print("\nTesting Budget Data /api/pi-grants-budget...")
        resp = client.get('/api/pi-grants-budget')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS: Budget Data accessible to Finance.")
        else:
            print(f"FAILURE: {resp.data.decode()}")

if __name__ == "__main__":
    test_finance_dashboard()
