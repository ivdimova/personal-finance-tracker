import { createWorker } from 'tesseract.js'

const MAX_OCR_WIDTH = 1500

let worker = null
let currentProgressCallback = null

const getWorker = async () => {
  if (!worker) {
    // Reason: logger must be set at worker creation time in Tesseract.js v5 —
    // passing it to recognize() causes a DataCloneError when postMessage tries to clone the fn.
    // We use a forwarding logger so callers can still pass per-call progress callbacks.
    worker = await createWorker('eng', 1, {
      logger: (m) => {
        if (m.status === 'recognizing text') {
          currentProgressCallback?.(Math.round(m.progress * 100))
        }
      },
    })
  }
  return worker
}

/**
 * Resize image to at most MAX_OCR_WIDTH before OCR.
 * Tesseract doesn't benefit from images wider than ~1500px and runs significantly faster.
 *
 * @param {File|Blob} imageFile
 * @returns {Promise<Blob>}
 */
export const preprocessImage = async (imageFile) => {
  const bitmap = await createImageBitmap(imageFile)

  if (bitmap.width <= MAX_OCR_WIDTH) {
    return imageFile
  }

  const scale = MAX_OCR_WIDTH / bitmap.width
  const w = MAX_OCR_WIDTH
  const h = Math.round(bitmap.height * scale)

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  canvas.getContext('2d').drawImage(bitmap, 0, 0, w, h)

  return new Promise((resolve, reject) =>
    canvas.toBlob(b => b ? resolve(b) : reject(new Error('canvas toBlob failed')), 'image/png')
  )
}

/**
 * Extract text from an image file using Tesseract OCR.
 *
 * @param {File|Blob} imageFile
 * @param {Function} [onProgress] - called with 0-100 progress value
 * @returns {Promise<string>} extracted text
 */
export const extractTextFromImage = async (imageFile, onProgress) => {
  currentProgressCallback = onProgress ?? null
  const processed = await preprocessImage(imageFile)
  const w = await getWorker()
  const { data } = await w.recognize(processed)
  return data.text
}

/**
 * Terminate the Tesseract worker and free memory.
 * Call this when the component using OCR unmounts.
 */
export const terminateOCR = async () => {
  if (worker) {
    await worker.terminate()
    worker = null
  }
}
