from app import create_app
from models import db, User
from services.auth_service import AuthService

def seed_team_members():
    app = create_app()
    with app.app_context():
        team_members_data = [
            {"name": "Alice Team", "email": "alice@mubas.ac.mw", "password": "password123", "role": "Team"},
            {"name": "Bob Team", "email": "bob@mubas.ac.mw", "password": "password123", "role": "Team"},
            {"name": "Charlie Team", "email": "charlie@mubas.ac.mw", "password": "password123", "role": "Team"}
        ]

        print("Creating sample Team member accounts...")
        created_users = []
        for member_data in team_members_data:
            try:
                # Check if user already exists to avoid duplicates
                existing_user = User.query.filter_by(email=member_data["email"]).first()
                if existing_user:
                    print(f"User {member_data['email']} already exists. Skipping.")
                    continue

                user = AuthService.register(
                    member_data["name"],
                    member_data["email"],
                    member_data["password"],
                    member_data["role"],
                    None # pay_rate is optional
                )
                created_users.append(user)
                print(f"Created user: {user.name} ({user.email})")
            except ValueError as e:
                print(f"Error creating user {member_data['email']}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for user {member_data['email']}: {e}")

        if created_users:
            print("\n--- Created Team Member Credentials ---")
            for user_obj in created_users:
                # Note: Passwords are not stored in plain text,
                # so we provide the one used for creation.
                original_password = next(
                    (item["password"] for item in team_members_data if item["email"] == user_obj.email),
                    "N/A"
                )
                print(f"Email: {user_obj.email}, Password: {original_password}")
            print("---------------------------------------")
        else:
            print("No new Team member accounts were created.")

if __name__ == "__main__":
    seed_team_members()
