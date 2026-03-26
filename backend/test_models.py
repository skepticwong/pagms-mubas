import sys
import os

# Add current directory
sys.path.append(os.getcwd())

import traceback

print("Checking models.py import...")
try:
    import models
    print("Models module imported successfully")
    print(f"Path: {models.__file__}")
    print(f"Items in models: {[x for x in dir(models) if not x.startswith('__')]}")
    if hasattr(models, 'CalendarEvent'):
        print("CalendarEvent is present")
    else:
        print("CalendarEvent is MISSING")
except Exception:
    print("ERROR importing models:")
    print(traceback.format_exc())
