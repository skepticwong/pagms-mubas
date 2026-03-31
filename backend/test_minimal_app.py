
from flask import Flask
from models import db
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/pagms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("Checkpoint 1: init_app")
db.init_app(app)

print("Checkpoint 2: app_context")
with app.app_context():
    print("Checkpoint 3: Querying User")
    from models import User
    user = User.query.get(1)
    print(f"Checkpoint 4: User: {user.name if user else 'None'}")

print("Checkpoint 5: DONE")
