# backend/routes/misc.py
from flask import Blueprint, jsonify

misc_bp = Blueprint('misc', __name__)

@misc_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns: API status
    """
    return jsonify({'status': 'ok', 'message': 'PAGMS API is running'}), 200