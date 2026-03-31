
import os
from app import create_app
from models import db, Grant, User

app = create_app()
with app.app_context():
    grant_count = Grant.query.count()
    user_count = User.query.count()
    print(f"Users in DB: {user_count}")
    print(f"Grants in DB: {grant_count}")
    if grant_count > 0:
        first_grant = Grant.query.first()
        print(f"First grant: {first_grant.title} (PI ID: {first_grant.pi_id})")
    
    # Check current session users
    users = User.query.all()
    for u in users:
        print(f"User: {u.id}, {u.email}, {u.role}")