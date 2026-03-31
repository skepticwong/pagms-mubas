import traceback
import sys

try:
    from app import create_app
except ImportError:
    pass

def test():
    try:
        from app import app
        from services.effort_service import EffortService
        with app.app_context():
            res = EffortService.check_spending_lock(15)
            print("check_spending_lock success:", res)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

test()
