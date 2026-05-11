import * as pdfjsLib from 'pdfjs-dist'

// Reason: pdfjs-dist requires a worker script; point it to the bundled copy
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.mjs',
  import.meta.url
).toString()

const MIN_TEXT_LENGTH = 50

/**
 * Extract text from a PDF file.
 * - Text-based PDFs: text is extracted directly (fast, accurate).
 * - Scanned/image PDFs: first page is rendered to canvas, caller should run OCR on the blob.
 *
 * @param {File} file
 * @returns {Promise<{ text: string, isScanned: boolean, canvas?: HTMLCanvasElement }>}
 */
export const extractFromPDF = async (file) => {
  const arrayBuffer = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise

  let fullText = ''
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    const pageText = content.items.map(item => item.str).join(' ')
    fullText += pageText + '\n'
  }

  if (fullText.trim().length >= MIN_TEXT_LENGTH) {
    return { text: fullText.trim(), isScanned: false }
  }

  // Reason: if very little text was found, the PDF is likely scanned —
  // render first page to a canvas blob for Tesseract OCR
  const page = await pdf.getPage(1)
  // Reason: scale 1.5 gives ~1200px for A4 — enough for OCR, faster than scale 2
  const viewport = page.getViewport({ scale: 1.5 })
  const canvas = document.createElement('canvas')
  canvas.width = viewport.width
  canvas.height = viewport.height
  await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise

  return { text: '', isScanned: true, canvas }
}
