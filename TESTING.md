# Personal Finance Tracker - Testing Documentation

This document provides comprehensive information about the testing infrastructure and test suites for the Personal Finance Tracker application.

## Overview

The testing strategy covers both backend (Flask) and frontend (React) components with three main testing levels:

- **Unit Tests**: Test individual functions, methods, and components in isolation
- **Integration Tests**: Test interactions between components and complete workflows
- **End-to-End Tests**: Test complete user workflows across the entire application

## Backend Testing (Python/Flask)

### Test Infrastructure

- **Framework**: pytest with Flask-Testing
- **Coverage**: pytest-cov for code coverage reporting
- **Mocking**: pytest-mock for mocking dependencies
- **Database**: SQLite in-memory database for testing

### Backend Test Structure

```
tests/
├── conftest.py                    # Shared test fixtures and configuration
├── unit/                          # Unit tests
│   ├── models/                    # Database model tests
│   │   ├── test_transaction.py    # Transaction and Category model tests
│   │   └── test_communal_expense.py # Communal expense model tests
│   └── routes/                    # API route tests
│       ├── test_finance_simple.py  # Finance API endpoint tests
│       ├── test_settings_simple.py # Settings API endpoint tests
│       └── test_receipts_simple.py # Receipts API endpoint tests
└── integration/                   # Integration tests
    └── test_api_workflows.py      # End-to-end API workflow tests
```

### Running Backend Tests

#### Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock pytest-flask flask-testing
```

#### Run All Tests
```bash
# Run all backend tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage report
python -m pytest --cov=src --cov-report=html --cov-report=term-missing
```

#### Run Specific Test Categories
```bash
# Run only unit tests
python -m pytest -m unit

# Run only API tests
python -m pytest -m api

# Run only model tests
python -m pytest -m models

# Run only finance-related tests
python -m pytest -m finance

# Run only integration tests
python -m pytest -m integration
```

#### Run Specific Test Files
```bash
# Run model tests only
python -m pytest tests/unit/models/

# Run finance route tests
python -m pytest tests/unit/routes/test_finance_simple.py

# Run integration tests
python -m pytest tests/integration/
```

### Backend Test Categories

#### Model Tests (`tests/unit/models/`)
- **Transaction Model**: CRUD operations, data validation, relationships
- **Category Model**: Categorization logic, keyword matching
- **CommunalExpense Model**: Expense type management, recurring expenses

#### Route Tests (`tests/unit/routes/`)
- **Finance Routes**: CSV import, transaction management, analytics
- **Settings Routes**: Communal expense configuration
- **Receipts Routes**: File upload validation, OCR processing

#### Integration Tests (`tests/integration/`)
- **Transaction Workflows**: Complete CSV import to analytics pipeline
- **Communal Expense Workflows**: Type creation to expense management
- **Data Consistency**: Reset operations, data integrity
- **Error Recovery**: Graceful error handling across components

### Backend Test Coverage Goals

- **Models**: >90% coverage - comprehensive testing of business logic
- **Routes**: >80% coverage - all endpoints and error conditions
- **Integration**: >70% coverage - critical user workflows

## Frontend Testing (React/JavaScript)

### Test Infrastructure

- **Framework**: Jest with React Testing Library
- **Environment**: jsdom for DOM simulation
- **Utilities**: @testing-library/user-event for user interaction simulation

### Frontend Test Structure

```
tests/
└── frontend/
    ├── Dashboard.test.jsx          # Dashboard component tests
    ├── Transactions.test.jsx       # Transaction management tests
    ├── Receipts.test.jsx          # Receipt upload tests
    └── Settings.test.jsx          # Settings component tests
```

### Running Frontend Tests

#### Setup
```bash
# Install frontend test dependencies (if not already installed)
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom
```

#### Run Frontend Tests
```bash
# Run all frontend tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode during development
npm run test:watch
```

### Frontend Test Categories

#### Component Tests
- **Rendering**: Components render without crashing
- **Props**: Components handle props correctly
- **User Interactions**: Button clicks, form submissions
- **API Integration**: Mocked API calls and responses
- **Error Handling**: Component behavior during errors

#### Integration Tests
- **Navigation**: Route changes and navigation flows
- **Data Flow**: Data passing between components
- **Form Workflows**: Complete form submission flows

## Test Configuration

### pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests that test individual functions/methods in isolation
    integration: Integration tests that test component interactions
    slow: Slow running tests that may take more time to execute
    api: API endpoint tests for HTTP routes
    models: Database model tests
    receipts: Receipt processing and OCR related tests
    finance: Finance functionality tests including CSV import
    settings: Settings and configuration tests
```

