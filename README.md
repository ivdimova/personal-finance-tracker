# Personal Finance Tracker

A comprehensive web application for managing personal finances with CSV import, receipt processing with OCR, and expense categorization including communal expenses.

## 🚀 Features

### 📊 **Financial Management**
- **CSV Import**: Support for multiple banking formats (CaixaBank, space-delimited formats)
- **Transaction Categorization**: Automatic categorization with customizable rules
- **Expense Analytics**: Spending trends, category summaries, and financial insights
- **Refund Detection**: Automatic detection and removal of refund transactions

### 🧾 **Receipt Processing**
- **OCR Integration**: Automatic text extraction from receipt images and PDFs
- **Smart Merchant Detection**: Enhanced merchant name recognition with fallback logic
- **Auto-Renaming**: Receipts automatically renamed to `YYYY-MM-DD-merchant-XX` format
- **Multiple Formats**: Support for PNG, JPG, PDF, WebP, HEIC files

### 🏠 **Communal Expenses**
- **Configurable Categories**: Set up communal expense types (utilities, rent, etc.)
- **Keyword Matching**: Automatic categorization based on transaction descriptions
- **Expense Tracking**: Monitor shared expenses with detailed reporting

### 📈 **Analytics & Reporting**
- **Dashboard Overview**: Financial summary with income, expenses, and net amount
- **Category Breakdown**: Visual representation of spending by category
- **Recent Transactions**: Quick view of latest financial activities
- **Spending Trends**: Historical analysis of financial patterns

## 🛠️ Tech Stack

### **Backend**
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Tesseract OCR**: Optical character recognition
- **Pandas**: CSV processing and data manipulation
- **PIL/Pillow**: Image processing

### **Frontend**
- **React**: Modern JavaScript UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication
- **Lucide React**: Beautiful icons
- **Vite**: Fast build tool and dev server

## 📋 Prerequisites

Before running the application locally, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and npm installed
- **Tesseract OCR** installed on your system

### Install Tesseract OCR

