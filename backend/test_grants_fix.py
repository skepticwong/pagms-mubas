
from app import create_app
from services.grant_service import GrantService
import json

app = create_app()
with app.app_context():
    try:
        # Default seeded PI is user_id 1
        grants = GrantService.get_grants_for_user(1)
        print("SUCCESS")
        print(json.dumps(grants, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
