import React, { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Save, X, AlertTriangle, Settings as SettingsIcon } from 'lucide-react'
import { settingsApi, resetApi } from '../services/api'

const Settings = () => {
  const [communalExpenseTypes, setCommunalExpenseTypes] = useState([])
  const [editingType, setEditingType] = useState(null)
  const [newType, setNewType] = useState({ name: '', keywords: '', description: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [resetting, setResetting] = useState(false)

  useEffect(() => {
    loadCommunalExpenseTypes()
  }, [])

  const loadCommunalExpenseTypes = async () => {
    try {
      setLoading(true)
      const response = await settingsApi.getCommunalExpenseTypes()
      setCommunalExpenseTypes(response.data)
    } catch (err) {
      setError(`Failed to load settings: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleAddType = async (e) => {
    e.preventDefault()
    if (!newType.name.trim()) return

    try {
      const keywordsArray = newType.keywords.split(',').map(k => k.trim()).filter(k => k.length > 0)
      await settingsApi.createCommunalExpenseType({
        name: newType.name.trim(),
        keywords: keywordsArray,
        description: newType.description.trim()
      })
      
      setNewType({ name: '', keywords: '', description: '' })
      setShowAddForm(false)
      await loadCommunalExpenseTypes()
    } catch (err) {
      setError(`Failed to create expense type: ${err.response?.data?.error || err.message}`)
    }
  }

  const handleEditType = (type) => {
    setEditingType({
      ...type,
      keywords: Array.isArray(JSON.parse(type.keywords || '[]')) 
        ? JSON.parse(type.keywords || '[]').join(', ')
        : ''
    })
  }

  const handleUpdateType = async (e) => {
    e.preventDefault()
    if (!editingType.name.trim()) return

    try {
      const keywordsArray = editingType.keywords.split(',').map(k => k.trim()).filter(k => k.length > 0)
      await settingsApi.updateCommunalExpenseType(editingType.id, {
        name: editingType.name.trim(),
        keywords: keywordsArray,
        description: editingType.description.trim()
      })
      
      setEditingType(null)
      await loadCommunalExpenseTypes()
    } catch (err) {
      setError(`Failed to update expense type: ${err.response?.data?.error || err.message}`)
    }
  }

  const handleDeleteType = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return

    try {
      await settingsApi.deleteCommunalExpenseType(id)
      await loadCommunalExpenseTypes()
    } catch (err) {
      setError(`Failed to delete expense type: ${err.response?.data?.error || err.message}`)
    }
  }

  const handleResetAll = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to reset ALL data? This will delete:\n\n' +
      '• All transactions\n' +
      '• All categories\n' +
      '• All communal expense settings\n\n' +
      'This action cannot be undone!'
    )
    
    if (!confirmed) return

    try {
      setResetting(true)
      await resetApi.all()
      await loadCommunalExpenseTypes()
      alert('All data has been reset successfully!')
    } catch (err) {
      setError(`Reset failed: ${err.response?.data?.error || err.message}`)
    } finally {
      setResetting(false)
    }
  }

  const handleResetTransactions = async () => {
    if (!window.confirm('Are you sure you want to delete all transactions? This cannot be undone!')) return

    try {
      await resetApi.transactions()
      alert('All transactions have been deleted successfully!')
    } catch (err) {
      setError(`Failed to reset transactions: ${err.response?.data?.error || err.message}`)
    }
  }

  const handleResetCommunalExpenses = async () => {
    if (!window.confirm('Are you sure you want to reset communal expense settings to defaults?')) return

    try {
      await settingsApi.resetCommunalExpenses()
      await loadCommunalExpenseTypes()
      alert('Communal expenses have been reset to defaults!')
    } catch (err) {
      setError(`Failed to reset communal expenses: ${err.response?.data?.error || err.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <SettingsIcon className="mr-2" size={28} />
          Settings
        </h2>
        <p className="text-gray-600">Configure your personal finance tracker</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="text-red-500 mr-2" size={20} />
            <p className="text-red-700">{error}</p>
          </div>
          <button 
            onClick={() => setError('')}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Communal Expenses Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Communal Expenses</h3>
            <p className="text-gray-600 text-sm">Configure expense types for bills, utilities, and shared costs</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Plus size={16} className="mr-1" />
            Add Type
          </button>
        </div>

        {/* Add New Type Form */}
        {showAddForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Add New Communal Expense Type</h4>
            <form onSubmit={handleAddType} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={newType.name}
                    onChange={(e) => setNewType({ ...newType, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., Electricity"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
                  <input
                    type="text"
                    value={newType.keywords}
                    onChange={(e) => setNewType({ ...newType, keywords: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="electric, power, edf (comma-separated)"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newType.description}
                  onChange={(e) => setNewType({ ...newType, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Description of this expense type"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Add Type
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Expense Types List */}
        <div className="space-y-4">
          {communalExpenseTypes.map((type) => (
            <div key={type.id} className="border border-gray-200 rounded-lg p-4">
              {editingType && editingType.id === type.id ? (
                <form onSubmit={handleUpdateType} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                      <input
                        type="text"
                        value={editingType.name}
                        onChange={(e) => setEditingType({ ...editingType, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
                      <input
                        type="text"
                        value={editingType.keywords}
                        onChange={(e) => setEditingType({ ...editingType, keywords: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <input
                      type="text"
                      value={editingType.description || ''}
                      onChange={(e) => setEditingType({ ...editingType, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setEditingType(null)}
                      className="flex items-center px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      <X size={16} className="mr-1" />
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <Save size={16} className="mr-1" />
                      Save
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{type.name}</h4>
                    {type.description && (
                      <p className="text-sm text-gray-600 mt-1">{type.description}</p>
                    )}
                    {type.keywords && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-500 mb-1">Keywords:</p>
                        <div className="flex flex-wrap gap-1">
                          {JSON.parse(type.keywords || '[]').map((keyword, index) => (
                            <span
                              key={index}
                              className="inline-flex px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEditType(type)}
                      className="flex items-center px-3 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => handleDeleteType(type.id, type.name)}
                      className="flex items-center px-3 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {communalExpenseTypes.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No communal expense types configured</p>
            <p className="text-sm text-gray-400 mt-1">Add some expense types to automatically categorize your bills</p>
          </div>
        )}
      </div>

      {/* Data Management Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Management</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
            <h4 className="font-medium text-yellow-800 mb-2">Reset Transactions</h4>
            <p className="text-sm text-yellow-700 mb-3">Delete all transaction data while keeping categories and settings</p>
            <button
              onClick={handleResetTransactions}
              className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
            >
              Reset Transactions
            </button>
          </div>
          
          <div className="border border-orange-200 rounded-lg p-4 bg-orange-50">
            <h4 className="font-medium text-orange-800 mb-2">Reset Communal Expenses</h4>
            <p className="text-sm text-orange-700 mb-3">Reset communal expense types to default settings</p>
            <button
              onClick={handleResetCommunalExpenses}
              className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
            >
              Reset to Defaults
            </button>
          </div>
          
          <div className="border border-red-200 rounded-lg p-4 bg-red-50">
            <h4 className="font-medium text-red-800 mb-2">Reset All Data</h4>
            <p className="text-sm text-red-700 mb-3">Delete ALL data including transactions, categories, and settings</p>
            <button
              onClick={handleResetAll}
              disabled={resetting}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {resetting ? 'Resetting...' : 'Reset Everything'}
            </button>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="font-medium text-blue-800 mb-3">ℹ️ How Communal Expenses Work</h4>
        <div className="text-sm text-blue-700 space-y-2">
          <p>• <strong>Keywords:</strong> Add words that commonly appear in these expense descriptions (e.g., "electric", "power", "edf" for electricity bills)</p>
          <p>• <strong>Automatic Categorization:</strong> New transactions will be automatically categorized as "Communal - [Type Name]" when keywords match</p>
          <p>• <strong>Priority:</strong> Communal expense matching takes priority over regular category matching</p>
          <p>• <strong>Case Insensitive:</strong> Keywords are matched regardless of uppercase/lowercase</p>
        </div>
      </div>
    </div>
  )
}

export default Settings