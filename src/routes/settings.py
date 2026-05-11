from flask import Blueprint, jsonify, request
import json
from datetime import datetime, date
from src.models.communal_expense import CommunalExpenseType, CommunalExpense
from src.models.user import db, UserSettings

settings_bp = Blueprint('settings', __name__)

# Default communal expense types
DEFAULT_COMMUNAL_EXPENSES = [
    {
        'name': 'Electricity',
        'keywords': ['electric', 'power', 'edf', 'iberdrola', 'endesa', 'edp', 'utility', 'energia'],
        'description': 'Electricity and power bills'
    },
    {
        'name': 'Water',
        'keywords': ['water', 'aqua', 'agua', 'sabesp', 'aguas'],
        'description': 'Water utility bills'
    },
    {
        'name': 'Gas',
        'keywords': ['gas', 'natural gas', 'propane', 'heating'],
        'description': 'Gas utility bills'
    },
    {
        'name': 'Internet',
        'keywords': ['internet', 'wifi', 'broadband', 'fiber', 'vodafone', 'meo', 'nos', 'nowo', 'telecoms'],
        'description': 'Internet and telecommunications'
    },
    {
        'name': 'Phone',
        'keywords': ['phone', 'mobile', 'cellular', 'telefonica', 'cell phone'],
        'description': 'Mobile phone bills'
    },
    {
        'name': 'Insurance',
        'keywords': ['insurance', 'seguros', 'assurance', 'coverage'],
        'description': 'Various insurance payments'
    },
    {
        'name': 'Rent/Mortgage',
        'keywords': ['rent', 'rental', 'mortgage', 'aluguel', 'casa', 'apartment'],
        'description': 'Housing payments'
    },
    {
        'name': 'Property Tax',
        'keywords': ['property tax', 'council tax', 'imi', 'property', 'municipal'],
        'description': 'Property and municipal taxes'
    },
    {
        'name': 'Waste/Sanitation',
        'keywords': ['waste', 'garbage', 'sanitation', 'lixo', 'cleaning'],
        'description': 'Waste management and sanitation'
    }
]

def initialize_default_communal_expenses():
    """Initialize default communal expense types if they don't exist"""
    for expense_data in DEFAULT_COMMUNAL_EXPENSES:
        existing = CommunalExpenseType.query.filter_by(name=expense_data['name']).first()
        if not existing:
            expense_type = CommunalExpenseType(
                name=expense_data['name'],
                keywords=json.dumps(expense_data['keywords']),
                description=expense_data['description'],
                is_active=True
            )
            db.session.add(expense_type)
    db.session.commit()

@settings_bp.route('/communal-expenses/types', methods=['GET'])
def get_communal_expense_types():
    """Get all communal expense types"""
    try:
        # Initialize defaults if needed
        initialize_default_communal_expenses()
        
        expense_types = CommunalExpenseType.query.filter_by(is_active=True).all()
        return jsonify([et.to_dict() for et in expense_types])
    except Exception as e:
        return jsonify({'error': f'Failed to get communal expense types: {str(e)}'}), 500

