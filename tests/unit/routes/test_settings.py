"""
Unit tests for the settings routes.

Tests all endpoints in the settings blueprint including communal expense
type management and configuration functionality.
"""
import pytest
import json
from datetime import date
from src.models.communal_expense import CommunalExpenseType, CommunalExpense


class TestCommunalExpenseTypesAPI:
    """Test the communal expense types API endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_get_communal_expense_types_empty(self, client, db_session):
        """Test getting communal expense types when none exist."""
        response = client.get('/api/settings/communal-expenses/types')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        # Should initialize default types
        assert len(data) > 0

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_get_communal_expense_types_with_data(self, client, sample_communal_expense_type):
        """Test getting communal expense types with existing data."""
        response = client.get('/api/settings/communal-expenses/types')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our test expense type
        test_type = next((t for t in data if t['name'] == 'Electricity'), None)
        assert test_type is not None
        assert test_type['description'] == 'Electricity and power bills'
        assert test_type['is_active'] is True

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_type_success(self, client, db_session):
        """Test successfully creating a new communal expense type."""
        new_expense_type = {
            'name': 'Internet',
            'keywords': ['wifi', 'broadband', 'internet'],
            'description': 'Internet and telecommunications bills'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=new_expense_type
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['name'] == 'Internet'
        assert data['description'] == 'Internet and telecommunications bills'
        assert data['is_active'] is True
        
        # Verify it was created in database
        expense_type = CommunalExpenseType.query.filter_by(name='Internet').first()
        assert expense_type is not None

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_type_missing_name(self, client, db_session):
        """Test creating communal expense type without required name."""
        invalid_data = {
            'keywords': ['test'],
            'description': 'Test description'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=invalid_data
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'Name is required' in data['error']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_type_duplicate_name(self, client, sample_communal_expense_type):
        """Test creating communal expense type with duplicate name."""
        duplicate_data = {
            'name': 'Electricity',  # Already exists
            'keywords': ['power'],
            'description': 'Duplicate electricity'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=duplicate_data
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_type_no_json(self, client):
        """Test creating communal expense type without JSON data."""
        response = client.post('/api/settings/communal-expenses/types')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_type_keywords_as_list(self, client, db_session):
        """Test creating expense type with keywords as list (should be converted to JSON)."""
        new_expense_type = {
            'name': 'Water',
            'keywords': ['water', 'h2o', 'aqua'],
            'description': 'Water utility bills'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=new_expense_type
        )
        assert response.status_code == 200
        
        # Verify keywords were stored as JSON string in database
        expense_type = CommunalExpenseType.query.filter_by(name='Water').first()
        assert expense_type is not None
        keywords = json.loads(expense_type.keywords)
        assert keywords == ['water', 'h2o', 'aqua']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_update_communal_expense_type(self, client, sample_communal_expense_type):
        """Test updating an existing communal expense type."""
        update_data = {
            'name': 'Electricity Updated',
            'keywords': ['electric', 'power', 'energy', 'updated'],
            'description': 'Updated electricity bills description'
        }
        
        response = client.put(
            f'/api/settings/communal-expenses/types/{sample_communal_expense_type.id}',
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['name'] == 'Electricity Updated'
        assert data['description'] == 'Updated electricity bills description'

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_update_nonexistent_communal_expense_type(self, client, db_session):
        """Test updating a non-existent communal expense type."""
        update_data = {
            'name': 'Non-existent',
            'description': 'Should not work'
        }
        
        response = client.put(
            '/api/settings/communal-expenses/types/999999',
            json=update_data
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_delete_communal_expense_type(self, client, sample_communal_expense_type):
        """Test deleting (deactivating) a communal expense type."""
        expense_type_id = sample_communal_expense_type.id
        
        response = client.delete(f'/api/settings/communal-expenses/types/{expense_type_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'deactivated' in data['message']
        
        # Verify it was deactivated (not deleted)
        expense_type = CommunalExpenseType.query.get(expense_type_id)
        assert expense_type is not None
        assert expense_type.is_active is False

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_delete_nonexistent_communal_expense_type(self, client, db_session):
        """Test deleting a non-existent communal expense type."""
        response = client.delete('/api/settings/communal-expenses/types/999999')
        assert response.status_code == 404


class TestCommunalExpensesAPI:
    """Test the communal expenses API endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_get_communal_expenses_empty(self, client, db_session):
        """Test getting communal expenses when none exist."""
        response = client.get('/api/settings/communal-expenses')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_get_communal_expenses_with_data(self, client, sample_communal_expense):
        """Test getting communal expenses with existing data."""
        response = client.get('/api/settings/communal-expenses')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        expense = data[0]
        assert expense['expense_type_name'] == 'Electricity'
        assert expense['amount'] == 120.50
        assert expense['is_recurring'] is True

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_success(self, client, sample_communal_expense_type):
        """Test successfully creating a new communal expense."""
        new_expense = {
            'expense_type_id': sample_communal_expense_type.id,
            'amount': 85.00,
            'date': '2024-02-01',
            'description': 'February electricity bill',
            'is_recurring': True
        }
        
        response = client.post(
            '/api/settings/communal-expenses',
            json=new_expense
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['amount'] == 85.00
        assert data['description'] == 'February electricity bill'
        assert data['is_recurring'] is True

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_missing_required_fields(self, client, db_session):
        """Test creating communal expense without required fields."""
        invalid_data = {
            'amount': 100.00
            # Missing expense_type_id and date
        }
        
        response = client.post(
            '/api/settings/communal-expenses',
            json=invalid_data
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_create_communal_expense_invalid_expense_type(self, client, db_session):
        """Test creating communal expense with non-existent expense type."""
        invalid_data = {
            'expense_type_id': 999999,  # Non-existent
            'amount': 100.00,
            'date': '2024-01-01'
        }
        
        response = client.post(
            '/api/settings/communal-expenses',
            json=invalid_data
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_update_communal_expense(self, client, sample_communal_expense):
        """Test updating an existing communal expense."""
        update_data = {
            'amount': 150.00,
            'description': 'Updated electricity bill',
            'is_recurring': False
        }
        
        response = client.put(
            f'/api/settings/communal-expenses/{sample_communal_expense.id}',
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['amount'] == 150.00
        assert data['description'] == 'Updated electricity bill'
        assert data['is_recurring'] is False

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_update_nonexistent_communal_expense(self, client, db_session):
        """Test updating a non-existent communal expense."""
        update_data = {
            'amount': 100.00,
            'description': 'Should not work'
        }
        
        response = client.put(
            '/api/settings/communal-expenses/999999',
            json=update_data
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_delete_communal_expense(self, client, sample_communal_expense):
        """Test deleting a communal expense."""
        expense_id = sample_communal_expense.id
        
        response = client.delete(f'/api/settings/communal-expenses/{expense_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'deleted' in data['message']
        
        # Verify it was actually deleted
        expense = CommunalExpense.query.get(expense_id)
        assert expense is None

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.settings
    def test_delete_nonexistent_communal_expense(self, client, db_session):
        """Test deleting a non-existent communal expense."""
        response = client.delete('/api/settings/communal-expenses/999999')
        assert response.status_code == 404


class TestSettingsDataValidation:
    """Test data validation in settings endpoints."""

    @pytest.mark.unit
    @pytest.mark.settings
    def test_expense_type_keywords_conversion(self, client, db_session):
        """Test that keywords are properly converted to JSON strings."""
        # Test with list
        data_with_list = {
            'name': 'Test List Keywords',
            'keywords': ['test1', 'test2', 'test3']
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=data_with_list
        )
        assert response.status_code == 200
        
        # Test with string (should also work)
        data_with_string = {
            'name': 'Test String Keywords',
            'keywords': '["string1", "string2"]'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=data_with_string
        )
        assert response.status_code == 200

    @pytest.mark.unit
    @pytest.mark.settings
    def test_expense_date_validation(self, client, sample_communal_expense_type):
        """Test date validation for communal expenses."""
        # Valid date formats
        valid_dates = ['2024-01-15', '2024-12-31']
        
        for valid_date in valid_dates:
            expense_data = {
                'expense_type_id': sample_communal_expense_type.id,
                'amount': 100.00,
                'date': valid_date
            }
            
            response = client.post(
                '/api/settings/communal-expenses',
                json=expense_data
            )
            assert response.status_code == 200

    @pytest.mark.unit
    @pytest.mark.settings
    def test_expense_amount_validation(self, client, sample_communal_expense_type):
        """Test amount validation for communal expenses."""
        # Test with valid amounts
        valid_amounts = [0.0, 1.0, 100.50, 1000.99]
        
        for amount in valid_amounts:
            expense_data = {
                'expense_type_id': sample_communal_expense_type.id,
                'amount': amount,
                'date': '2024-01-15'
            }
            
            response = client.post(
                '/api/settings/communal-expenses',
                json=expense_data
            )
            assert response.status_code == 200


class TestSettingsIntegration:
    """Test integration scenarios in settings functionality."""

    @pytest.mark.unit
    @pytest.mark.settings
    def test_full_expense_type_lifecycle(self, client, db_session):
        """Test complete lifecycle of a communal expense type."""
        # 1. Create expense type
        create_data = {
            'name': 'Lifecycle Test',
            'keywords': ['test', 'lifecycle'],
            'description': 'Test expense type lifecycle'
        }
        
        response = client.post(
            '/api/settings/communal-expenses/types',
            json=create_data
        )
        assert response.status_code == 200
        expense_type_id = response.get_json()['id']
        
        # 2. Update expense type
        update_data = {
            'name': 'Lifecycle Test Updated',
            'keywords': ['test', 'lifecycle', 'updated'],
            'description': 'Updated test expense type'
        }
        
        response = client.put(
            f'/api/settings/communal-expenses/types/{expense_type_id}',
            json=update_data
        )
        assert response.status_code == 200
        
        # 3. Create expense using this type
        expense_data = {
            'expense_type_id': expense_type_id,
            'amount': 75.00,
            'date': '2024-01-15',
            'description': 'Test expense'
        }
        
        response = client.post(
            '/api/settings/communal-expenses',
            json=expense_data
        )
        assert response.status_code == 200
        expense_id = response.get_json()['id']
        
        # 4. Verify both exist
        response = client.get('/api/settings/communal-expenses/types')
        assert response.status_code == 200
        types = response.get_json()
        assert any(t['id'] == expense_type_id for t in types)
        
        response = client.get('/api/settings/communal-expenses')
        assert response.status_code == 200
        expenses = response.get_json()
        assert any(e['id'] == expense_id for e in expenses)
        
        # 5. Deactivate expense type
        response = client.delete(f'/api/settings/communal-expenses/types/{expense_type_id}')
        assert response.status_code == 200
        
        # 6. Verify expense type is deactivated but expense still exists
        response = client.get('/api/settings/communal-expenses/types')
        types = response.get_json()
        active_types = [t for t in types if t['is_active']]
        assert not any(t['id'] == expense_type_id for t in active_types)
        
        response = client.get('/api/settings/communal-expenses')
        expenses = response.get_json()
        assert any(e['id'] == expense_id for e in expenses)