from app import create_app
from models import db, User, Grant, GrantTeam

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f"Total Users: {len(users)}")
    for u in users:
        print(f"User: {u.id}, Email: {u.email}, Role: {u.role}")
        
    grants = Grant.query.all()
    print(f"\nTotal Grants: {len(grants)}")
    for g in grants:
        print(f"Grant: {g.id}, Code: {g.grant_code}, PI_ID: {g.pi_id}, Status: {g.status}")
        
        # Check team
        team = GrantTeam.query.filter_by(grant_id=g.id).all()
        for member in team:
            print(f"  Member: {member.user_id}, Role: {member.role}")

    # Specific check for pi@mubas.ac.mw
    pi = User.query.filter_by(email='pi@mubas.ac.mw').first()
    if pi:
        from services.grant_service import GrantService
        my_grants = GrantService.get_grants_for_user(pi.id)
        print(f"\nGrants for pi@mubas.ac.mw (ID {pi.id}): {len(my_grants)}")
    else:
        print("\nUser pi@mubas.ac.mw NOT FOUND")
