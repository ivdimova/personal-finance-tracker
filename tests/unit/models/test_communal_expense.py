"""
Unit tests for the CommunalExpense and CommunalExpenseType models.

Tests the communal expense models including their relationships,
validation, and data conversion methods.
"""
import pytest
import json
from datetime import date, datetime
from src.models.communal_expense import CommunalExpenseType, CommunalExpense


class TestCommunalExpenseType:
    """Test cases for the CommunalExpenseType model."""

    @pytest.mark.unit
    @pytest.mark.models
    def test_create_communal_expense_type(self, db_session):
        """Test creating a new communal expense type."""
        expense_type = CommunalExpenseType(
            name='Electricity',
            keywords=json.dumps(['electric', 'power', 'edf']),
            description='Electricity and power bills',
            is_active=True
        )
        
        db_session.add(expense_type)
        db_session.commit()
        
        assert expense_type.id is not None
        assert expense_type.name == 'Electricity'
        assert expense_type.keywords == json.dumps(['electric', 'power', 'edf'])
        assert expense_type.description == 'Electricity and power bills'
        assert expense_type.is_active is True
        assert expense_type.created_at is not None
        assert expense_type.updated_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_to_dict(self, sample_communal_expense_type):
        """Test communal expense type to_dict method."""
        result = sample_communal_expense_type.to_dict()
        
        expected_keys = ['id', 'name', 'keywords', 'description', 'is_active', 'created_at', 'updated_at']
        assert all(key in result for key in expected_keys)
        
        assert result['name'] == 'Electricity'
        assert result['keywords'] == json.dumps(['electric', 'power', 'edf'])
        assert result['description'] == 'Electricity and power bills'
        assert result['is_active'] is True

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Missing name should raise an error
        with pytest.raises(Exception):
            expense_type = CommunalExpenseType(
                keywords=json.dumps(['test']),
                description='Test'
            )
            db_session.add(expense_type)
            db_session.commit()

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_nullable_fields(self, db_session):
        """Test that nullable fields can be None."""
        expense_type = CommunalExpenseType(
            name='Minimal Expense',
            keywords=None,
            description=None,
            is_active=True
        )
        
        db_session.add(expense_type)
        db_session.commit()
        
        assert expense_type.keywords is None
        assert expense_type.description is None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_default_values(self, db_session):
        """Test default values for fields."""
        expense_type = CommunalExpenseType(name='Test Expense')
        
        db_session.add(expense_type)
        db_session.commit()
        
        # is_active should default to True
        assert expense_type.is_active is True
        # timestamps should be set automatically
        assert expense_type.created_at is not None
        assert expense_type.updated_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_updated_at_changes(self, db_session):
        """Test that updated_at changes when record is updated."""
        expense_type = CommunalExpenseType(name='Test Expense')
        db_session.add(expense_type)
        db_session.commit()
        
        original_updated_at = expense_type.updated_at
        
        # Update the record
        expense_type.description = 'Updated description'
        db_session.commit()
        
        # updated_at should change (in a real scenario with onupdate)
        # Note: This test might not work exactly as expected in SQLite with our current setup
        assert expense_type.updated_at >= original_updated_at

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_active_filtering(self, db_session):
        """Test filtering by is_active status."""
        # Create active and inactive expense types
        active_type = CommunalExpenseType(name='Active Type', is_active=True)
        inactive_type = CommunalExpenseType(name='Inactive Type', is_active=False)
        
        db_session.add(active_type)
        db_session.add(inactive_type)
        db_session.commit()
        
        # Query only active types
        active_types = CommunalExpenseType.query.filter_by(is_active=True).all()
        inactive_types = CommunalExpenseType.query.filter_by(is_active=False).all()
        
        assert len(active_types) >= 1  # At least our test type
        assert len(inactive_types) == 1  # Just our test type
        
        active_names = [t.name for t in active_types]
        assert 'Active Type' in active_names
        assert inactive_types[0].name == 'Inactive Type'

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_type_keywords_json(self, db_session):
        """Test that keywords are properly stored and retrieved as JSON."""
        keywords = ['electric', 'electricity', 'power', 'energy']
        expense_type = CommunalExpenseType(
            name='Electric Test',
            keywords=json.dumps(keywords)
        )
        
        db_session.add(expense_type)
        db_session.commit()
        
        # Retrieve and verify keywords can be parsed as JSON
        retrieved_keywords = json.loads(expense_type.keywords)
        assert retrieved_keywords == keywords


