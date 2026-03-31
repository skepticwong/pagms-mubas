#!/usr/bin/env python3
"""
Debug backend startup to identify the 500 error
"""

import sys
import traceback

def main():
    try:
        print("Starting backend debug...")
        
        # Try importing app
        print("1. Importing app...")
        from app import create_app
        print("   ✅ App imported successfully")
        
        # Try creating app
        print("2. Creating app...")
        app = create_app()
        print("   ✅ App created successfully")
        
        # Try database setup
        print("3. Setting up database...")
        from app import setup_database
        setup_database(app)
        print("   ✅ Database setup successful")
        
        # Try importing all services
        print("4. Testing service imports...")
        from services.nce_service import NCEService
        from services.burn_rate_service import BurnRateService
        from services.budget_forecasting_service import BudgetForecastingService
        print("   ✅ All services imported successfully")
        
        # Try importing all routes
        print("5. Testing route imports...")
        from routes.amendments import amendments_bp
        from routes.rules import rules_bp
        print("   ✅ All routes imported successfully")
        
        # Test login endpoint
        print("6. Testing login endpoint...")
        with app.test_client() as client:
            response = client.post('/api/login', 
                                 json={'email': 'test@example.com', 'password': 'test'},
                                 content_type='application/json')
            print(f"   Login response: {response.status_code}")
            if response.status_code == 500:
                print(f"   Error data: {response.get_json()}")
                
                # Check if user exists
                from models import User
                with app.app_context():
                    users = User.query.all()
                    print(f"   Users in database: {len(users)}")
                    if len(users) == 0:
                        print("   ⚠️  No users in database - need to create test user")
                        
                        # Create test user
                        test_user = User(
                            name='Test User',
                            email='test@example.com',
                            role='Team'
                        )
                        test_user.set_password('test')
                        from models import db
                        db.session.add(test_user)
                        db.session.commit()
                        print("   ✅ Test user created")
                        
                        # Try login again
                        response = client.post('/api/login', 
                                             json={'email': 'test@example.com', 'password': 'test'},
                                             content_type='application/json')
                        print(f"   Login retry response: {response.status_code}")
                        print(f"   Login retry data: {response.get_json()}")
            else:
                print(f"   Login success: {response.get_json()}")
        
        print("7. Starting development server...")
        print("   Backend ready to start!")
        print("   Run: python app.py")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
