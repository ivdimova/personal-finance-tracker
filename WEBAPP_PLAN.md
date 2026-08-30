# Personal Finance Tracker — Browser-Only Web App Plan

## Goal

Rewrite the app as a fully client-side React application:
- All financial data stored in browser IndexedDB (never leaves the device)
- OCR runs in-browser via Tesseract.js (WASM)
- AI is optional — user brings their own API key and endpoint
- No backend server — deployable as a static site (Vercel / Netlify / GitHub Pages)

---

## Tech Stack

| Concern | Library | Notes |
|---|---|---|
| Framework | React 18 + Vite | Same as current |
| Styling | Tailwind CSS | Same as current |
| Database | Dexie.js v4 | IndexedDB wrapper |
| OCR | tesseract.js v5 | WASM, runs in browser |
| CSV parsing | PapaParse | Lightweight, well maintained |
| AI client | Custom fetch wrapper | OpenAI-compatible API format |
| Charts | Recharts | Same as current (if used) |
| Hosting | Vercel or Netlify | Free tier, static deploy |

---

## Project Structure

```
src/
  main.jsx
  App.jsx

  db/
    index.js              # Dexie instance + schema
    transactions.js       # CRUD helpers for transactions
    categories.js         # CRUD helpers for categories
    settings.js           # Read/write user settings
    overrides.js          # Category override helpers

  services/
    ai.js                 # AI client (OpenAI-compatible fetch wrapper)
    ocr.js                # Tesseract.js wrapper
    csv.js                # CSV parsing (PapaParse, Revolut format)
    categorizer.js        # Rule-based categorization (keyword matching)

  components/
    (keep existing components, update data calls)

  pages/
    (keep existing pages, update data calls)

  hooks/
    useTransactions.js    # React hook over db/transactions.js
    useCategories.js      # React hook over db/categories.js
    useSettings.js        # React hook over db/settings.js
    useAI.js              # React hook for AI availability + calls
```

---

## Phase 1: Project Setup

1. Create new Vite + React project: `npm create vite@latest finance-tracker -- --template react`
2. Install dependencies:
   ```bash
   npm install dexie dexie-react-hooks tesseract.js papaparse recharts
   npm install -D tailwindcss postcss autoprefixer
   ```
3. Set up Tailwind CSS (`tailwind.config.js`, `postcss.config.js`)
4. Copy over existing React components and pages from `frontend/` as a starting point
5. Remove all `fetch('/api/...')` calls — these will be replaced with Dexie calls

---

## Phase 2: Database Layer (Dexie.js)

### Schema — `src/db/index.js`

```js
import Dexie from 'dexie'

export const db = new Dexie('PersonalFinanceTracker')

db.version(1).stores({
  transactions: '++id, date, description, amount, category, account, createdAt',
  categories:   '++id, &name',
  overrides:    '++id, &description',   // maps description → category
  settings:     '&key',                 // key-value store
})
```

### CRUD helpers

**`src/db/transactions.js`**
```js
import { db } from './index'

export const getTransactions = (filters = {}) => {
  let query = db.transactions.orderBy('date').reverse()
  if (filters.category) query = query.filter(t => t.category === filters.category)
  if (filters.search)   query = query.filter(t =>
    t.description.toLowerCase().includes(filters.search.toLowerCase())
  )
  return query.toArray()
}

export const addTransactions = (transactions) => db.transactions.bulkAdd(transactions)
export const updateTransaction = (id, changes) => db.transactions.update(id, changes)
export const deleteTransaction = (id) => db.transactions.delete(id)
export const clearTransactions = () => db.transactions.clear()
```

**`src/db/categories.js`**
```js
import { db } from './index'

export const getCategories = () => db.categories.toArray()
export const addCategory = (cat) => db.categories.add(cat)
export const updateCategory = (id, changes) => db.categories.update(id, changes)
export const seedDefaultCategories = async () => {
  const count = await db.categories.count()
  if (count > 0) return
  await db.categories.bulkAdd(DEFAULT_CATEGORIES)
}
```

