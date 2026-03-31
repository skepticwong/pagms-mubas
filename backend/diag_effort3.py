import traceback
import sys
import os

def test():
    try:
        from app import app
        from services.effort_service import EffortService
        with app.app_context():
            res = EffortService.check_spending_lock(15)
            open('err_trace.txt', 'w').write(f"Success: {res}")
    except Exception as e:
        with open('err_trace.txt', 'w') as f:
            traceback.print_exc(file=f)

test()
