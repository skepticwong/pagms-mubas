import os
from flask import Flask
from models import db
from sqlalchemy import text
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pagms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def migrate():
    with app.app_context():
        # Get the database connection
        connection = db.engine.connect()
        try:
            print("Starting index migration for rate_type...")
            
            # Check if column exists first to avoid errors
            result = connection.execute(text("PRAGMA table_info(expense_claims)"))
            columns = [row[1] for row in result]
            
            if 'rate_type' not in columns:
                print("Adding rate_type column to expense_claims table...")
                connection.execute(text("ALTER TABLE expense_claims ADD COLUMN rate_type VARCHAR(10)"))
                print("Successfully added rate_type column.")
            else:
                print("Column rate_type already exists in expense_claims table.")
                
            connection.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            connection.rollback()
        finally:
            connection.close()

if __name__ == '__main__':
    migrate()