Default categories to seed (match current app):
- Groceries & Supermarkets
- Eating Out
- Transport
- Entertainment
- Health
- Shopping
- Bills & Utilities
- Travel
- Income
- Other

**`src/db/settings.js`**
```js
import { db } from './index'

export const getSetting = (key) =>
  db.settings.get(key).then(row => row?.value ?? null)

export const setSetting = (key, value) =>
  db.settings.put({ key, value })
```

Settings keys used in the app:
- `userName`
- `aiApiKey`
- `aiBaseUrl`
- `aiModel`
- `aiEnabled`
- `defaultCurrency`

**`src/db/overrides.js`**
```js
import { db } from './index'

export const getOverride = (description) =>
  db.overrides.get({ description })

export const setOverride = (description, category) =>
  db.overrides.put({ description, category })

export const getAllOverrides = () => db.overrides.toArray()
```

---

## Phase 3: Services

### 3a. CSV Parser — `src/services/csv.js`

Handle Revolut CSV format (same logic as current `finance.py`):

```js
import Papa from 'papaparse'

export const parseRevolutCSV = (file) => new Promise((resolve, reject) => {
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: ({ data, errors }) => {
      if (errors.length) return reject(errors)
      const transactions = data.map(row => ({
        date: row['Started Date']?.split(' ')[0] ?? row['Completed Date']?.split(' ')[0],
        description: row['Description'],
        amount: parseFloat(row['Amount']),
        currency: row['Currency'],
        account: 'Revolut',
        category: null,
        createdAt: new Date().toISOString(),
      })).filter(t => t.date && t.description && !isNaN(t.amount))
      resolve(transactions)
    },
    error: reject,
  })
})
```

### 3b. Rule-Based Categorizer — `src/services/categorizer.js`

Move keyword matching from the backend to the frontend:

```js
const KEYWORD_RULES = [
  { category: 'Groceries & Supermarkets', keywords: ['tesco', 'lidl', 'aldi', 'sainsbury', 'waitrose', 'asda', 'morrisons'] },
  { category: 'Eating Out',   keywords: ['mcdonalds', 'starbucks', 'deliveroo', 'uber eats', 'just eat', 'pizza'] },
  { category: 'Transport',    keywords: ['uber', 'bolt', 'tfl', 'trainline', 'national rail', 'bus'] },
  { category: 'Entertainment',keywords: ['netflix', 'spotify', 'cinema', 'steam', 'playstation'] },
  { category: 'Health',       keywords: ['pharmacy', 'boots', 'gym', 'dentist', 'doctor'] },
  { category: 'Bills & Utilities', keywords: ['electricity', 'gas', 'water', 'internet', 'vodafone', 'ee ', 'o2'] },
  { category: 'Travel',       keywords: ['airbnb', 'booking.com', 'ryanair', 'easyjet', 'hotel'] },
  // extend as needed
]

export const categorizeByRules = (description) => {
  const lower = description.toLowerCase()
  for (const rule of KEYWORD_RULES) {
    if (rule.keywords.some(kw => lower.includes(kw))) return rule.category
  }
  return 'Other'
}
```

### 3c. OCR Service — `src/services/ocr.js`

```js
import { createWorker } from 'tesseract.js'

let worker = null

const getWorker = async () => {
  if (!worker) {
    worker = await createWorker('eng')
  }
  return worker
}

export const extractTextFromImage = async (imageFile, onProgress) => {
  const w = await getWorker()
  const { data } = await w.recognize(imageFile, {}, {
    logger: onProgress ? (m) => {
      if (m.status === 'recognizing text') onProgress(Math.round(m.progress * 100))
    } : undefined
  })
  return data.text
}

// Call this on app unmount or when done
export const terminateOCR = async () => {
  if (worker) {
    await worker.terminate()
    worker = null
  }
}
```

Note: Tesseract.js downloads the language model (~10MB) on first use and caches it in the browser.

### 3d. AI Service — `src/services/ai.js`

Supports any OpenAI-compatible API (OpenAI, Groq, Ollama, LM Studio, etc.):

