# backend/check_db.py
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Grant

with app.app_context():
    print("=== USERS ===")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}")
        # DO NOT print password_hash in real projects!
    
    print("\n=== GRANTS ===")
    grants = Grant.query.all()
    for g in grants:
        print(f"ID: {g.id}, Title: {g.title}, PI: ?, Budget: {g.total_budget}")