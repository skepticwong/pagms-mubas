#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)

# Very permissive CORS for debugging
CORS(app, 
     origins=["*"],  # Allow all origins for debugging
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])

@app.route('/api/me', methods=['GET'])
def me():
    return jsonify({"message": "API working"})

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        "id": 1,
        "name": "Test User", 
        "email": "test@test.com",
        "role": "PI"
    })

@app.route('/api/rules', methods=['GET'])
def rules():
    return jsonify([
        {
            "id": 1,
            "name": "Test Rule",
            "rule_type": "THRESHOLD",
            "outcome": "BLOCK",
            "priority_level": 1,
            "is_active": True,
            "guidance_text": "Test rule for CORS"
        }
    ])

if __name__ == '__main__':
    print("Starting simple CORS test server...")
    print("Server running on: http://localhost:5000")
    print("Test with browser: http://localhost:5000/api/me")
    app.run(host='0.0.0.0', port=5000, debug=True)
