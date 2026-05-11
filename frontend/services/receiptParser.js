/**
 * Parse key fields from raw OCR or PDF text without AI.
 * Looks for common date, amount, and merchant patterns.
 *
 * @param {string} text
 * @param {string} fallbackCurrency
 * @returns {{ merchant: string, date: string, amount: string, currency: string }}
 */
export const parseReceiptText = (text, fallbackCurrency = 'EUR') => {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean)

  return {
    merchant: extractMerchant(lines),
    date: extractDate(text),
    amount: extractAmount(text),
    currency: extractCurrency(text) || fallbackCurrency,
  }
}

// --- merchant ---

const SKIP_WORDS = /^(receipt|invoice|tax invoice|vat receipt|till receipt|welcome|thank you|thanks|store|branch|reg no|tel|www|http|email|registered|company|ltd|plc|inc)$/i

const extractMerchant = (lines) => {
  for (const line of lines.slice(0, 8)) {
    if (line.length < 3 || line.length > 60) continue
    if (/^\d/.test(line)) continue
    if (SKIP_WORDS.test(line.replace(/[^a-z ]/gi, '').trim())) continue
    if (/[@#]/.test(line)) continue
    return line
  }
  return ''
}

// --- date ---

const DATE_PATTERNS = [
  { re: /\b(\d{4})-(\d{2})-(\d{2})\b/, fn: (m) => `${m[1]}-${m[2]}-${m[3]}` },
  { re: /\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b/, fn: (m) => `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}` },
  { re: /\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2})\b/, fn: (m) => `20${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}` },
  {
    re: /\b(\d{1,2})\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{4})\b/i,
    fn: (m) => {
      const months = { jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12 }
      const mo = months[m[2].slice(0,3).toLowerCase()]
      return `${m[3]}-${String(mo).padStart(2,'0')}-${m[1].padStart(2,'0')}`
    }
  },
  {
    re: /\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})\b/i,
    fn: (m) => {
      const months = { jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12 }
      const mo = months[m[1].slice(0,3).toLowerCase()]
      return `${m[3]}-${String(mo).padStart(2,'0')}-${m[2].padStart(2,'0')}`
    }
  },
]

const extractDate = (text) => {
  for (const { re, fn } of DATE_PATTERNS) {
    const m = text.match(re)
    if (m) {
      try {
        const date = fn(m)
        if (/^\d{4}-\d{2}-\d{2}$/.test(date) && !isNaN(Date.parse(date))) return date
      } catch { /* skip */ }
    }
  }
  return ''
}

// --- amount ---

const extractAmount = (text) => {
  const totalMatch = text.match(/(?:total|amount|sum|grand total|to pay|balance due)[^\d\n]*[\£\$\€]?\s*(\d+[.,]\d{2})/i)
  if (totalMatch) return totalMatch[1].replace(',', '.')

  const amounts = [...text.matchAll(/[\£\$\€]\s*(\d+[.,]\d{2})\b/g)]
    .map(m => parseFloat(m[1].replace(',', '.')))
    .filter(n => !isNaN(n))
  if (amounts.length > 0) return String(Math.max(...amounts))

  const prices = [...text.matchAll(/\b(\d{1,4}[.,]\d{2})\b/g)]
    .map(m => parseFloat(m[1].replace(',', '.')))
    .filter(n => n > 0 && n < 100000)
  if (prices.length > 0) return String(Math.max(...prices))

  return ''
}

// --- currency ---

const extractCurrency = (text) => {
  if (/[\£]/.test(text)) return 'GBP'
  if (/[\€]/.test(text)) return 'EUR'
  if (/[\$]/.test(text)) return 'USD'
  if (/\bGBP\b/.test(text)) return 'GBP'
  if (/\bEUR\b/.test(text)) return 'EUR'
  if (/\bUSD\b/.test(text)) return 'USD'
  return ''
}
