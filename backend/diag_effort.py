from app import create_app
from services.effort_service import EffortService
import traceback

app = create_app()
with app.app_context():
    try:
        res = EffortService.check_spending_lock(15)
        print("Success:", res)
    except Exception as e:
        traceback.print_exc()
