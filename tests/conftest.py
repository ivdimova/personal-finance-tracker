"""
Main test configuration and fixtures for the personal finance tracker application.

This file contains shared fixtures and configuration used across all test modules.
"""
import os
import tempfile
import pytest
from datetime import datetime, date
import json
from flask import Flask
from src.main import app as _app
from src.models.user import db
from src.models.transaction import Transaction, Category
from src.models.communal_expense import CommunalExpenseType, CommunalExpense


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test session."""
    # Create a temporary file to serve as the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the Flask app for testing
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    # Create the database tables
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()
    
    # Close and remove the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a clean database session for each test."""
    with app.app_context():
        # Clear all tables
        db.session.query(Transaction).delete()
        db.session.query(Category).delete()
        db.session.query(CommunalExpense).delete()
        db.session.query(CommunalExpenseType).delete()
        db.session.commit()
        yield db.session
        db.session.rollback()


@pytest.fixture
def sample_category(db_session):
    """Create a sample category for testing."""
    category = Category(
        name='Food & Dining',
        keywords=json.dumps(['restaurant', 'cafe', 'food']),
        color='#FF6B6B'
    )
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def sample_categories(db_session):
    """Create multiple sample categories for testing."""
    categories = [
        Category(
            name='Food & Dining',
            keywords=json.dumps(['restaurant', 'cafe', 'food', 'grocery']),
            color='#FF6B6B'
        ),
        Category(
            name='Transportation',
            keywords=json.dumps(['uber', 'taxi', 'bus', 'gas', 'fuel']),
            color='#4ECDC4'
        ),
        Category(
            name='Bills & Utilities',
            keywords=json.dumps(['electric', 'water', 'internet', 'phone']),
            color='#FFEAA7'
        ),
        Category(
            name='Income',
            keywords=json.dumps(['salary', 'payroll', 'deposit']),
            color='#98D8C8'
        )
    ]
    
    for category in categories:
        db_session.add(category)
    db_session.commit()
    return categories


@pytest.fixture
def sample_transaction(db_session, sample_category):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        date=date(2024, 1, 15),
        description='Test Restaurant Purchase',
        amount=-25.50,
        category='Food & Dining',
        account='Main Account'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


@pytest.fixture
def sample_transactions(db_session, sample_categories):
    """Create multiple sample transactions for testing."""
    transactions = [
        Transaction(
            date=date(2024, 1, 15),
            description='Restaurant ABC',
            amount=-25.50,
            category='Food & Dining',
            account='Main Account'
        ),
        Transaction(
            date=date(2024, 1, 14),
            description='Uber ride to work',
            amount=-12.30,
            category='Transportation',
            account='Main Account'
        ),
        Transaction(
            date=date(2024, 1, 13),
            description='Salary deposit',
            amount=2500.00,
            category='Income',
            account='Main Account'
        ),
        Transaction(
            date=date(2024, 1, 12),
            description='Electric bill',
            amount=-89.45,
            category='Bills & Utilities',
            account='Main Account'
        ),
        Transaction(
            date=date(2024, 1, 11),
            description='Grocery shopping',
            amount=-67.20,
            category='Food & Dining',
            account='Main Account'
        )
    ]
    
    for transaction in transactions:
        db_session.add(transaction)
    db_session.commit()
    return transactions


@pytest.fixture
def sample_communal_expense_type(db_session):
    """Create a sample communal expense type for testing."""
    expense_type = CommunalExpenseType(
        name='Electricity',
        keywords=json.dumps(['electric', 'power', 'edf']),
        description='Electricity and power bills',
        is_active=True
    )
    db_session.add(expense_type)
    db_session.commit()
    return expense_type


@pytest.fixture
def sample_communal_expense(db_session, sample_communal_expense_type):
    """Create a sample communal expense for testing."""
    expense = CommunalExpense(
        expense_type_id=sample_communal_expense_type.id,
        amount=120.50,
        date=date(2024, 1, 15),
        description='Monthly electricity bill',
        is_recurring=True
    )
    db_session.add(expense)
    db_session.commit()
    return expense


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing import functionality."""
    return [
        ['Date', 'Description', 'Amount', 'Category'],
        ['2024-01-15', 'Restaurant ABC', '-25.50', ''],
        ['2024-01-14', 'Salary deposit', '2500.00', ''],
        ['2024-01-13', 'Uber ride', '-12.30', ''],
        ['2024-01-12', 'Electric bill', '-89.45', '']
    ]


@pytest.fixture
def sample_caixabank_csv():
    """Sample CaixaBank format CSV for testing."""
    return """Date;Amount;Description;Account
15/01/2024;-25,50;Restaurant ABC;ES12 3456 7890 1234 5678 9012
14/01/2024;2500,00;SALARY DEPOSIT COMPANY XYZ;ES12 3456 7890 1234 5678 9012
13/01/2024;-12,30;UBER TRIP 123;ES12 3456 7890 1234 5678 9012
12/01/2024;-89,45;ELECTRIC COMPANY - MONTHLY;ES12 3456 7890 1234 5678 9012"""


@pytest.fixture
def sample_space_delimited_csv():
    """Sample space-delimited CSV for testing."""
    return """2024-01-15 -25.50 "Restaurant ABC" MainAccount
2024-01-14 2500.00 "SALARY DEPOSIT" MainAccount
2024-01-13 -12.30 "Uber trip" MainAccount
2024-01-12 -89.45 "Electric bill" MainAccount"""


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing file uploads."""
    csv_file = tmp_path / "test_transactions.csv"
    csv_content = """Date,Description,Amount,Category
2024-01-15,Restaurant ABC,-25.50,
2024-01-14,Salary deposit,2500.00,
2024-01-13,Uber ride,-12.30,
2024-01-12,Electric bill,-89.45,"""
    
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def temp_receipt_file(tmp_path):
    """Create a temporary image file for testing receipt uploads."""
    # This would typically be a real image file, but for testing we'll use a simple file
    receipt_file = tmp_path / "test_receipt.jpg"
    receipt_file.write_bytes(b"fake_image_data_for_testing")
    return receipt_file


@pytest.fixture
def mock_ocr_result():
    """Mock OCR result for testing receipt processing."""
    return {
        'text': 'RESTAURANT ABC\n123 Main St\nReceipt #12345\nDate: 2024-01-15\nBurger: $12.50\nDrink: $3.50\nTax: $1.60\nTotal: $17.60\nThank you!',
        'merchant': 'Restaurant ABC',
        'total': 17.60,
        'date': '2024-01-15'
    }


# Helper functions for testing
def create_test_transaction(**kwargs):
    """Helper function to create a test transaction with default values."""
    defaults = {
        'date': date.today(),
        'description': 'Test Transaction',
        'amount': -10.00,
        'category': 'Other',
        'account': 'Test Account'
    }
    defaults.update(kwargs)
    return Transaction(**defaults)


def create_test_category(**kwargs):
    """Helper function to create a test category with default values."""
    defaults = {
        'name': 'Test Category',
        'keywords': json.dumps(['test']),
        'color': '#FFFFFF'
    }
    defaults.update(kwargs)
    return Category(**defaults)


def create_test_communal_expense_type(**kwargs):
    """Helper function to create a test communal expense type with default values."""
    defaults = {
        'name': 'Test Expense',
        'keywords': json.dumps(['test']),
        'description': 'Test expense type',
        'is_active': True
    }
    defaults.update(kwargs)
    return CommunalExpenseType(**defaults)