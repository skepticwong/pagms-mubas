#!/usr/bin/env python3
"""
Start script for the PAGMS backend server
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting PAGMS Backend Server...")
    print("📍 Server will run on: http://localhost:5000")
    print("🔗 API endpoints available at: http://localhost:5000/api/")
    print("📊 Dashboard endpoints available at: http://localhost:5000/api/dashboard/")
    print("=" * 50)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