#### macOS (using Homebrew):
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## 🚀 Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd personal-finance-tracker
```

### 2. Backend Setup (Flask)

#### Create and Activate Virtual Environment:
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Install Python Dependencies:
```bash
pip install flask flask-cors flask-sqlalchemy pandas pillow pytesseract pypdf2 uuid werkzeug
```

#### Initialize Database:
```bash
# The database will be automatically created when you start the Flask server
python src/main.py
```

### 3. Frontend Setup (React)

#### Install Node.js Dependencies:
```bash
npm install
```

#### Install Required Packages:
```bash
npm install react react-dom react-router-dom axios lucide-react
npm install -D @vitejs/plugin-react vite tailwindcss postcss autoprefixer
```

### 4. Start the Application

#### Terminal 1 - Start Flask Backend:
```bash
source venv/bin/activate
python src/main.py
```
Backend will run on: http://localhost:5555

#### Terminal 2 - Start React Frontend:
```bash
npm run dev
```
Frontend will run on: http://localhost:3000

## 📁 Project Structure

```
personal-finance-tracker/
├── src/                          # Backend (Flask)
│   ├── models/                   # Database models
│   │   ├── user.py
│   │   ├── transaction.py
│   │   └── communal_expense.py
│   ├── routes/                   # API endpoints
│   │   ├── finance.py           # Transaction & CSV import
│   │   ├── receipts.py          # Receipt processing & OCR
│   │   ├── settings.py          # Communal expense settings
│   │   └── user.py              # User management
│   ├── database/                # SQLite database
│   └── main.py                  # Flask application entry point
├── components/                   # Frontend (React)
│   ├── Dashboard.jsx            # Main dashboard
│   ├── Transactions.jsx         # Transaction management
│   ├── Receipts.jsx             # Receipt upload & management
│   ├── Settings.jsx             # Settings configuration
│   ├── Layout.jsx               # App layout wrapper
│   └── FileUpload.jsx           # File upload component
├── services/                     # Frontend services
│   └── api.js                   # API communication
├── receipts/                     # Receipt storage (auto-created)
│   ├── 01/                      # January receipts
│   ├── 02/                      # February receipts
│   └── ...                      # Monthly folders
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Test configuration
├── App.jsx                      # React app root
├── main.jsx                     # React entry point
├── package.json                 # Node.js dependencies
└── vite.config.js              # Vite configuration
```

## 🔧 API Endpoints

### **Finance & Transactions**
- `GET /api/transactions` - List all transactions
- `POST /api/upload` - Upload CSV file for import
- `GET /api/categories` - Get transaction categories
- `GET /api/analytics/spending-trends` - Get spending trends
- `GET /api/analytics/category-summary` - Get category breakdown
- `GET /api/expenses/summary` - Get expense summary
- `DELETE /api/reset/transactions` - Reset all transactions
- `DELETE /api/reset/categories` - Reset all categories
- `DELETE /api/reset/all` - Reset all data

### **Receipts & OCR**
- `POST /api/receipts/upload` - Upload receipt files
- `GET /api/receipts/list` - List organized receipts
- `GET /api/receipts/folder/<month>` - Get receipts for specific month

### **Settings & Communal Expenses**
- `GET /api/settings/communal-expenses/types` - Get communal expense types
- `POST /api/settings/communal-expenses/types` - Create new expense type
- `PUT /api/settings/communal-expenses/types/<id>` - Update expense type
- `DELETE /api/settings/communal-expenses/types/<id>` - Delete expense type
- `GET /api/settings/communal-expenses` - Get communal expenses
- `POST /api/settings/communal-expenses` - Create new communal expense
- `PUT /api/settings/communal-expenses/<id>` - Update communal expense
- `DELETE /api/settings/communal-expenses/<id>` - Delete communal expense

## 📤 Usage Guide

### **1. CSV Import**
1. Navigate to the Dashboard
2. Click "Upload CSV File"
3. Select your banking CSV file
4. The app will automatically detect the format and import transactions
5. Supported formats:
   - CaixaBank format (semicolon-separated)
   - Space-delimited banking files
   - Standard CSV formats

### **2. Receipt Processing**
1. Go to the "Receipts" tab
2. Drag and drop receipt files or click to browse
3. Supported formats: PNG, JPG, PDF, WebP, HEIC, HEIF
4. The app will:
   - Extract text using OCR
   - Detect merchant names
   - Automatically rename files to `YYYY-MM-DD-merchant-XX` format
   - Organize by month in folders

### **3. Communal Expenses Setup**
1. Go to "Settings" tab
2. Create communal expense types (e.g., "Electricity", "Internet")
3. Add keywords for automatic detection
4. The system will automatically categorize transactions matching these keywords

### **4. Analytics**
- **Dashboard**: Overview of income, expenses, and net amount
- **Categories**: Visual breakdown of spending by category
- **Trends**: Historical analysis of spending patterns
- **Recent Activity**: Latest transactions and activities

## 🧪 Testing

The application includes a comprehensive test suite covering:

### **Run Tests**
```bash
# Backend tests
source venv/bin/activate
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/models/ -v        # Model tests
python -m pytest tests/unit/routes/ -v        # API tests
python -m pytest tests/integration/ -v        # Integration tests

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### **Test Coverage**
- **Unit Tests**: Database models, utility functions, individual components
- **Integration Tests**: Complete workflows, API endpoint interactions
- **Model Tests**: 34/34 passing (100%)
- **Overall**: 113+ tests covering core functionality

## 🛡️ Security Features

- **File Upload Validation**: Restricted file types and secure filename handling
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Input Sanitization**: Validation of all user inputs
- **Secure File Storage**: Safe handling of uploaded receipt files

## 🔧 Configuration

### **Environment Variables** (Optional)
Create a `.env` file in the root directory:
```bash
FLASK_DEBUG=True
DATABASE_URL=sqlite:///src/database/app.db
TESSERACT_CMD=/usr/local/bin/tesseract  # Path to tesseract binary
```

### **Customization**
- **Categories**: Add/modify transaction categories in the Settings
- **OCR Languages**: Modify language settings in `src/routes/receipts.py`
- **File Storage**: Adjust receipt storage paths in receipt processing functions
- **Banking Formats**: Extend CSV parsing in `src/routes/finance.py`

## 🚀 Production Deployment

### **Backend (Flask)**
```bash
# Install production WSGI server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5555 src.main:app
```

### **Frontend (React)**
```bash
# Build for production
npm run build

# Serve built files with a web server (nginx, apache, etc.)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest tests/`
5. Commit your changes: `git commit -m "Description"`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### **Common Issues**

#### **Tesseract OCR not found**
```bash
# Error: TesseractNotFoundError
# Solution: Install tesseract and ensure it's in your PATH
which tesseract
```

#### **Database connection errors**
```bash
# Error: Database locked or connection issues
# Solution: Ensure only one Flask instance is running
pkill -f "python src/main.py"
```

#### **Port already in use**
```bash
# Error: Port 5555 or 3000 already in use
# Solution: Kill existing processes or change ports
lsof -ti:5555 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

#### **OCR poor performance**
- Ensure receipt images are clear and well-lit
- Supported formats work best: PNG, JPG with high contrast
- The app includes image preprocessing to improve OCR accuracy

### **Support**
For issues and feature requests, please create an issue in the GitHub repository.

---

**Built with ❤️ using Flask, React, and modern web technologies**