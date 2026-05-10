import React, { useState, useEffect } from 'react'
import { Filter, TrendingUp, TrendingDown, DollarSign, AlertCircle, Pencil, Trash2 } from 'lucide-react'
import { transactionsApi, categoriesApi } from '../services/api'

const Transactions = () => {
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingCategoryId, setEditingCategoryId] = useState(null)

  useEffect(() => {
    loadCategories()
  }, [])

  useEffect(() => {
    loadTransactions()
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      const response = await categoriesApi.getAll()
      setCategories(response.data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }

  const loadTransactions = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await transactionsApi.getAll(selectedCategory)
      setTransactions(response.data.transactions)
      setSummary(response.data.summary)
    } catch (err) {
      setError(`Failed to load transactions: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const formatAmount = (amount) => {
    const absAmount = Math.abs(amount)
    return amount >= 0 ? `+€${absAmount.toFixed(2)}` : `-€${absAmount.toFixed(2)}`
  }

  const getAmountClass = (amount) => {
    return amount >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'
  }

  const handleDelete = async (transactionId) => {
    if (!window.confirm('Delete this transaction?')) return
    try {
      await transactionsApi.delete(transactionId)
      loadTransactions()
    } catch (err) {
      setError('Failed to delete transaction. Please try again.')
    }
  }

  const handleCategoryChange = async (transactionId, newCategory) => {
    try {
      await transactionsApi.updateCategory(transactionId, newCategory)
      setTransactions((prev) =>
        prev.map((t) =>
          t.id === transactionId ? { ...t, category: newCategory } : t
        )
      )
      setEditingCategoryId(null)
      loadTransactions()
    } catch (err) {
      console.error('Failed to update category:', err)
      setError('Failed to update category. Please try again.')
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="text-red-500 mr-2" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
        <button 
          onClick={loadTransactions}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Transactions</h2>
          <p className="text-gray-600">View and filter your transaction history</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="flex items-center space-x-4">
          <Filter size={20} className="text-gray-500" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="flex-1 max-w-xs px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.name}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary Section */}
      {summary && selectedCategory && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {selectedCategory} - Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Transactions</p>
                  <p className="text-xl font-bold text-gray-900">{summary.transaction_count}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-700">Income</p>
                  <p className="text-xl font-bold text-green-900">€{summary.income_total.toFixed(2)}</p>
                </div>
                <TrendingUp className="text-green-600" size={24} />
              </div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-700">Expenses</p>
                  <p className="text-xl font-bold text-red-900">€{summary.expense_total.toFixed(2)}</p>
                </div>
                <TrendingDown className="text-red-600" size={24} />
              </div>
            </div>
            
            <div className={`p-4 rounded-lg ${summary.net_amount >= 0 ? 'bg-blue-50' : 'bg-orange-50'}`}>
              <div className="flex items-center">
                <div className="flex-1">
                  <p className={`text-sm font-medium ${summary.net_amount >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                    Net Amount
                  </p>
                  <p className={`text-xl font-bold ${summary.net_amount >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
                    €{summary.net_amount.toFixed(2)}
                  </p>
                </div>
                <DollarSign className={`${summary.net_amount >= 0 ? 'text-blue-600' : 'text-orange-600'}`} size={24} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No transactions found</p>
            <p className="text-gray-400 text-sm mt-1">
              {selectedCategory ? 'Try selecting a different category' : 'Upload a CSV file to get started'}
            </p>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-purple-600">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-6 py-3"></th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {transaction.description || 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(transaction.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getAmountClass(transaction.amount)}>
                          {formatAmount(transaction.amount)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {editingCategoryId === transaction.id ? (
                          <select
                            value={transaction.category || ''}
                            onChange={(e) => handleCategoryChange(transaction.id, e.target.value)}
                            onBlur={() => setEditingCategoryId(null)}
                            autoFocus
                            className="text-xs px-2 py-1 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          >
                            {categories.map((cat) => (
                              <option key={cat.id} value={cat.name}>{cat.name}</option>
                            ))}
                          </select>
                        ) : (
                          <span
                            onClick={() => setEditingCategoryId(transaction.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full cursor-pointer hover:bg-purple-200 hover:shadow-sm transition-all group"
                            title="Click to change category"
                          >
                            {transaction.category || 'Uncategorized'}
                            <Pencil size={11} className="text-purple-400 group-hover:text-purple-600 transition-colors" />
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {transaction.account || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleDelete(transaction.id)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                          title="Delete transaction"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden divide-y divide-gray-200">
              {transactions.map((transaction, index) => (
                <div key={index} className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{transaction.description || 'N/A'}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(transaction.date).toLocaleDateString()}
                        {transaction.account && ` • ${transaction.account}`}
                      </p>
                      {editingCategoryId === transaction.id ? (
                        <select
                          value={transaction.category || ''}
                          onChange={(e) => handleCategoryChange(transaction.id, e.target.value)}
                          onBlur={() => setEditingCategoryId(null)}
                          autoFocus
                          className="text-xs px-2 py-1 mt-2 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        >
                          {categories.map((cat) => (
                            <option key={cat.id} value={cat.name}>{cat.name}</option>
                          ))}
                        </select>
                      ) : (
                        <span
                          onClick={() => setEditingCategoryId(transaction.id)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full mt-2 cursor-pointer hover:bg-purple-200 hover:shadow-sm transition-all group"
                          title="Click to change category"
                        >
                          {transaction.category || 'Uncategorized'}
                          <Pencil size={11} className="text-purple-400 group-hover:text-purple-600 transition-colors" />
                        </span>
                      )}
                    </div>
                    <div className="ml-4 flex flex-col items-end gap-2">
                      <span className={getAmountClass(transaction.amount)}>
                        {formatAmount(transaction.amount)}
                      </span>
                      <button
                        onClick={() => handleDelete(transaction.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        title="Delete transaction"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Transactions