### Jest Configuration (`jest.config.js`)

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapping: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.{js,jsx}',
    '<rootDir>/tests/frontend/**/*.spec.{js,jsx}',
  ],
  collectCoverageFrom: [
    'components/**/*.{js,jsx}',
    'services/**/*.{js,jsx}',
    '!**/node_modules/**',
    '!**/dist/**',
  ],
  coverageDirectory: 'coverage-frontend',
  coverageReporters: ['text', 'lcov', 'html'],
};
```

## Test Data and Fixtures

### Backend Fixtures (`tests/conftest.py`)

The test suite includes comprehensive fixtures for testing:

- **Database Setup**: Clean SQLite database for each test
- **Sample Data**: Pre-populated transactions, categories, communal expenses
- **Mock Data**: CSV files, receipt images for upload testing
- **Helper Functions**: Utilities for creating test data

### Key Fixtures:
- `app`: Flask application configured for testing
- `client`: Test client for API requests
- `db_session`: Clean database session for each test
- `sample_transactions`: Pre-populated transaction data
- `sample_categories`: Default category data
- `sample_communal_expense_type`: Communal expense type for testing
- `temp_csv_file`: Temporary CSV file for upload testing

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock pytest-flask flask-testing
    - name: Run backend tests
      run: python -m pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm install
    - name: Run frontend tests
      run: npm run test:coverage
```

## Test Best Practices

### Backend Testing Best Practices

1. **Test Structure**: Use AAA pattern (Arrange, Act, Assert)
2. **Isolation**: Each test should be independent and isolated
3. **Data Setup**: Use fixtures for consistent test data
4. **Mocking**: Mock external dependencies (APIs, file system, etc.)
5. **Edge Cases**: Test error conditions and edge cases
6. **Descriptive Names**: Test names should describe the scenario being tested

### Example Backend Test:
```python
@pytest.mark.unit
@pytest.mark.models
def test_transaction_categorization_with_keywords(self, app, sample_categories):
    """Test that transactions are categorized based on description keywords."""
    with app.app_context():
        # Arrange
        description = 'Dinner at Restaurant ABC'
        amount = -45.50
        
        # Act
        result = categorize_transaction(description, amount)
        
        # Assert
        assert result == 'Food & Dining'
```

### Frontend Testing Best Practices

1. **User-Centric Testing**: Test what users see and do
2. **Mock API Calls**: Use Jest mocks for API interactions
3. **Accessibility**: Test with screen readers in mind
4. **Error States**: Test loading and error states
5. **User Interactions**: Test actual user workflows

### Example Frontend Test:
```javascript
test('handles form submission correctly', async () => {
  // Arrange
  const mockSubmit = jest.fn();
  render(<TransactionForm onSubmit={mockSubmit} />);
  
  // Act
  await user.type(screen.getByLabelText(/description/i), 'Test Transaction');
  await user.type(screen.getByLabelText(/amount/i), '25.50');
  await user.click(screen.getByRole('button', { name: /submit/i }));
  
  // Assert
  expect(mockSubmit).toHaveBeenCalledWith({
    description: 'Test Transaction',
    amount: 25.50
  });
});
```

## Troubleshooting

### Common Backend Issues

1. **Database Conflicts**: Ensure tests use isolated database sessions
2. **Import Errors**: Check that all modules are properly imported
3. **Application Context**: Some tests need Flask application context
4. **Mock Issues**: Verify mocks are properly configured and reset

### Common Frontend Issues

1. **Component Not Found**: Ensure components are properly imported
2. **API Mocking**: Verify API mocks are configured correctly
3. **Async Testing**: Use proper async/await for asynchronous operations
4. **Environment Issues**: Ensure jsdom is properly configured

### Debug Commands

```bash
# Run single test with full output
python -m pytest tests/unit/models/test_transaction.py::TestTransaction::test_create_transaction -v -s

# Run tests with Python debugger
python -m pytest --pdb

# Run frontend tests in debug mode
npm test -- --watchAll=false --verbose
```

## Coverage Reports

After running tests with coverage, reports are generated in:

- **Backend**: `htmlcov/index.html` - HTML coverage report
- **Frontend**: `coverage-frontend/lcov-report/index.html` - HTML coverage report

Open these files in a browser to view detailed coverage information.

## Continuous Integration

The test suite is designed to run in CI/CD pipelines with:

- **Fast execution**: Most tests complete in under 30 seconds
- **Reliable results**: Tests are isolated and deterministic
- **Clear output**: Failures include detailed error information
- **Coverage reporting**: Integrated coverage tracking

## Adding New Tests

### For Backend Features:

1. Add test file in appropriate directory (`tests/unit/` or `tests/integration/`)
2. Use existing fixtures from `conftest.py`
3. Follow naming convention: `test_*.py`
4. Add appropriate pytest markers
5. Include both success and failure scenarios

### For Frontend Features:

1. Create test file alongside component: `ComponentName.test.jsx`
2. Mock external dependencies (APIs, services)
3. Test user interactions and component states
4. Include accessibility considerations

## Test Maintenance

- **Regular Updates**: Keep tests updated with code changes
- **Dependency Updates**: Update testing libraries regularly
- **Performance**: Monitor test execution time
- **Coverage**: Maintain high coverage levels
- **Documentation**: Keep test documentation current

This comprehensive testing infrastructure ensures the reliability, maintainability, and quality of the Personal Finance Tracker application.