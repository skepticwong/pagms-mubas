
import os
import sys
# Ensure we are in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Grant, GrantTeam

app = create_app()
with app.app_context():
    print("--- USERS ---")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}")
    
    print("\n--- GRANTS ---")
    grants = Grant.query.all()
    for g in grants:
        print(f"ID: {g.id}, Title: {g.title}, PI_ID: {g.pi_id}, Status: {g.status}")
        
    print("\n--- GRANT TEAMS ---")
    teams = GrantTeam.query.all()
    for t in teams:
        print(f"GrantID: {t.grant_id}, UserID: {t.user_id}, Role: {t.role}")