@settings_bp.route('/communal-expenses/types', methods=['POST'])
def create_communal_expense_type():
    """Create a new communal expense type"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Check if name already exists
        existing = CommunalExpenseType.query.filter_by(name=data['name'], is_active=True).first()
        if existing:
            return jsonify({'error': f'Communal expense type "{data["name"]}" already exists'}), 400
        
        expense_type = CommunalExpenseType(
            name=data['name'],
            keywords=json.dumps(data.get('keywords', [])),
            description=data.get('description', ''),
            is_active=True
        )
        
        db.session.add(expense_type)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense type "{expense_type.name}" created successfully',
            'expense_type': expense_type.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create communal expense type: {str(e)}'}), 500

@settings_bp.route('/communal-expenses/types/<int:type_id>', methods=['PUT'])
def update_communal_expense_type(type_id):
    """Update a communal expense type"""
    try:
        expense_type = CommunalExpenseType.query.get(type_id)
        if not expense_type:
            return jsonify({'error': 'Communal expense type not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            expense_type.name = data['name']
        if 'keywords' in data:
            expense_type.keywords = json.dumps(data['keywords'])
        if 'description' in data:
            expense_type.description = data['description']
        if 'is_active' in data:
            expense_type.is_active = data['is_active']
        
        expense_type.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense type "{expense_type.name}" updated successfully',
            'expense_type': expense_type.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update communal expense type: {str(e)}'}), 500

@settings_bp.route('/communal-expenses/types/<int:type_id>', methods=['DELETE'])
def delete_communal_expense_type(type_id):
    """Delete (deactivate) a communal expense type"""
    try:
        expense_type = CommunalExpenseType.query.get(type_id)
        if not expense_type:
            return jsonify({'error': 'Communal expense type not found'}), 404
        
        # Soft delete by deactivating
        expense_type.is_active = False
        expense_type.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense type "{expense_type.name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete communal expense type: {str(e)}'}), 500

@settings_bp.route('/communal-expenses', methods=['GET'])
def get_communal_expenses():
    """Get all communal expenses"""
    try:
        expenses = CommunalExpense.query.join(CommunalExpenseType).filter(
            CommunalExpenseType.is_active == True
        ).all()
        return jsonify([expense.to_dict() for expense in expenses])
    except Exception as e:
        return jsonify({'error': f'Failed to get communal expenses: {str(e)}'}), 500

@settings_bp.route('/communal-expenses', methods=['POST'])
def create_communal_expense():
    """Create a new communal expense"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('expense_type_id'):
            return jsonify({'error': 'Expense type ID is required'}), 400
        if not data.get('amount'):
            return jsonify({'error': 'Amount is required'}), 400
        if not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
        
        # Validate expense type exists
        expense_type = CommunalExpenseType.query.get(data['expense_type_id'])
        if not expense_type or not expense_type.is_active:
            return jsonify({'error': 'Invalid expense type'}), 400
        
        # Parse date
        try:
            expense_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        expense = CommunalExpense(
            expense_type_id=data['expense_type_id'],
            amount=float(data['amount']),
            date=expense_date,
            description=data.get('description', ''),
            is_recurring=data.get('is_recurring', True)
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense created successfully',
            'expense': expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create communal expense: {str(e)}'}), 500

@settings_bp.route('/communal-expenses/<int:expense_id>', methods=['PUT'])
def update_communal_expense(expense_id):
    """Update a communal expense"""
    try:
        expense = CommunalExpense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Communal expense not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'expense_type_id' in data:
            expense_type = CommunalExpenseType.query.get(data['expense_type_id'])
            if not expense_type or not expense_type.is_active:
                return jsonify({'error': 'Invalid expense type'}), 400
            expense.expense_type_id = data['expense_type_id']
        
        if 'amount' in data:
            expense.amount = float(data['amount'])
        
        if 'date' in data:
            try:
                expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'description' in data:
            expense.description = data['description']
        
        if 'is_recurring' in data:
            expense.is_recurring = data['is_recurring']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense updated successfully',
            'expense': expense.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update communal expense: {str(e)}'}), 500

@settings_bp.route('/communal-expenses/<int:expense_id>', methods=['DELETE'])
def delete_communal_expense(expense_id):
    """Delete a communal expense"""
    try:
        expense = CommunalExpense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Communal expense not found'}), 404
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Communal expense deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete communal expense: {str(e)}'}), 500

@settings_bp.route('/reset/communal-expenses', methods=['DELETE'])
def reset_communal_expenses():
    """Reset all communal expenses and types to defaults"""
    try:
        # Delete all existing communal expenses
        CommunalExpense.query.delete()
        
        # Delete all existing communal expense types
        CommunalExpenseType.query.delete()
        
        db.session.commit()
        
        # Reinitialize with defaults
        initialize_default_communal_expenses()
        
        return jsonify({
            'success': True,
            'message': 'All communal expenses have been reset to defaults'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error resetting communal expenses: {str(e)}'
        }), 500
# User Settings Endpoints

@settings_bp.route('/user', methods=['GET'])
def get_user_settings():
    """Get user settings."""
    import os
    try:
        return jsonify({
            'success': True,
            'user_name': UserSettings.get('user_name', ''),
            'ai_enabled': UserSettings.get('ai_enabled', os.getenv('AI_ENABLED', 'true')),
            'ai_endpoint': UserSettings.get('ai_endpoint', os.getenv('AI_ENDPOINT', 'http://localhost:11434')),
            'ai_model': UserSettings.get('ai_model', os.getenv('AI_MODEL', 'llama3.2:3b')),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching user settings: {str(e)}'}), 500


@settings_bp.route('/user', methods=['PUT'])
def update_user_settings():
    """Update user settings."""
    try:
        data = request.get_json()

        if 'user_name' in data:
            UserSettings.set('user_name', data['user_name'].strip())
        if 'ai_enabled' in data:
            UserSettings.set('ai_enabled', str(data['ai_enabled']).lower())
        if 'ai_endpoint' in data:
            UserSettings.set('ai_endpoint', data['ai_endpoint'].strip())
        if 'ai_model' in data:
            UserSettings.set('ai_model', data['ai_model'].strip())

        return jsonify({'success': True, 'message': 'Settings updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating settings: {str(e)}'}), 500


@settings_bp.route('/ai/test', methods=['GET'])
def test_ai_connection():
    """Test connection to the configured AI endpoint."""
    try:
        from src.ai.client import get_ollama_client
        client = get_ollama_client()
        available = client.is_available()
        if available:
            return jsonify({'success': True, 'message': f'Connected to {client.base_url}'})
        else:
            return jsonify({'success': False, 'message': f'Cannot reach {client.base_url}'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 200
