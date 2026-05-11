import React, { useState, useEffect } from 'react'
import { Upload, FileText, Download, AlertCircle, X, CheckCircle, Loader, Sparkles } from 'lucide-react'
import { extractTextFromImage, terminateOCR } from '../services/ocr'
import { extractFromPDF } from '../services/pdf'
import { parseReceiptText } from '../services/receiptParser'
import { receiptsApi } from '../services/api'

const ACCEPTED = '.jpg,.jpeg,.png,.webp,.pdf'
const DEFAULT_CURRENCY = 'EUR'

const slugify = (str) =>
  str.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

const buildFilename = (date, merchant, originalName) => {
  const ext = originalName.includes('.') ? originalName.split('.').pop() : 'jpg'
  const datePart = date || 'unknown-date'
  const merchantPart = merchant ? slugify(merchant) : 'receipt'
  return `${datePart}-${merchantPart}.${ext}`
}

const downloadFile = (file, filename) => {
  const url = URL.createObjectURL(file)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const Receipts = () => {
  // Each entry: { file, status: 'pending'|'processing'|'analyzing'|'done'|'error', form, error }
  const [items, setItems] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [ocrProgress, setOcrProgress] = useState(0)

  useEffect(() => () => { terminateOCR() }, [])

  const updateItem = (idx, patch) =>
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it))

  const processFile = async (file, idx) => {
    updateItem(idx, { status: 'processing' })
    setOcrProgress(0)

    try {
      const isPDF = file.type === 'application/pdf' || file.name.endsWith('.pdf')
      let text

      if (isPDF) {
        const result = await extractFromPDF(file)
        if (result.isScanned) {
          const blob = await new Promise(resolve => result.canvas.toBlob(resolve, 'image/png'))
          text = await extractTextFromImage(blob, setOcrProgress)
        } else {
          setOcrProgress(100)
          text = result.text
        }
      } else {
        text = await extractTextFromImage(file, setOcrProgress)
      }

      const parsed = parseReceiptText(text, DEFAULT_CURRENCY)

      // AI analysis phase
      updateItem(idx, { status: 'analyzing' })
      try {
        const aiResponse = await receiptsApi.parseText(text)
        if (aiResponse.data?.success) {
          const ai = aiResponse.data
          parsed.merchant = ai.merchant || parsed.merchant
          parsed.date = ai.date || parsed.date
          parsed.amount = ai.amount != null ? String(ai.amount) : parsed.amount
          parsed.currency = ai.currency || parsed.currency
        }
      } catch {
        // AI failed silently — regex results are good enough
      }

      updateItem(idx, { status: 'done', form: parsed, error: '' })
    } catch (err) {
      updateItem(idx, { status: 'error', error: err.message ?? 'Processing failed' })
    }
  }

  const addFiles = async (fileList) => {
    const newFiles = Array.from(fileList).filter(f => {
      const isPDF = f.type === 'application/pdf' || f.name.endsWith('.pdf')
      return isPDF || f.type.startsWith('image/')
    })
    if (newFiles.length === 0) return

    const startIdx = items.length
    const newItems = newFiles.map(file => ({
      file,
      status: 'pending',
      form: { merchant: '', date: '', amount: '', currency: DEFAULT_CURRENCY },
      error: '',
    }))

    setItems(prev => [...prev, ...newItems])

    for (let i = 0; i < newFiles.length; i++) {
      await processFile(newFiles[i], startIdx + i)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(e.type === 'dragenter' || e.type === 'dragover')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files)
  }

  const handleDownload = (item) => {
    const filename = buildFilename(item.form.date, item.form.merchant, item.file.name)
    downloadFile(item.file, filename)
  }

  const handleDownloadAll = () => {
    items.filter(it => it.status === 'done').forEach(handleDownload)
  }

  const removeItem = (idx) => setItems(prev => prev.filter((_, i) => i !== idx))

  const isProcessing = items.some(it => ['pending', 'processing', 'analyzing'].includes(it.status))
  const doneCount = items.filter(it => it.status === 'done').length

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Receipt Upload</h2>
        <p className="text-gray-600">
          OCR extracts text from your receipt — review the fields and download with a clean filename.
        </p>
      </div>

      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragActive ? 'border-purple-400 bg-purple-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <FileText className="mx-auto text-gray-400 mb-3" size={36} />
        <p className="text-gray-500 text-sm mb-3">JPG, PNG, WebP, or PDF — multiple files supported</p>
        <label className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer">
          <Upload className="mr-2" size={18} />
          Choose Files
          <input
            type="file"
            accept={ACCEPTED}
            multiple
            onChange={e => addFiles(e.target.files)}
            className="hidden"
          />
        </label>
      </div>

      {/* File list */}
      {items.length > 0 && (
        <div className="space-y-3">
          {items.map((item, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow p-4 space-y-3">
              {/* Header row */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  {item.status === 'processing' && (
                    <Loader size={16} className="text-purple-500 animate-spin shrink-0" />
                  )}
                  {item.status === 'analyzing' && (
                    <Sparkles size={16} className="text-indigo-500 animate-pulse shrink-0" />
                  )}
                  {item.status === 'done' && (
                    <CheckCircle size={16} className="text-green-500 shrink-0" />
                  )}
                  {item.status === 'error' && (
                    <AlertCircle size={16} className="text-red-500 shrink-0" />
                  )}
                  {item.status === 'pending' && (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 shrink-0" />
                  )}
                  <span className="text-sm text-gray-600 truncate">{item.file.name}</span>
                </div>
                <button onClick={() => removeItem(idx)} className="text-gray-400 hover:text-gray-600 shrink-0">
                  <X size={16} />
                </button>
              </div>

              {/* Progress bar while OCR is running */}
              {item.status === 'processing' && (
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-purple-600 h-1.5 rounded-full transition-all"
                    style={{ width: `${ocrProgress}%` }}
                  />
                </div>
              )}
              {item.status === 'analyzing' && (
                <p className="text-xs text-indigo-500 flex items-center gap-1">
                  <Sparkles size={12} /> AI analyzing...
                </p>
              )}

              {/* Error */}
              {item.error && (
                <p className="text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle size={12} /> {item.error}
                </p>
              )}

              {/* Editable fields + download */}
              {item.status === 'done' && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Merchant', key: 'merchant', type: 'text' },
                      { label: 'Date', key: 'date', type: 'date' },
                      { label: 'Amount', key: 'amount', type: 'number' },
                      { label: 'Currency', key: 'currency', type: 'text' },
                    ].map(({ label, key, type }) => (
                      <div key={key}>
                        <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                        <input
                          type={type}
                          value={item.form[key]}
                          onChange={e => updateItem(idx, { form: { ...item.form, [key]: e.target.value } })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md
                                     focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono text-gray-500 truncate">
                      {buildFilename(item.form.date, item.form.merchant, item.file.name)}
                    </span>
                    <button
                      onClick={() => handleDownload(item)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 shrink-0"
                    >
                      <Download size={14} /> Download
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}

          {/* Download all */}
          {doneCount > 1 && !isProcessing && (
            <button
              onClick={handleDownloadAll}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Download size={18} />
              Download all {doneCount} files
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default Receipts
