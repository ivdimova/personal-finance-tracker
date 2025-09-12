#!/bin/bash

# Personal Finance Tracker - Test Runner Script
# This script runs both backend and frontend tests

set -e  # Exit on any error

echo "🧪 Personal Finance Tracker Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default options
run_backend=true
run_frontend=true
run_coverage=false
run_integration=false
quick_mode=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            run_frontend=false
            shift
            ;;
        --frontend-only)
            run_backend=false
            shift
            ;;
        --coverage)
            run_coverage=true
            shift
            ;;
        --integration)
            run_integration=true
            shift
            ;;
        --quick)
            quick_mode=true
            run_integration=false
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend-only    Run only backend tests"
            echo "  --frontend-only   Run only frontend tests"
            echo "  --coverage        Generate coverage reports"
            echo "  --integration     Include integration tests"
            echo "  --quick           Run only unit tests (fastest)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if virtual environment exists for backend
if [ "$run_backend" = true ]; then
    if [ ! -d "venv" ]; then
        print_error "Python virtual environment not found. Please create it first:"
        echo "python -m venv venv"
        echo "source venv/bin/activate"
        echo "pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if node_modules exists for frontend
if [ "$run_frontend" = true ]; then
    if [ ! -d "node_modules" ]; then
        print_error "Node modules not found. Please install them first:"
        echo "npm install"
        exit 1
    fi
fi

# Backend Tests
if [ "$run_backend" = true ]; then
    print_status "Running Backend Tests (Python/Flask)"
    echo "----------------------------------------"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Build test command
    test_cmd="python -m pytest"
    
    if [ "$quick_mode" = true ]; then
        test_cmd="$test_cmd -m 'unit and not slow'"
        print_status "Quick mode: Running only fast unit tests"
    elif [ "$run_integration" = true ]; then
        test_cmd="$test_cmd"
        print_status "Running all tests including integration tests"
    else
        test_cmd="$test_cmd -m 'not slow'"
        print_status "Running unit tests (excluding slow tests)"
    fi
    
    if [ "$run_coverage" = true ]; then
        test_cmd="$test_cmd --cov=src --cov-report=html:htmlcov --cov-report=term-missing"
        print_status "Coverage reporting enabled"
    fi
    
    # Add verbose output
    test_cmd="$test_cmd -v"
    
    echo "Executing: $test_cmd"
    echo ""
    
    if $test_cmd; then
        print_success "Backend tests passed!"
        
        if [ "$run_coverage" = true ]; then
            print_status "Backend coverage report generated: htmlcov/index.html"
        fi
    else
        print_error "Backend tests failed!"
        exit 1
    fi
    
    echo ""
fi

# Frontend Tests
if [ "$run_frontend" = true ]; then
    print_status "Running Frontend Tests (React/Jest)"
    echo "----------------------------------------"
    
    # Build test command
    if [ "$run_coverage" = true ]; then
        test_cmd="npm run test:coverage"
        print_status "Coverage reporting enabled"
    else
        test_cmd="npm test -- --watchAll=false"
    fi
    
    echo "Executing: $test_cmd"
    echo ""
    
    if $test_cmd; then
        print_success "Frontend tests passed!"
        
        if [ "$run_coverage" = true ]; then
            print_status "Frontend coverage report generated: coverage-frontend/lcov-report/index.html"
        fi
    else
        print_error "Frontend tests failed!"
        exit 1
    fi
    
    echo ""
fi

# Summary
echo "🎉 Test Summary"
echo "==============="

if [ "$run_backend" = true ]; then
    print_success "✓ Backend tests completed"
fi

if [ "$run_frontend" = true ]; then
    print_success "✓ Frontend tests completed"
fi

if [ "$run_coverage" = true ]; then
    echo ""
    print_status "Coverage reports:"
    if [ "$run_backend" = true ]; then
        echo "  - Backend: htmlcov/index.html"
    fi
    if [ "$run_frontend" = true ]; then
        echo "  - Frontend: coverage-frontend/lcov-report/index.html"
    fi
fi

echo ""
print_success "All tests completed successfully! 🚀"