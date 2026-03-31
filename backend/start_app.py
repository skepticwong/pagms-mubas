#!/usr/bin/env python3
"""
Simple app startup script
"""

import sys
import os

def main():
    print("🚀 Starting PAGMS Asset Management Backend...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Import and create app
        from app import create_app
        app = create_app()
        
        print("✅ App created successfully!")
        
        # Setup database
        from app import setup_database
        setup_database(app)
        print("✅ Database setup complete!")
        
        # Start the server
        print("🌐 Starting Flask server on http://localhost:5000")
        print("📊 Asset Management API is ready!")
        print("🔗 Health check available at: http://localhost:5000/health")
        print("📚 API documentation will be available at: http://localhost:5000")
        print("\n🎉 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(debug=True, port=5000, host='0.0.0.0')
        
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
