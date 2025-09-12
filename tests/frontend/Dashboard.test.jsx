import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../../components/Dashboard';

// Mock the API services
jest.mock('../../services/api', () => ({
  analyticsApi: {
    getExpenseSummary: jest.fn(),
  },
  transactionsApi: {
    getAll: jest.fn(),
  },
}));

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('renders dashboard loading state', () => {
    // Mock API calls to hang (never resolve)
    const mockSummary = new Promise(() => {});
    const mockTransactions = new Promise(() => {});
    
    require('../../services/api').analyticsApi.getExpenseSummary.mockReturnValue(mockSummary);
    require('../../services/api').transactionsApi.getAll.mockReturnValue(mockTransactions);

    renderDashboard();
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('renders dashboard with mock data', async () => {
    // Mock successful API responses
    const mockSummaryResponse = {
      data: {
        total_income: 5000,
        total_expenses: -2000,
        net_amount: 3000,
        categories: [
          { name: 'Food & Dining', amount: 500, percentage: 25 },
          { name: 'Transportation', amount: 200, percentage: 10 },
        ],
      },
    };

    const mockTransactionsResponse = {
      data: {
        transactions: [
          {
            id: 1,
            date: '2024-01-15',
            description: 'Test Restaurant',
            amount: -25.50,
            category: 'Food & Dining',
          },
          {
            id: 2,
            date: '2024-01-14',
            description: 'Salary',
            amount: 2500.00,
            category: 'Income',
          },
        ],
      },
    };

    require('../../services/api').analyticsApi.getExpenseSummary.mockResolvedValue(mockSummaryResponse);
    require('../../services/api').transactionsApi.getAll.mockResolvedValue(mockTransactionsResponse);

    renderDashboard();

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Check that summary cards are rendered
    expect(screen.getByText(/total income/i)).toBeInTheDocument();
    expect(screen.getByText(/total expenses/i)).toBeInTheDocument();
    expect(screen.getByText(/net income/i)).toBeInTheDocument();

    // Check that recent transactions are shown
    expect(screen.getByText(/recent transactions/i)).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    // Mock API calls to reject
    const mockError = new Error('API Error');
    require('../../services/api').analyticsApi.getExpenseSummary.mockRejectedValue(mockError);
    require('../../services/api').transactionsApi.getAll.mockRejectedValue(mockError);

    renderDashboard();

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
    });
  });

  test('displays upload button', async () => {
    // Mock successful API responses with empty data
    const mockSummaryResponse = { data: { total_income: 0, total_expenses: 0, net_amount: 0, categories: [] } };
    const mockTransactionsResponse = { data: { transactions: [] } };

    require('../../services/api').analyticsApi.getExpenseSummary.mockResolvedValue(mockSummaryResponse);
    require('../../services/api').transactionsApi.getAll.mockResolvedValue(mockTransactionsResponse);

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Check for upload button
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    expect(uploadButton).toBeInTheDocument();
  });
});