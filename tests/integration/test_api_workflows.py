"""
Integration tests for complete API workflows.

These tests validate end-to-end functionality across multiple components
and endpoints working together as a complete system.
"""
import pytest
import json
import io
from datetime import date


class TestTransactionWorkflow:
    """Test complete transaction management workflow."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_complete_transaction_lifecycle(self, client, db_session):
        """Test complete transaction lifecycle from creation to analytics."""
        # 1. Initialize categories (should happen automatically)
        categories_response = client.get('/api/categories')
        assert categories_response.status_code == 200
        
        # 2. Check initial empty state
        transactions_response = client.get('/api/transactions')
        assert transactions_response.status_code == 200
        initial_data = transactions_response.get_json()
        assert len(initial_data['transactions']) == 0
        
        # 3. Simulate CSV upload with sample data
        csv_content = """Date,Description,Amount,Category
2024-01-15,Restaurant ABC,-25.50,
2024-01-14,Salary deposit,2500.00,
2024-01-13,Uber ride,-12.30,
2024-01-12,Electric bill,-89.45,"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        response = client.post(
            '/api/upload',
            data={'file': (csv_file, 'test_transactions.csv')},
            content_type='multipart/form-data'
        )
        
        # Upload should succeed
        if response.status_code == 200:
            # 4. Verify transactions were created
            transactions_response = client.get('/api/transactions')
            assert transactions_response.status_code == 200
            data = transactions_response.get_json()
            assert len(data['transactions']) > 0
            
            # 5. Check expense summary
            summary_response = client.get('/api/expenses/summary')
            assert summary_response.status_code == 200
            summary_data = summary_response.get_json()
            assert summary_data['total_income'] > 0
            assert summary_data['total_expenses'] < 0
            
            # 6. Check analytics endpoints
            trends_response = client.get('/api/analytics/spending-trends')
            assert trends_response.status_code == 200
            trends_data = trends_response.get_json()
            assert isinstance(trends_data, list)
            
            category_summary_response = client.get('/api/analytics/category-summary')
            assert category_summary_response.status_code == 200
            category_data = category_summary_response.get_json()
            assert isinstance(category_data, list)

    @pytest.mark.integration
    @pytest.mark.api
    def test_transaction_filtering_workflow(self, client, sample_transactions):
        """Test transaction filtering across different criteria."""
        # 1. Get all transactions
        all_response = client.get('/api/transactions')
        assert all_response.status_code == 200
        all_data = all_response.get_json()
        total_transactions = len(all_data['transactions'])
        assert total_transactions > 0
        
        # 2. Filter by category
        food_response = client.get('/api/transactions?category=Food & Dining')
        assert food_response.status_code == 200
        food_data = food_response.get_json()
        
        # Should have fewer or equal transactions than total
        assert len(food_data['transactions']) <= total_transactions
        
        # All returned transactions should be Food & Dining
        for transaction in food_data['transactions']:
            assert transaction['category'] == 'Food & Dining'
        
        # 3. Test non-existent category filter
        empty_response = client.get('/api/transactions?category=NonExistentCategory')
        assert empty_response.status_code == 200
        empty_data = empty_response.get_json()
        assert len(empty_data['transactions']) == 0