```js
export const callAI = async ({ apiKey, baseUrl, model, systemPrompt, userPrompt }) => {
  const url = `${baseUrl.replace(/\/$/, '')}/chat/completions`

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user',   content: userPrompt },
      ],
      temperature: 0.1,
      response_format: { type: 'json_object' },
    }),
  })

  if (!res.ok) throw new Error(`AI API error: ${res.status} ${await res.text()}`)

  const data = await res.json()
  return JSON.parse(data.choices[0].message.content)
}

export const testConnection = async ({ apiKey, baseUrl, model }) => {
  try {
    await callAI({
      apiKey, baseUrl, model,
      systemPrompt: 'You are a test assistant. Reply with {"ok": true}.',
      userPrompt: 'ping',
    })
    return { success: true }
  } catch (e) {
    return { success: false, error: e.message }
  }
}
```

**AI prompts** (move to `src/services/prompts.js`):

```js
export const CATEGORIZE_PROMPT = (categories) =>
  `You are a personal finance assistant. Categorize the transaction descriptions into one of these categories: ${categories.join(', ')}.
   Return JSON: {"results": [{"description": "...", "category": "..."}]}`

export const PARSE_RECEIPT_PROMPT = `You are a receipt parser. Extract the merchant name, date, total amount and currency from the receipt text.
  Return JSON: {"merchant": "...", "date": "YYYY-MM-DD", "amount": 0.00, "currency": "EUR", "confidence": 0.0}`
```

---

## Phase 4: React Hooks

These hooks sit between components and the db layer, so components never import Dexie directly.

**`src/hooks/useTransactions.js`**
```js
import { useLiveQuery } from 'dexie-react-hooks'
import { db } from '../db'
import { addTransactions, updateTransaction, deleteTransaction } from '../db/transactions'

export const useTransactions = (filters) => {
  const transactions = useLiveQuery(() => {
    let q = db.transactions.orderBy('date').reverse()
    if (filters?.search) q = q.filter(t =>
      t.description.toLowerCase().includes(filters.search.toLowerCase())
    )
    if (filters?.category) q = q.filter(t => t.category === filters.category)
    return q.toArray()
  }, [filters?.search, filters?.category])

  return { transactions, addTransactions, updateTransaction, deleteTransaction }
}
```

**`src/hooks/useSettings.js`**
```js
import { useLiveQuery } from 'dexie-react-hooks'
import { db } from '../db'
import { setSetting } from '../db/settings'

export const useSettings = () => {
  const settings = useLiveQuery(() =>
    db.settings.toArray().then(rows =>
      Object.fromEntries(rows.map(r => [r.key, r.value]))
    )
  )
  return { settings: settings ?? {}, setSetting }
}
```

**`src/hooks/useAI.js`**
```js
import { useSettings } from './useSettings'
import { callAI, testConnection } from '../services/ai'
import { CATEGORIZE_PROMPT, PARSE_RECEIPT_PROMPT } from '../services/prompts'

export const useAI = () => {
  const { settings } = useSettings()
  const { aiApiKey, aiBaseUrl, aiModel, aiEnabled } = settings

  const isConfigured = aiEnabled && aiApiKey && aiBaseUrl && aiModel

  const categorize = (descriptions, categories) => {
    if (!isConfigured) return null
    return callAI({
      apiKey: aiApiKey,
      baseUrl: aiBaseUrl,
      model: aiModel,
      systemPrompt: CATEGORIZE_PROMPT(categories),
      userPrompt: JSON.stringify(descriptions),
    })
  }

  const parseReceipt = (ocrText) => {
    if (!isConfigured) return null
    return callAI({
      apiKey: aiApiKey,
      baseUrl: aiBaseUrl,
      model: aiModel,
      systemPrompt: PARSE_RECEIPT_PROMPT,
      userPrompt: ocrText,
    })
  }

  return { isConfigured, categorize, parseReceipt, testConnection: () =>
    testConnection({ apiKey: aiApiKey, baseUrl: aiBaseUrl, model: aiModel })
  }
}
```

---

## Phase 5: Settings Page

The settings page needs a new **AI Configuration** section:

```
AI Configuration
────────────────
[ ] Enable AI features

API Base URL   [https://api.openai.com/v1        ]
API Key        [sk-...                    👁 show]
Model          [gpt-4o-mini                      ]

Suggested providers:
  • OpenAI   → https://api.openai.com/v1
  • Groq     → https://api.groq.com/openai/v1
  • Ollama   → http://localhost:11434/v1   (fully local, fully private)
  • LM Studio→ http://localhost:1234/v1   (fully local, fully private)

[ Test Connection ]  → shows ✓ Connected or ✗ error message
```

All values saved to IndexedDB via `setSetting`. API key never leaves the browser.

---

## Phase 6: CSV Import Flow (updated)

```
User selects CSV
  → PapaParse parses rows
  → For each transaction:
      1. Check overrides table for exact description match → use that category
      2. If no override → run rule-based categorizer
      3. If AI enabled → batch remaining "Other" descriptions to AI
  → bulkAdd to IndexedDB
  → Show summary (total, categories breakdown)
```

---

## Phase 7: Receipt Upload Flow (updated)

```
User selects image
  → Show progress bar
  → Tesseract.js extracts text (runs in browser)
  → If AI enabled:
      → Send OCR text to user's AI endpoint
      → Parse merchant / date / amount from response
  → If AI not enabled:
      → Show raw OCR text, user fills in fields manually
  → Save as transaction in IndexedDB
```

---

## Phase 8: Data Export / Import

Since data is browser-only, export/import is critical for backup and device migration.

**Export:** Download all transactions as CSV (existing feature, keep it)

**Import backup:** Accept a JSON export of the full IndexedDB state
```js
export const exportAll = async () => {
  const [transactions, categories, overrides] = await Promise.all([
    db.transactions.toArray(),
    db.categories.toArray(),
    db.overrides.toArray(),
  ])
  const blob = new Blob([JSON.stringify({ transactions, categories, overrides })],
    { type: 'application/json' })
  // trigger download
}

export const importAll = async (jsonFile) => {
  const { transactions, categories, overrides } = JSON.parse(await jsonFile.text())
  await db.transaction('rw', db.transactions, db.categories, db.overrides, async () => {
    await db.transactions.bulkPut(transactions)
    await db.categories.bulkPut(categories)
    await db.overrides.bulkPut(overrides)
  })
}
```

Add **Export data** and **Import backup** buttons to Settings.

---

## Phase 9: Hosting

Since the app is fully static:

**Vercel (recommended):**
1. Push to GitHub
2. Connect repo to Vercel
3. Build command: `npm run build`
4. Output dir: `dist`
5. Done — auto-deploys on every push

**Netlify:**
- Same process, same settings

**GitHub Pages:**
- Add `"homepage": "https://username.github.io/repo"` to `package.json`
- Use `vite-plugin-gh-pages` or GitHub Actions

No environment variables needed — no server, no secrets.

---

## What to Keep from the Current App

Copy these directly into the new project and update imports:

| Current file | Action |
|---|---|
| `frontend/src/components/*` | Copy, replace `fetch('/api/...')` with hook calls |
| `frontend/src/pages/*` | Copy, same as above |
| `tailwind.config.js` | Copy as-is |
| `vite.config.js` | Copy, remove proxy config (no backend) |
| `jest.config.js` | Copy as-is |
| Keyword rules in categorizer | Extract and put in `src/services/categorizer.js` |

**Do not copy:**
- `src/` (Flask backend — entire directory)
- `requirements.txt`
- `pytest.ini`
- `src-tauri/` (if it exists)

---

## Limitations to Communicate to Users

- Data is stored in this browser only — clearing browser data deletes everything
- Use **Export data** regularly as a backup
- To move to another device, use **Export → Import**
- AI features are optional and require your own API key
- Receipt OCR works best on clear, well-lit photos
- Ollama / LM Studio users get fully local AI with no data leaving their machine

---

## Out of Scope (potential future additions)

- End-to-end encrypted sync (e.g. via a user-provided S3 bucket or WebDAV)
- PWA / offline support (straightforward to add with Vite PWA plugin)
- Mobile app via Capacitor (wraps the same React app)
- Anthropic Claude support (different API format — would need a separate adapter)
