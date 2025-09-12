"""
Unit tests for the Transaction model.

Tests the Transaction and Category models including their relationships,
validation, and data conversion methods.
"""
import pytest
import json
from datetime import date, datetime
from src.models.transaction import Transaction, Category


class TestTransaction:
    """Test cases for the Transaction model."""

    @pytest.mark.unit
    @pytest.mark.models
    def test_create_transaction(self, db_session):
        """Test creating a new transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            description='Test purchase',
            amount=-25.50,
            category='Food & Dining',
            account='Main Account'
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.date == date(2024, 1, 15)
        assert transaction.description == 'Test purchase'
        assert transaction.amount == -25.50
        assert transaction.category == 'Food & Dining'
        assert transaction.account == 'Main Account'
        assert transaction.created_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_to_dict(self, sample_transaction):
        """Test transaction to_dict method."""
        result = sample_transaction.to_dict()
        
        expected_keys = ['id', 'date', 'description', 'amount', 'category', 'account', 'created_at']
        assert all(key in result for key in expected_keys)
        
        assert result['date'] == '2024-01-15'
        assert result['description'] == 'Test Restaurant Purchase'
        assert result['amount'] == -25.50
        assert result['category'] == 'Food & Dining'
        assert result['account'] == 'Main Account'

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # Missing date should raise an error
        with pytest.raises(Exception):
            transaction = Transaction(
                description='Test',
                amount=-10.00
            )
            db_session.add(transaction)
            db_session.commit()

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_nullable_fields(self, db_session):
        """Test that nullable fields can be None."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            description='Test transaction',
            amount=-10.00,
            category=None,
            account=None
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.category is None
        assert transaction.account is None

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_amount_types(self, db_session):
        """Test different amount types (positive, negative, zero)."""
        transactions = [
            Transaction(date=date.today(), description='Income', amount=100.00),
            Transaction(date=date.today(), description='Expense', amount=-50.00),
            Transaction(date=date.today(), description='Zero', amount=0.00)
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        income = db_session.query(Transaction).filter_by(description='Income').first()
        expense = db_session.query(Transaction).filter_by(description='Expense').first()
        zero = db_session.query(Transaction).filter_by(description='Zero').first()
        
        assert income.amount == 100.00
        assert expense.amount == -50.00
        assert zero.amount == 0.00

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_ordering(self, sample_transactions):
        """Test that transactions can be ordered by date."""
        # Query transactions ordered by date descending
        transactions = Transaction.query.order_by(Transaction.date.desc()).all()
        
        dates = [t.date for t in transactions]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_filtering_by_category(self, sample_transactions):
        """Test filtering transactions by category."""
        food_transactions = Transaction.query.filter_by(category='Food & Dining').all()
        
        assert len(food_transactions) == 2  # Restaurant and grocery
        for transaction in food_transactions:
            assert transaction.category == 'Food & Dining'

    @pytest.mark.unit
    @pytest.mark.models
    def test_transaction_filtering_by_amount_range(self, sample_transactions):
        """Test filtering transactions by amount range."""
        # Find transactions between -100 and 0 (expenses)
        expenses = Transaction.query.filter(
            Transaction.amount >= -100,
            Transaction.amount < 0
        ).all()
        
        assert len(expenses) == 4  # All negative amounts except the large electric bill
        for transaction in expenses:
            assert -100 <= transaction.amount < 0


class TestCategory:
    """Test cases for the Category model."""

    @pytest.mark.unit
    @pytest.mark.models
    def test_create_category(self, db_session):
        """Test creating a new category."""
        category = Category(
            name='Test Category',
            keywords=json.dumps(['test', 'sample']),
            color='#FF0000'
        )
        
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == 'Test Category'
        assert category.keywords == json.dumps(['test', 'sample'])
        assert category.color == '#FF0000'

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_to_dict(self, sample_category):
        """Test category to_dict method."""
        result = sample_category.to_dict()
        
        expected_keys = ['id', 'name', 'keywords', 'color']
        assert all(key in result for key in expected_keys)
        
        assert result['name'] == 'Food & Dining'
        assert result['keywords'] == json.dumps(['restaurant', 'cafe', 'food'])
        assert result['color'] == '#FF6B6B'

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_unique_name(self, db_session, sample_category):
        """Test that category names must be unique."""
        # Try to create another category with the same name
        duplicate_category = Category(
            name='Food & Dining',
            keywords=json.dumps(['duplicate']),
            color='#00FF00'
        )
        
        db_session.add(duplicate_category)
        
        with pytest.raises(Exception):
            db_session.commit()

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_nullable_fields(self, db_session):
        """Test that nullable fields can be None."""
        category = Category(
            name='Minimal Category',
            keywords=None,
            color=None
        )
        
        db_session.add(category)
        db_session.commit()
        
        assert category.keywords is None
        assert category.color is None

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_keywords_json_format(self, db_session):
        """Test that keywords are stored and retrieved as JSON."""
        keywords = ['food', 'restaurant', 'dining']
        category = Category(
            name='Food Category',
            keywords=json.dumps(keywords),
            color='#FF6B6B'
        )
        
        db_session.add(category)
        db_session.commit()
        
        # Retrieve and verify keywords can be parsed as JSON
        retrieved_keywords = json.loads(category.keywords)
        assert retrieved_keywords == keywords

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_color_format(self, db_session):
        """Test that color field accepts hex color codes."""
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000']
        
        for i, color in enumerate(valid_colors):
            category = Category(
                name=f'Color Test {i}',
                color=color
            )
            db_session.add(category)
        
        db_session.commit()
        
        # Verify all colors were stored correctly
        categories = Category.query.filter(Category.name.like('Color Test%')).all()
        stored_colors = [cat.color for cat in categories]
        assert set(stored_colors) == set(valid_colors)

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_filtering_by_name(self, sample_categories):
        """Test filtering categories by name."""
        food_category = Category.query.filter_by(name='Food & Dining').first()
        
        assert food_category is not None
        assert food_category.name == 'Food & Dining'

    @pytest.mark.unit
    @pytest.mark.models
    def test_category_search_by_keyword(self, sample_categories):
        """Test searching categories by keywords (simulated)."""
        # This simulates how the application might search for categories by keyword
        search_keyword = 'uber'
        
        categories = Category.query.all()
        matching_categories = []
        
        for category in categories:
            if category.keywords:
                keywords = json.loads(category.keywords)
                if search_keyword in keywords:
                    matching_categories.append(category)
        
        assert len(matching_categories) == 1
        assert matching_categories[0].name == 'Transportation'