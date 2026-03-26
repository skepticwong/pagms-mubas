#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Simple CORS setup
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

@app.route('/api/test', methods=['GET', 'POST'])
def test():
    return jsonify({"message": "CORS test successful", "method": request.method})

@app.route('/api/login', methods=['POST'])
def login():
    return jsonify({"message": "Login endpoint working"})

if __name__ == '__main__':
    print("Starting minimal test server on http://localhost:5000")
    print("Test with: curl -X POST http://localhost:5000/api/login")
    app.run(host='0.0.0.0', port=5000, debug=True)
