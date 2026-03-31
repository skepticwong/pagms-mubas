try:
    from app import create_app, setup_database
    print("Application imported successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
