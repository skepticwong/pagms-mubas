#!/usr/bin/env python3
"""
Test backend startup and login endpoint
"""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("Starting backend test...")
    
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"Health check: {response.status_code} - {response.get_json()}")
        
        # Test login endpoint
        response = client.post('/api/login', 
                             json={'email': 'test@example.com', 'password': 'test'},
                             content_type='application/json')
        print(f"Login test: {response.status_code} - {response.get_json()}")
        
        if response.status_code == 500:
            print("Login error detected, checking database...")
            try:
                from models import db, User
                with app.app_context():
                    user_count = User.query.count()
                    print(f"Users in database: {user_count}")
                    
                    # Try to create a test user
                    test_user = User.query.filter_by(email='test@example.com').first()
                    if not test_user:
                        print("Creating test user...")
                        user = User(
                            name='Test User',
                            email='test@example.com',
                            role='Team'
                        )
                        user.set_password('test')
                        db.session.add(user)
                        db.session.commit()
                        print("Test user created")
                    else:
                        print("Test user already exists")
                        
            except Exception as e:
                print(f"Database error: {e}")
                
    print("Backend test complete")