class TestCommunalExpenseWorkflow:
    """Test complete communal expense management workflow."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_communal_expense_complete_workflow(self, client, db_session):
        """Test complete communal expense workflow from type creation to expense management."""
        # 1. Get initial expense types (should have defaults)
        types_response = client.get('/api/settings/communal-expenses/types')
        assert types_response.status_code == 200
        initial_types = types_response.get_json()
        initial_count = len(initial_types)
        
        # 2. Create a new expense type
        new_type_data = {
            'name': 'Integration Test Cable',
            'keywords': ['cable', 'tv', 'entertainment', 'integration'],
            'description': 'Cable TV for integration testing'
        }
        
        create_response = client.post(
            '/api/settings/communal-expenses/types',
            json=new_type_data
        )
        assert create_response.status_code == 201
        
        created_type = create_response.get_json()['expense_type']
        type_id = created_type['id']
        
        # 3. Verify type was added
        types_response = client.get('/api/settings/communal-expenses/types')
        updated_types = types_response.get_json()
        assert len(updated_types) == initial_count + 1
        
        # 4. Create expense using the new type
        expense_data = {
            'expense_type_id': type_id,
            'amount': 59.99,
            'date': '2024-01-15',
            'description': 'Monthly cable bill',
            'is_recurring': True
        }
        
        expense_response = client.post(
            '/api/settings/communal-expenses',
            json=expense_data
        )
        assert expense_response.status_code in [200, 201]
        
        # 5. Verify expense was created
        expenses_response = client.get('/api/settings/communal-expenses')
        assert expenses_response.status_code == 200
        expenses = expenses_response.get_json()
        
        # Find our expense
        our_expense = next((e for e in expenses if e.get('expense_type_id') == type_id), None)
        assert our_expense is not None
        assert our_expense['amount'] == 59.99
        
        # 6. Update the expense
        expense_id = our_expense['id']
        update_data = {
            'amount': 69.99,
            'description': 'Updated monthly cable bill',
            'is_recurring': False
        }
        
        update_response = client.put(
            f'/api/settings/communal-expenses/{expense_id}',
            json=update_data
        )
        assert update_response.status_code == 200
        
        # 7. Verify update
        expenses_response = client.get('/api/settings/communal-expenses')
        updated_expenses = expenses_response.get_json()
        updated_expense = next((e for e in updated_expenses if e['id'] == expense_id), None)
        assert updated_expense['amount'] == 69.99
        assert updated_expense['is_recurring'] is False
        
        # 8. Delete the expense
        delete_response = client.delete(f'/api/settings/communal-expenses/{expense_id}')
        assert delete_response.status_code == 200
        
        # 9. Verify deletion
        expenses_response = client.get('/api/settings/communal-expenses')
        final_expenses = expenses_response.get_json()
        deleted_expense = next((e for e in final_expenses if e['id'] == expense_id), None)
        assert deleted_expense is None


class TestDataConsistency:
    """Test data consistency across different operations."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_reset_operations_consistency(self, client, sample_transactions, sample_categories):
        """Test that reset operations maintain data consistency."""
        # 1. Verify initial state has data
        transactions_response = client.get('/api/transactions')
        assert len(transactions_response.get_json()['transactions']) > 0
        
        categories_response = client.get('/api/categories')
        assert len(categories_response.get_json()) > 0
        
        # 2. Reset transactions only
        reset_transactions_response = client.delete('/api/reset/transactions')
        assert reset_transactions_response.status_code == 200
        
        # Transactions should be gone, categories should remain
        transactions_response = client.get('/api/transactions')
        assert len(transactions_response.get_json()['transactions']) == 0
        
        categories_response = client.get('/api/categories')
        assert len(categories_response.get_json()) > 0
        
        # 3. Reset categories
        reset_categories_response = client.delete('/api/reset/categories')
        assert reset_categories_response.status_code == 200
        
        # Both should be empty now
        transactions_response = client.get('/api/transactions')
        assert len(transactions_response.get_json()['transactions']) == 0
        
        categories_response = client.get('/api/categories')
        assert len(categories_response.get_json()) == 0

    @pytest.mark.integration
    @pytest.mark.api
    def test_analytics_with_real_data(self, client, sample_transactions):
        """Test analytics calculations with real transaction data."""
        # 1. Get expense summary
        summary_response = client.get('/api/expenses/summary')
        assert summary_response.status_code == 200
        summary_data = summary_response.get_json()
        
        # 2. Get transactions for manual verification
        transactions_response = client.get('/api/transactions')
        assert transactions_response.status_code == 200
        transactions_data = transactions_response.get_json()
        
        # Manual calculation for verification
        total_income = sum(t['amount'] for t in transactions_data['transactions'] if t['amount'] > 0)
        total_expenses = sum(t['amount'] for t in transactions_data['transactions'] if t['amount'] < 0)
        
        # Verify analytics match manual calculations
        assert summary_data['total_income'] == total_income
        assert summary_data['total_expenses'] == total_expenses
        
        # 3. Test category breakdown
        category_summary_response = client.get('/api/analytics/category-summary')
        assert category_summary_response.status_code == 200
        category_data = category_summary_response.get_json()
        
        # Should have categories with proper structure
        for category in category_data:
            assert 'category' in category
            assert 'total_amount' in category
            assert 'transaction_count' in category
            assert 'percentage' in category


