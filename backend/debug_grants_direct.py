
import os
from app import create_app
from services.grant_service import GrantService
from models import User

app = create_app()
with app.app_context():
    # Test for the PI user
    user = User.query.filter_by(email='pi@mubas.ac.mw').first()
    if not user:
        print("PI User not found in DB!")
    else:
        print(f"Testing for user: {user.id} ({user.role})")
        try:
            grants = GrantService.get_grants_for_user(user.id)
            print(f"Count: {len(grants)}")
            for g in grants:
                print(f"- {g['title']} (Role: {g['user_role']})")
                print(f"  KPIs: {len(g.get('kpi_summary', []))}")
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()

    # Test for Action Items
    print("\nTesting Action Items...")
    try:
        actions = GrantService.get_pi_action_items(user.id if user else 1)
        print(f"Actions: {actions.keys()}")
        print(f"Ready Tranches: {len(actions.get('ready_tranches', []))}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
