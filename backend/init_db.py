# backend/init_db.py
from app import app, db
import os

with app.app_context():
    print("Initializing Database...")
    db.create_all()
    print("Database Initialized Successfully.")