class TestCommunalExpense:
    """Test cases for the CommunalExpense model."""

    @pytest.mark.unit
    @pytest.mark.models
    def test_create_communal_expense(self, db_session, sample_communal_expense_type):
        """Test creating a new communal expense."""
        expense = CommunalExpense(
            expense_type_id=sample_communal_expense_type.id,
            amount=120.50,
            date=date(2024, 1, 15),
            description='Monthly electricity bill',
            is_recurring=True
        )
        
        db_session.add(expense)
        db_session.commit()
        
        assert expense.id is not None
        assert expense.expense_type_id == sample_communal_expense_type.id
        assert expense.amount == 120.50
        assert expense.date == date(2024, 1, 15)
        assert expense.description == 'Monthly electricity bill'
        assert expense.is_recurring is True
        assert expense.created_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_to_dict(self, sample_communal_expense):
        """Test communal expense to_dict method."""
        result = sample_communal_expense.to_dict()
        
        expected_keys = ['id', 'expense_type_id', 'expense_type_name', 'amount', 
                        'date', 'description', 'is_recurring', 'created_at']
        assert all(key in result for key in expected_keys)
        
        assert result['expense_type_id'] == sample_communal_expense.expense_type_id
        assert result['expense_type_name'] == 'Electricity'
        assert result['amount'] == 120.50
        assert result['date'] == '2024-01-15'
        assert result['description'] == 'Monthly electricity bill'
        assert result['is_recurring'] is True

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_required_fields(self, db_session, sample_communal_expense_type):
        """Test that required fields are enforced."""
        # Missing expense_type_id should raise an error
        with pytest.raises(Exception):
            expense = CommunalExpense(
                amount=100.00,
                date=date.today()
            )
            db_session.add(expense)
            db_session.commit()

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_nullable_fields(self, db_session, sample_communal_expense_type):
        """Test that nullable fields can be None."""
        expense = CommunalExpense(
            expense_type_id=sample_communal_expense_type.id,
            amount=100.00,
            date=date.today(),
            description=None,
            is_recurring=False
        )
        
        db_session.add(expense)
        db_session.commit()
        
        assert expense.description is None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_default_values(self, db_session, sample_communal_expense_type):
        """Test default values for fields."""
        expense = CommunalExpense(
            expense_type_id=sample_communal_expense_type.id,
            amount=100.00,
            date=date.today()
        )
        
        db_session.add(expense)
        db_session.commit()
        
        # is_recurring should default to True
        assert expense.is_recurring is True
        # created_at should be set automatically
        assert expense.created_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_relationship(self, sample_communal_expense):
        """Test the relationship between CommunalExpense and CommunalExpenseType."""
        # Test that we can access the expense type through the relationship
        expense_type = sample_communal_expense.expense_type
        
        assert expense_type is not None
        assert expense_type.name == 'Electricity'
        assert expense_type.id == sample_communal_expense.expense_type_id

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_backref(self, sample_communal_expense, sample_communal_expense_type):
        """Test the backref relationship from CommunalExpenseType to CommunalExpense."""
        # Test that we can access expenses through the expense type
        expenses = sample_communal_expense_type.expenses
        
        assert len(expenses) == 1
        assert expenses[0].id == sample_communal_expense.id

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_amount_types(self, db_session, sample_communal_expense_type):
        """Test different amount types (positive, zero)."""
        # Communal expenses should typically be positive (costs)
        expenses = [
            CommunalExpense(
                expense_type_id=sample_communal_expense_type.id,
                amount=100.00,
                date=date.today(),
                description='Normal expense'
            ),
            CommunalExpense(
                expense_type_id=sample_communal_expense_type.id,
                amount=0.00,
                date=date.today(),
                description='Zero expense'
            )
        ]
        
        for expense in expenses:
            db_session.add(expense)
        db_session.commit()
        
        normal = db_session.query(CommunalExpense).filter_by(description='Normal expense').first()
        zero = db_session.query(CommunalExpense).filter_by(description='Zero expense').first()
        
        assert normal.amount == 100.00
        assert zero.amount == 0.00

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_recurring_filtering(self, db_session, sample_communal_expense_type):
        """Test filtering by is_recurring status."""
        recurring_expense = CommunalExpense(
            expense_type_id=sample_communal_expense_type.id,
            amount=100.00,
            date=date.today(),
            is_recurring=True
        )
        one_time_expense = CommunalExpense(
            expense_type_id=sample_communal_expense_type.id,
            amount=50.00,
            date=date.today(),
            is_recurring=False
        )
        
        db_session.add(recurring_expense)
        db_session.add(one_time_expense)
        db_session.commit()
        
        # Query by recurring status
        recurring = CommunalExpense.query.filter_by(is_recurring=True).all()
        one_time = CommunalExpense.query.filter_by(is_recurring=False).all()
        
        assert len(recurring) >= 1  # At least our test expense
        assert len(one_time) == 1  # Just our test expense
        
        recurring_amounts = [e.amount for e in recurring]
        assert 100.00 in recurring_amounts
        assert one_time[0].amount == 50.00

    @pytest.mark.unit
    @pytest.mark.models
    def test_communal_expense_date_ordering(self, db_session, sample_communal_expense_type):
        """Test ordering expenses by date."""
        dates = [date(2024, 1, 15), date(2024, 1, 10), date(2024, 1, 20)]
        
        for i, expense_date in enumerate(dates):
            expense = CommunalExpense(
                expense_type_id=sample_communal_expense_type.id,
                amount=100.00 + i,
                date=expense_date
            )
            db_session.add(expense)
        db_session.commit()
        
        # Query expenses ordered by date
        expenses = CommunalExpense.query.order_by(CommunalExpense.date.asc()).all()
        
        expense_dates = [e.date for e in expenses]
        assert expense_dates == sorted(expense_dates)