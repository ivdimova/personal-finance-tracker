import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, TrendingUp, TrendingDown, DollarSign, FileText, AlertCircle } from 'lucide-react'
import { analyticsApi, transactionsApi } from '../services/api'
import FileUpload from './FileUpload'

const Dashboard = () => {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError('')

      // Load expense summary and recent transactions in parallel
      const [summaryResponse, transactionsResponse] = await Promise.all([
        analyticsApi.getExpenseSummary(),
        transactionsApi.getAll()
      ])

      setSummary(summaryResponse.data)
      setRecentTransactions(transactionsResponse.data.transactions.slice(0, 5))
    } catch (err) {
      setError(`Failed to load dashboard data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = () => {
    setShowUpload(false)
    loadDashboardData() // Reload data after successful upload
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="text-red-500 mr-2" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
        <button 
          onClick={loadDashboardData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Your Finance Dashboard</h2>
        <p className="text-gray-600">Track your expenses, upload receipts, and manage your financial data</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center justify-center p-6 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all duration-200 shadow-lg"
        >
          <Upload className="mr-3" size={24} />
          <span className="text-lg font-semibold">Upload CSV File</span>
        </button>
        
        <button
          onClick={() => navigate('/transactions')}
          className="flex items-center justify-center p-6 bg-gradient-to-r from-blue-500 to-cyan-600 text-white rounded-xl hover:from-blue-600 hover:to-cyan-700 transition-all duration-200 shadow-lg"
        >
          <FileText className="mr-3" size={24} />
          <span className="text-lg font-semibold">View All Transactions</span>
        </button>
      </div>

      {/* Financial Summary */}
      {summary && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Financial Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-700 text-sm font-medium">Total Income</p>
                  <p className="text-2xl font-bold text-green-900">€{summary.total_income.toFixed(2)}</p>
                </div>
                <TrendingUp className="text-green-600" size={32} />
              </div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-700 text-sm font-medium">Total Expenses</p>
                  <p className="text-2xl font-bold text-red-900">€{summary.total_expenses.toFixed(2)}</p>
                </div>
                <TrendingDown className="text-red-600" size={32} />
              </div>
            </div>
            
            <div className={`p-4 rounded-lg border ${summary.net_amount >= 0 ? 'bg-blue-50 border-blue-200' : 'bg-orange-50 border-orange-200'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm font-medium ${summary.net_amount >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                    Net Amount
                  </p>
                  <p className={`text-2xl font-bold ${summary.net_amount >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
                    €{summary.net_amount.toFixed(2)}
                  </p>
                </div>
                <DollarSign className={`${summary.net_amount >= 0 ? 'text-blue-600' : 'text-orange-600'}`} size={32} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Categories */}
      {summary && summary.categories && summary.categories.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Top Spending Categories</h3>
          <div className="space-y-3">
            {summary.categories.slice(0, 5).map((category, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900">{category.name}</span>
                    <span className="text-sm font-semibold text-gray-700">
                      €{category.amount.toFixed(2)} ({category.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${category.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      {recentTransactions.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Recent Transactions</h3>
          <div className="space-y-2">
            {recentTransactions.map((transaction, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{transaction.description}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(transaction.date).toLocaleDateString()} • {transaction.category || 'Uncategorized'}
                  </p>
                </div>
                <span className={`font-semibold ${transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {transaction.amount >= 0 ? '+' : ''}€{Math.abs(transaction.amount).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Upload CSV File</h3>
              <button
                onClick={() => setShowUpload(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <FileUpload
              onSuccess={handleUploadSuccess}
              onError={(error) => setError(error)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard