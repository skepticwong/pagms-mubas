#!/usr/bin/env python3
"""
Simple backend server starter
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting PAGMS Backend Server...")
    print("📍 Server: http://localhost:5000")
    print("🔗 API: http://localhost:5000/api")
    print("=" * 50)
    
    try:
        from app import create_app
        app = create_app()
        
        # Run with minimal configuration
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
