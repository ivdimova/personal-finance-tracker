import React, { useState } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { transactionsApi } from '../services/api'

const FileUpload = ({ onSuccess, onError }) => {
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)

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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      onError('Please select a CSV file')
      return
    }

    setUploading(true)
    setUploadResult(null)

    try {
      const response = await transactionsApi.upload(file)
      setUploadResult(response.data)
      
      if (onSuccess) {
        setTimeout(() => {
          onSuccess()
        }, 2000) // Show success message for 2 seconds before closing
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message || 'Upload failed'
      onError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  if (uploading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Processing your CSV file...</p>
        <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
      </div>
    )
  }

  if (uploadResult) {
    return (
      <div className="text-center py-8">
        <CheckCircle className="mx-auto text-green-500 mb-4" size={48} />
        <h3 className="text-lg font-semibold text-green-700 mb-2">Upload Successful!</h3>
        <p className="text-gray-600 mb-4">{uploadResult.message}</p>
        
        <div className="bg-green-50 rounded-lg p-4 text-left">
          <h4 className="font-medium text-green-800 mb-2">Summary:</h4>
          <ul className="space-y-1 text-sm text-green-700">
            <li>• Total processed: {uploadResult.total_processed} transactions</li>
            <li>• Successfully saved: {uploadResult.saved_count} transactions</li>
            {uploadResult.refunds_removed > 0 && (
              <li>• Refunds detected and removed: {uploadResult.refunds_removed} pairs</li>
            )}
            <li>• Final count: {uploadResult.final_count} transactions</li>
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
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
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Drop your CSV file here
        </h3>
        <p className="text-gray-600 mb-4">
          Or click to browse and select a file
        </p>
        
        <label className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer transition-colors">
          <Upload className="mr-2" size={20} />
          Choose CSV File
          <input
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
          />
        </label>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h4 className="font-medium text-blue-800 mb-2">Supported Features:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Automatic date format detection</li>
          <li>• Multi-currency support</li>
          <li>• Intelligent expense categorization</li>
          <li>• Refund detection and removal</li>
          <li>• Duplicate transaction prevention</li>
        </ul>
      </div>

      <div className="bg-yellow-50 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="text-yellow-600 mr-2 mt-0.5" size={16} />
          <div>
            <h4 className="font-medium text-yellow-800">Tip:</h4>
            <p className="text-sm text-yellow-700">
              Your CSV file should contain columns for date, description, and amount. 
              The system will automatically detect and adapt to different formats from banks like Revolut, CaixaBank, and others.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FileUpload