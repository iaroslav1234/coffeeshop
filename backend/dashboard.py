from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/low-stock-alerts', methods=['GET'])
@jwt_required()
def get_low_stock_alerts():
    # Placeholder data - replace with actual database queries
    alerts = [
        {
            'id': 1,
            'name': 'Coffee Beans (Arabica)',
            'current_stock': 2,
            'unit': 'kg'
        },
        {
            'id': 2,
            'name': 'Milk',
            'current_stock': 5,
            'unit': 'liters'
        }
    ]
    return jsonify(alerts)

@dashboard_bp.route('/finance', methods=['GET'])
@jwt_required()
def get_finance_overview():
    # Placeholder data - replace with actual database queries
    finance_data = {
        'current_balance': 50000.00,
        'total_income': 75000.00,
        'total_expenses': 25000.00
    }
    return jsonify(finance_data)
