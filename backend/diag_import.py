import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    import models
    print(f"Models file: {models.__file__}")
    print(f"Available names in models: {dir(models)}")
    if hasattr(models, 'CalendarEvent'):
        print("SUCCESS: CalendarEvent found in models")
    else:
        print("FAILURE: CalendarEvent NOT found in models")
except Exception as e:
    import traceback
    print("CRITICAL ERROR during import:")
    print(traceback.format_exc())
