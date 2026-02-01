import React, { useState, useEffect } from 'react'
import { Upload, FileText, Folder, AlertCircle, CheckCircle, X } from 'lucide-react'
import { receiptsApi } from '../services/api'

const Receipts = () => {
  const [receiptFolders, setReceiptFolders] = useState([])
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  useEffect(() => {
    loadReceiptFolders()
  }, [])

  const loadReceiptFolders = async () => {
    try {
      setLoading(true)
      const response = await receiptsApi.list()
      setReceiptFolders(response.data.folders || [])
    } catch (err) {
      setError(`Failed to load receipts: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (index) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    setError('')

    try {
      const response = await receiptsApi.upload(selectedFiles)
      setUploadResults(response.data)
      setSelectedFiles([])
      loadReceiptFolders() // Refresh the folder list
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.error || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const clearResults = () => {
    setUploadResults(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error && !uploadResults) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="text-red-500 mr-2" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
        <button 
          onClick={loadReceiptFolders}
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
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Receipt Manager</h2>
        <p className="text-gray-600">Upload and organize your receipts with automatic processing</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Receipts</h3>
        
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-purple-400 bg-purple-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <FileText className="mx-auto text-gray-400 mb-4" size={48} />
          <h4 className="text-lg font-medium text-gray-900 mb-2">
            Drop your receipts here
          </h4>
          <p className="text-gray-600 mb-4">
            Or click to browse and select files
          </p>
          
          <label className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer transition-colors">
            <Upload className="mr-2" size={20} />
            Choose Files
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.pdf,.webp,.heic,.heif"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
          
          <p className="text-xs text-gray-500 mt-2">
            Supports: JPG, PNG, PDF, WebP, HEIC, HEIF
          </p>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">
              Selected Files ({selectedFiles.length})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center">
                    <FileText size={16} className="text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900">{file.name}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end mt-4">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Processing...' : `Upload ${selectedFiles.length} File(s)`}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Results */}
      {uploadResults && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Processing Results</h3>
            <button onClick={clearResults} className="text-gray-500 hover:text-gray-700">
              <X size={20} />
            </button>
          </div>
          
          {/* Summary */}
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <p className="text-sm text-blue-700">Total Files</p>
                <p className="text-xl font-bold text-blue-900">{uploadResults.summary?.total_files || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-green-700">Successful</p>
                <p className="text-xl font-bold text-green-900">{uploadResults.summary?.successful || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-red-700">Failed</p>
                <p className="text-xl font-bold text-red-900">{uploadResults.summary?.failed || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-yellow-700">Total Amount</p>
                <p className="text-xl font-bold text-yellow-900">€{uploadResults.summary?.total_amount || 0}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-purple-700">Processing Time</p>
                <p className="text-xl font-bold text-purple-900">{uploadResults.summary?.processing_time || 0}s</p>
              </div>
            </div>
          </div>
          
          {/* Individual Results */}
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {uploadResults.receipts?.map((receipt, index) => (
              <div key={index} className={`border rounded-lg p-4 ${receipt.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{receipt.original_name}</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    receipt.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {receipt.success ? <CheckCircle size={12} className="mr-1" /> : <AlertCircle size={12} className="mr-1" />}
                    {receipt.success ? 'Processed' : 'Failed'}
                  </span>
                </div>
                
                {receipt.success ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Merchant</p>
                      <p className="font-medium">{receipt.merchant || 'Unknown'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Date</p>
                      <p className="font-medium">{receipt.date || 'Unknown'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Amount</p>
                      <p className="font-medium">{receipt.amount ? `€${receipt.amount}` : 'Not detected'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">New Name</p>
                      <p className="font-medium text-xs">{receipt.new_name}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-red-700 text-sm">{receipt.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && uploadResults && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="text-red-500 mr-2" size={20} />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Receipt Organization */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Receipt Organization</h3>
        
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-gray-800 mb-2">📁 Automatic Organization</h4>
          <div className="text-sm text-gray-600 font-mono leading-relaxed">
            receipts/<br />
            ├── 01/ (January)<br />
            ├── 02/ (February)<br />
            ├── ...<br />
            ├── 08/ (August)<br />
            │   ├── 2024-08-15-uber-01.jpg<br />
            │   ├── 2024-08-15-starbucks-01.pdf<br />
            │   └── 2024-08-20-grocery-store-01.png<br />
            └── 12/ (December)
          </div>
        </div>

        {/* Current Receipts */}
        {receiptFolders.length > 0 ? (
          <div>
            <h4 className="font-medium text-gray-800 mb-3">Current Receipts</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {receiptFolders.map((folder, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center">
                    <Folder className="text-purple-600 mr-3" size={24} />
                    <div>
                      <p className="font-medium text-gray-900">{folder.name}</p>
                      <p className="text-sm text-gray-500">{folder.count} receipt(s)</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <Folder className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-500">No receipts uploaded yet</p>
            <p className="text-sm text-gray-400 mt-1">Upload some receipts to see them organized by month</p>
          </div>
        )}
      </div>

      {/* Features Info */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="font-medium text-blue-800 mb-3">🤖 Automatic Processing Features</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
          <div>
            <h5 className="font-medium mb-1">📄 OCR Text Extraction</h5>
            <p>Advanced text recognition from images and PDFs</p>
          </div>
          <div>
            <h5 className="font-medium mb-1">🏪 Merchant Detection</h5>
            <p>Automatically identifies business names</p>
          </div>
          <div>
            <h5 className="font-medium mb-1">📅 Date Recognition</h5>
            <p>Detects transaction dates in multiple formats</p>
          </div>
          <div>
            <h5 className="font-medium mb-1">💰 Amount Extraction</h5>
            <p>Finds total amounts from receipt text</p>
          </div>
          <div>
            <h5 className="font-medium mb-1">📂 Smart Filing</h5>
            <p>Organizes by month with standardized names</p>
          </div>
          <div>
            <h5 className="font-medium mb-1">🔄 Duplicate Prevention</h5>
            <p>Prevents duplicate receipts automatically</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Receipts