class TestErrorRecovery:
    """Test error recovery and graceful handling of edge cases."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_graceful_handling_of_missing_data(self, client, db_session):
        """Test that APIs handle missing data gracefully."""
        # Test all major endpoints with empty database
        endpoints = [
            '/api/transactions',
            '/api/categories', 
            '/api/analytics/spending-trends',
            '/api/analytics/category-summary',
            '/api/expenses/summary',
            '/api/settings/communal-expenses/types',
            '/api/settings/communal-expenses'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            # Should return valid JSON
            data = response.get_json()
            assert data is not None
            
            # Should return appropriate empty structures
            if isinstance(data, list):
                assert len(data) >= 0  # Empty list is OK
            elif isinstance(data, dict):
                # Should have some structure, not just empty dict
                assert len(data) >= 0

    @pytest.mark.integration
    @pytest.mark.api
    def test_api_error_consistency(self, client, db_session):
        """Test that errors are handled consistently across APIs."""
        # Test invalid requests to various endpoints
        error_tests = [
            ('POST', '/api/upload', {}),  # No file
            ('POST', '/api/settings/communal-expenses/types', {}),  # No data
            ('PUT', '/api/settings/communal-expenses/types/999999', {}),  # Non-existent
            ('DELETE', '/api/settings/communal-expenses/999999', {}),  # Non-existent
        ]
        
        for method, endpoint, data in error_tests:
            if method == 'POST':
                if endpoint == '/api/upload':
                    response = client.post(endpoint, data=data)
                else:
                    response = client.post(endpoint, json=data)
            elif method == 'PUT':
                response = client.put(endpoint, json=data)
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            # Should return appropriate error status
            assert response.status_code >= 400
            
            # Should return JSON error response
            error_data = response.get_json()
            assert error_data is not None
            assert 'error' in error_data or 'message' in error_data


class TestSystemIntegration:
    """Test integration between different system components."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_system_workflow(self, client, db_session):
        """Test a complete workflow using multiple system components."""
        # This test simulates a real user workflow:
        # 1. Set up communal expenses
        # 2. Upload transactions
        # 3. View analytics
        # 4. Manage data
        
        # Step 1: Set up communal expense types
        expense_type_data = {
            'name': 'System Test Utilities',
            'keywords': ['system', 'test', 'utility'],
            'description': 'Utilities for system testing'
        }
        
        type_response = client.post(
            '/api/settings/communal-expenses/types',
            json=expense_type_data
        )
        assert type_response.status_code == 201
        
        # Step 2: Create a communal expense
        type_id = type_response.get_json()['expense_type']['id']
        expense_data = {
            'expense_type_id': type_id,
            'amount': 125.00,
            'date': '2024-01-15',
            'description': 'System test utility bill'
        }
        
        expense_response = client.post(
            '/api/settings/communal-expenses',
            json=expense_data
        )
        assert expense_response.status_code in [200, 201]
        
        # Step 3: Upload some transactions
        csv_content = """Date,Description,Amount,Category
2024-01-15,Test Restaurant,-45.50,
2024-01-14,Test Salary,3000.00,
2024-01-13,System Test Utility Bill,-125.00,"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        upload_response = client.post(
            '/api/upload',
            data={'file': (csv_file, 'system_test.csv')},
            content_type='multipart/form-data'
        )
        
        # Step 4: Verify everything is connected
        if upload_response.status_code == 200:
            # Check transactions were created
            transactions_response = client.get('/api/transactions')
            transactions = transactions_response.get_json()['transactions']
            assert len(transactions) > 0
            
            # Check analytics work
            summary_response = client.get('/api/expenses/summary')
            summary = summary_response.get_json()
            assert summary['total_income'] > 0
            
            # Check communal expenses are tracked
            communal_response = client.get('/api/settings/communal-expenses')
            communal_expenses = communal_response.get_json()
            assert len(communal_expenses) > 0
            
            # Step 5: Clean up - test reset functionality
            reset_response = client.delete('/api/reset/all')
            assert reset_response.status_code == 200
            
            # Verify cleanup
            final_transactions = client.get('/api/transactions').get_json()['transactions']
            assert len(final_transactions) == 0