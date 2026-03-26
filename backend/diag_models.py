import os
import sys
import inspect

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import models
    print(f"Models file: {models.__file__}")
    
    names = ['OutcomeIndicator', 'OutcomeReportingPeriod', 'OutcomeActual']
    for name in names:
        if hasattr(models, name):
            obj = getattr(models, name)
            print(f"{name} found in models.")
            print(f"{name} type: {type(obj)}")
            try:
                print(f"{name} file: {inspect.getfile(obj)}")
            except:
                print(f"Could not get file for {name}")
        else:
            print(f"{name} NOT found in models.")
            
except Exception as e:
    print(f"Error: {e}")
