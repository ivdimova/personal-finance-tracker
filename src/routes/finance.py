from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
import os
import csv
import pandas as pd
from datetime import datetime
import json
import re
from src.models.transaction import Transaction, Category
from src.models.communal_expense import CommunalExpenseType
from src.models.user import db

finance_bp = Blueprint('finance', __name__)

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

# Default categories with keywords for auto-categorization
DEFAULT_CATEGORIES = [
    {
        'name': 'Food & Dining',
        'keywords': ['restaurant', 'cafe', 'food', 'grocery', 'supermarket', 'mcdonalds', 'starbucks', 'pizza', 'delivery', 
                    'glovo', 'deli', 'aroma', 'newcoffee', 'traveller caf', 'ssp hellas', 'mega place', 'publix', 
                    'farmacia saude', 'matteo biancardi', 'krhtikos', 'wine bar', 'lounge', 'bistro', 'bakery', 
                    'bakey', 'gelato', 'so fresh', 'solea', 'bar', 'celeiro', 'belmiro'],
        'color': '#FF6B6B'
    },
    {
        'name': 'Transportation',
        'keywords': ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'bus', 'train', 'parking', 'metro', 'transit', 
                    'bolt', 'ktel', 'pending.uber', 'ubr', 'verify ri', 'transportes intermodais', 'transport',
                    'metro do porto', 'rede expressos', 'cp - comboios', 'taxime', 'sky express', 'ryanair',
                    'british airways', 'stansted express', 'transport for london'],
        'color': '#4ECDC4'
    },
    {
        'name': 'Bills & Utilities',
        'keywords': ['electric', 'water', 'gas', 'internet', 'phone', 'utility', 'bill', 'insurance',
                    'telefonica', 'iberdrola', 'prosegur', 'proseguir', 'alarmas', 'asisa', 'cotizacion', 'tgss',
                    'netflix', 'spotify', 'disney plus', 'apple.com/bill', 'subscription', 'monthly', 'prime',
                    'glovo prime', 'onebill mybox', 'television', 'tv', 'lexdixit', 'edp', 'enel', 'iberdrola',
                    'vodafone', 'meo', 'nos', 'sapo', 'multibanco', 'mbnet', 'paypal'],
        'color': '#FFEAA7'
    },
    {
        'name': 'Travel & Hotels',
        'keywords': ['booking', 'hotel', 'bkg', 'art plaza hotel', 'airport', 'venetis airport', 'ssp airport',
                    'fairfield', 'getyourguide', 'duty free', 'hmshost', 'gail', 'go to gate'],
        'color': '#E74C3C'
    },
    {
        'name': 'Shopping & Retail',
        'keywords': ['amazon', 'store', 'mall', 'shop', 'retail', 'clothing', 'electronics', 'purchase',
                    'card purchase', 'ellestia mall', 'television por', 'arbitrade', 'cursor', 'zara',
                    'h&m', 'mango', 'fnac', 'continente', 'pingo doce', 'auchan', 'lidl', 'carrefour',
                    'el corte ingles', 'worten', 'media markt', 'primark', 'bershka', 'pull&bear',
                    'stradivarius', 'massimo dutti', 'decathlon', 'ikea', 'leroy merlin', 'jumbo'],
        'color': '#96CEB4'
    },
    {
        'name': 'Health & Wellness',
        'keywords': ['doctor', 'hospital', 'pharmacy', 'medical', 'health', 'clinic', 'massage', 'thai massage',
                    'sopharmacy', 'farmacia'],
        'color': '#DDA0DD'
    },
    {
        'name': 'Income',
        'keywords': ['salary', 'payroll', 'deposit', 'income', 'payment', 'salary deposit', 'blueline growth',
                    'wage', 'bonus', 'commission', 'dividend', 'interest', 'refund', 'return'],
        'color': '#98D8C8'
    },
    {
        'name': 'Transfers',
        'keywords': ['immediate', 'tfr', 'transfer', 'immediate tfr', 'immediate transfer', 'top-up', 
                    'revolut bank', 'to ivelina', 'to shady', 'send money', 'receive money', 'p2p'],
        'color': '#A8E6CF'
    },
    {
        'name': 'Entertainment',
        'keywords': ['cinema', 'movie', 'theatre', 'concert', 'entertainment', 'game', 'sport', 'streaming',
                    'music', 'podcast', 'youtube premium', 'gaming', 'steam', 'playstation', 'xbox', 'nintendo',
                    'cinemax', 'nos cinemas', 'uci cinemas', 'eventbrite', 'ticketmaster', 'stubhub',
                    'casino', 'lottery', 'bet', 'show', 'festival'],
        'color': '#FFB74D'
    },
    {
        'name': 'ATM & Banking',
        'keywords': ['atm', 'withdrawal', 'cash', 'bank fee', 'foreign exchange', 'fx', 'exchange fee',
                    'caixa automatico', 'levantamento', 'multibanco fee', 'card fee', 'maintenance fee'],
        'color': '#85C1E9'
    },
    {
        'name': 'Other',
        'keywords': [],
        'color': '#F7DC6F'
    }
]

def initialize_categories():
    """Initialize default categories if they don't exist"""
    for cat_data in DEFAULT_CATEGORIES:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(
                name=cat_data['name'],
                keywords=json.dumps(cat_data['keywords']),
                color=cat_data['color']
            )
            db.session.add(category)
    db.session.commit()

def categorize_transaction(description, amount=0.0):
    """Auto-categorize transaction based on description and amount"""
    description_lower = description.lower()
    
    # Check if it's a transfer first, then decide based on amount
    transfer_keywords = ['immediate', 'tfr', 'transfer', 'immediate tfr', 'immediate transfer', 'top-up', 
                        'revolut bank', 'to ivelina', 'to shady', 'send money', 'receive money', 'p2p']
    
    is_transfer = any(keyword.lower() in description_lower for keyword in transfer_keywords)
    
    if is_transfer:
        # Positive transfers are income, negative transfers stay as transfers
        if amount > 0:
            return 'Income'
        else:
            return 'Transfers'
    
    # Check user-defined communal expenses first (higher priority)
    communal_expense_types = CommunalExpenseType.query.filter_by(is_active=True).all()
    for expense_type in communal_expense_types:
        if expense_type.keywords:
            keywords = json.loads(expense_type.keywords)
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return f'Communal - {expense_type.name}'
    
    # Regular categorization for non-transfers and non-communal expenses
    categories = Category.query.all()
    for category in categories:
        if category.keywords and category.name not in ['Income', 'Transfers']:
            keywords = json.loads(category.keywords)
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category.name
    
    return 'Other'

def detect_and_remove_refunds():
    """Detect and remove refund pairs from transactions"""
    current_app.logger.info("Starting refund detection and removal process")
    
    # Get all transactions ordered by date
    transactions = Transaction.query.order_by(Transaction.date.asc()).all()
    
    refunds_removed = 0
    transactions_to_delete = []
    
    # Group transactions by description similarity for faster matching
    description_groups = {}
    for transaction in transactions:
        # Normalize description for matching
        normalized_desc = normalize_description_for_refunds(transaction.description.lower())
        if normalized_desc not in description_groups:
            description_groups[normalized_desc] = []
        description_groups[normalized_desc].append(transaction)
    
    # Look for refund pairs within each description group
    for description, group_transactions in description_groups.items():
        if len(group_transactions) < 2:
            continue
            
        # Sort by date to check chronologically
        group_transactions.sort(key=lambda x: x.date)
        
        i = 0
        while i < len(group_transactions):
            charge_transaction = group_transactions[i]
            
            # Skip if already marked for deletion
            if charge_transaction.id in [t.id for t in transactions_to_delete]:
                i += 1
                continue
                
            # Look for a refund (opposite sign) after this transaction
            if charge_transaction.amount < 0:  # This is a charge (negative)
                refund_amount_target = abs(charge_transaction.amount)
                
                # Look for positive amount (refund) in the next few transactions
                for j in range(i + 1, min(i + 10, len(group_transactions))):  # Check next 10 transactions max
                    potential_refund = group_transactions[j]
                    
                    # Skip if already marked for deletion
                    if potential_refund.id in [t.id for t in transactions_to_delete]:
                        continue
                    
                    # Check if this could be a refund
                    if (potential_refund.amount > 0 and 
                        potential_refund.amount <= refund_amount_target and
                        potential_refund.amount >= refund_amount_target * 0.5):  # Allow partial refunds (50%+)
                        
                        # Check date proximity (within 30 days)
                        date_diff = (potential_refund.date - charge_transaction.date).days
                        if 0 <= date_diff <= 30:
                            current_app.logger.info(f"Found refund pair: {charge_transaction.description} "
                                                  f"({charge_transaction.amount}) -> ({potential_refund.amount})")
                            
                            # Mark both transactions for deletion
                            transactions_to_delete.append(charge_transaction)
                            transactions_to_delete.append(potential_refund)
                            refunds_removed += 1
                            break
            i += 1
    
    # Delete the identified refund pairs
    for transaction in transactions_to_delete:
        db.session.delete(transaction)
    
    if transactions_to_delete:
        db.session.commit()
        current_app.logger.info(f"Removed {refunds_removed} refund pairs ({len(transactions_to_delete)} total transactions)")
    else:
        current_app.logger.info("No refunds detected")
    
    return refunds_removed, len(transactions_to_delete)

def normalize_description_for_refunds(description):
    """Normalize transaction description for refund matching"""
    import re
    
    # Convert to lowercase
    desc = description.lower()
    
    # Remove common refund indicators
    refund_words = ['refund', 'return', 'reversal', 'correction', 'adjustment']
    for word in refund_words:
        desc = desc.replace(word, '')
    
    # Remove extra whitespace and special characters for better matching
    desc = re.sub(r'[^\w\s]', ' ', desc)
    desc = ' '.join(desc.split())  # Normalize whitespace
    
    # Take first few significant words for grouping
    words = desc.split()[:3]  # First 3 words usually capture the merchant
    return ' '.join(words)

def clean_amount_string(amount_str):
    """Clean amount string by removing currency symbols and formatting"""
    if pd.isna(amount_str) or amount_str == '':
        return 0.0
    
    # Convert to string and strip whitespace
    amount_str = str(amount_str).strip()
    
    # Common currency symbols and words to remove
    currency_patterns = [
        r'EUR\s*',  # EUR with optional space
        r'€\s*',    # Euro symbol
        r'\$\s*',   # Dollar sign
        r'USD\s*',  # USD
        r'GBP\s*',  # British Pound
        r'£\s*',    # Pound symbol
        r'CHF\s*',  # Swiss Franc
        r'¥\s*',    # Yen symbol
        r'₹\s*',    # Rupee symbol
        r'kr\s*',   # Krona/Krone
        r'SEK\s*',  # Swedish Krona
        r'NOK\s*',  # Norwegian Krone
        r'DKK\s*',  # Danish Krone
    ]
    
    # Remove currency symbols (at beginning or end)
    for pattern in currency_patterns:
        amount_str = re.sub(f'^{pattern}|{pattern}$', '', amount_str, flags=re.IGNORECASE)
    
    # Replace comma as thousand separator with nothing, but keep comma as decimal separator
    # Handle European format (123.456,78) vs US format (123,456.78)
    if ',' in amount_str and '.' in amount_str:
        # Both comma and dot present - determine which is decimal separator
        last_comma = amount_str.rfind(',')
        last_dot = amount_str.rfind('.')
        
        if last_comma > last_dot:
            # Comma is decimal separator (European format: 1.234,56)
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal separator (US format: 1,234.56)
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str and amount_str.count(',') == 1:
        # Only comma present - check if it's decimal separator
        comma_pos = amount_str.find(',')
        digits_after_comma = len(amount_str) - comma_pos - 1
        if digits_after_comma <= 2:  # Likely decimal separator (e.g., "-11,49")
            amount_str = amount_str.replace(',', '.')
        else:  # Likely thousand separator
            amount_str = amount_str.replace(',', '')
    
    # Remove any remaining non-numeric characters except dots and hyphens
    clean_str = re.sub(r'[^\d.-]', '', amount_str)
    
    # Handle multiple dots (keep only the last one as decimal)
    if clean_str.count('.') > 1:
        parts = clean_str.split('.')
        clean_str = ''.join(parts[:-1]) + '.' + parts[-1]
    
    # Handle empty string or just symbols
    if not clean_str or clean_str in ['-', '.', '-.']:
        return 0.0
    
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_space_delimited_banking_file(file_path, sample_lines):
    """Parse space-delimited banking format files like Portuguese banks"""
    transactions = []
    current_app.logger.info("DEBUG: Parsing space-delimited banking format")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        for line_num, line in enumerate(lines, 1):
            try:
                current_app.logger.info(f"DEBUG: Processing line {line_num}: {line}")
                
                # Split by multiple spaces to separate columns
                # Format: DESCRIPTION    DATE    AMOUNT    BALANCE
                parts = re.split(r'\s{2,}', line.strip())  # Split on 2+ consecutive spaces
                
                if len(parts) < 3:
                    current_app.logger.warning(f"DEBUG: Skipping line {line_num} - insufficient columns: {parts}")
                    continue
                
                description = parts[0].strip()
                date_str = parts[1].strip()
                amount_str = parts[2].strip()
                # parts[3] would be balance if present
                
                current_app.logger.info(f"DEBUG: Parsed - desc: '{description}', date: '{date_str}', amount: '{amount_str}'")
                
                # Parse date (DD/MM/YYYY format)
                try:
                    if '/' in date_str:
                        date_parts = date_str.split('/')
                        if len(date_parts) == 3:
                            day, month, year = date_parts
                            # Handle 2-digit year
                            if len(year) == 2:
                                year = '20' + year if int(year) < 50 else '19' + year
                            date_obj = datetime(int(year), int(month), int(day)).date()
                            current_app.logger.info(f"DEBUG: Parsed date: {date_obj}")
                        else:
                            current_app.logger.error(f"DEBUG: Invalid date format: {date_str}")
                            continue
                    else:
                        current_app.logger.error(f"DEBUG: Date format not recognized: {date_str}")
                        continue
                except (ValueError, IndexError) as e:
                    current_app.logger.error(f"DEBUG: Date parsing error for '{date_str}': {e}")
                    continue
                
                # Parse amount (handle EUR suffix and comma decimal)
                amount = clean_amount_string(amount_str)
                current_app.logger.info(f"DEBUG: Parsed amount: {amount}")
                
                if amount == 0.0:
                    current_app.logger.warning(f"DEBUG: Skipping line {line_num} - zero amount")
                    continue
                
                # Auto-categorize
                category = categorize_transaction(description, amount)
                current_app.logger.info(f"DEBUG: Assigned category: {category}")
                
                transactions.append({
                    'date': date_obj,
                    'description': description,
                    'amount': amount,
                    'category': category
                })
                
                current_app.logger.info(f"DEBUG: Successfully processed transaction {len(transactions)}")
                
            except Exception as e:
                current_app.logger.error(f"DEBUG: Error processing line {line_num}: {e}")
                continue
        
        current_app.logger.info(f"DEBUG: Space-delimited parsing completed - {len(transactions)} transactions")
        return transactions
        
    except Exception as e:
        current_app.logger.error(f"DEBUG: Error in space-delimited parsing: {e}")
        raise ValueError(f"Error parsing space-delimited banking file: {str(e)}")

def parse_csv_file(file_path):
    """Parse CSV file and extract transactions"""
    transactions = []
    
    try:
        # First check if this is a space-delimited format (like Portuguese banking)
        with open(file_path, 'r', encoding='utf-8') as f:
            sample_lines = [line.strip() for line in f.readlines()[:3] if line.strip()]
        
        # Check for space-delimited format with EUR currency (only if no tabs or commas)
        if (sample_lines and 
            all('EUR' in line and len(line.split()) >= 4 for line in sample_lines) and
            not any('\t' in line or ',' in line for line in sample_lines)):
            current_app.logger.info("DEBUG: Detected space-delimited banking format")
            return parse_space_delimited_banking_file(file_path, sample_lines)
        
        # Try different encodings and delimiters for standard CSV
        df = None
        delimiters = [',', ';', '\t', '|']
        best_result = None
        best_score = 0
        
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            current_app.logger.info(f"DEBUG: Trying encoding '{encoding}'")
            for delimiter in delimiters:
                current_app.logger.info(f"DEBUG: Testing delimiter '{delimiter}'")
                try:
                    # First try with headers
                    df_with_headers = pd.read_csv(file_path, encoding=encoding, dtype=str, sep=delimiter)
                    
                    # Skip if we only got 1 column and it's not the comma delimiter
                    if len(df_with_headers.columns) == 1 and delimiter != ',':
                        current_app.logger.info(f"DEBUG: Skipping delimiter '{delimiter}' - only got 1 column")
                        continue
                    
                    current_app.logger.info(f"DEBUG: Trying delimiter '{delimiter}', got {df_with_headers.shape[1]} columns")
                    
                    # Score this result - prefer more columns and cleaner data
                    score = len(df_with_headers.columns)
                    
                    # Check if first row looks like data rather than headers
                    first_row = df_with_headers.iloc[0] if len(df_with_headers) > 0 else None
                    has_date_in_first_row = False
                    
                    if first_row is not None:
                        for val in first_row:
                            if pd.notna(val) and re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', str(val).strip()):
                                has_date_in_first_row = True
                                score += 10  # Bonus for having date in data
                                break
                    
                    # Also check if column names look like data
                    has_date_in_columns = any(
                        re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', str(col).strip())
                        for col in df_with_headers.columns
                    )
                    
                    if has_date_in_columns:
                        score += 10  # Bonus for date in columns
                    
                    current_app.logger.info(f"DEBUG: Delimiter '{delimiter}' scored {score}")
                    
                    # Store best result
                    if score > best_score:
                        best_score = score
                        
                        # Check if first row looks like headers by examining column names
                        has_proper_headers = False
                        if len(df_with_headers.columns) > 0:
                            # Check for common CSV header patterns
                            header_keywords = ['type', 'product', 'date', 'description', 'amount', 'currency', 
                                             'started', 'completed', 'state', 'balance', 'fee', 'memo', 'payee']
                            header_matches = 0
                            for col in df_with_headers.columns:
                                col_lower = str(col).lower().strip()
                                if any(keyword in col_lower for keyword in header_keywords):
                                    header_matches += 1
                            
                            # If we have multiple header matches, treat as proper headers
                            if header_matches >= 3:
                                has_proper_headers = True
                                current_app.logger.info(f"DEBUG: Found {header_matches} header matches, treating as headers")
                        
                        if has_date_in_columns or (not has_date_in_first_row and len(df_with_headers.columns) > 4 and not has_proper_headers):
                            # No headers, read again without headers
                            current_app.logger.info(f"DEBUG: Reading without headers")
                            best_result = (pd.read_csv(file_path, encoding=encoding, dtype=str, header=None, sep=delimiter), encoding, delimiter)
                        else:
                            current_app.logger.info(f"DEBUG: Reading with headers")
                            best_result = (df_with_headers, encoding, delimiter)
                        
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            
            if best_result is not None:
                break
        
        if best_result is None:
            raise ValueError("Could not decode file with any encoding or delimiter")
        
        df, used_encoding, used_delimiter = best_result
        current_app.logger.info(f"DEBUG: Selected encoding '{used_encoding}' and delimiter '{used_delimiter}' with {len(df.columns)} columns")
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Common column name mappings (more comprehensive)
        column_mappings = {
            'date': ['date', 'transaction date', 'posting date', 'trans date', 'datum', 'fecha', 'data', 
                    'completed date', 'completed_date', 'settlement date', 'started date'],
            'description': ['description', 'memo', 'payee', 'transaction description', 'details', 'beschreibung', 
                           'descripcion', 'descrizione', 'reference', 'counterparty', 'merchant'],
            'amount': ['amount', 'debit', 'credit', 'transaction amount', 'value', 'betrag', 'importe', 
                      'importo', 'montant', 'total', 'sum']
        }
        
        # Detect column structure based on the DataFrame format
        found_columns = False
        actual_columns = {}
        
        # Check if we have numeric column names (header=None case) 
        if all(isinstance(col, int) for col in df.columns):
            current_app.logger.info(f"DEBUG: Numeric column names detected, checking data structure")
            # No headers - need to detect structure from data
            if len(df.columns) >= 3:
                # Check if this looks like CaixaBank format based on first row
                first_row = df.iloc[0] if len(df) > 0 else None
                current_app.logger.info(f"DEBUG: First row data: {first_row.tolist() if first_row is not None else None}")
                
                if first_row is not None:
                    # Look for CaixaBank pattern: Description, Date, Amount, Balance
                    val1 = str(first_row.iloc[1]).strip() if len(first_row) > 1 else ""
                    current_app.logger.info(f"DEBUG: Checking if '{val1}' (type: {type(val1)}) is a date")
                    
                    # Check if column 1 looks like a date (DD/MM/YYYY format)
                    date_pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'
                    date_match = re.match(date_pattern, val1)
                    current_app.logger.info(f"DEBUG: Date regex pattern: {date_pattern}")
                    current_app.logger.info(f"DEBUG: Date regex match result: {date_match is not None}")
                    current_app.logger.info(f"DEBUG: Match object: {date_match}")
                    
                    if date_match:
                        current_app.logger.info(f"DEBUG: Found CaixaBank format!")
                        # CaixaBank format: Description, Date, Amount, Balance
                        actual_columns = {
                            'description': 0,
                            'date': 1,
                            'amount': 2
                        }
                        found_columns = True
                    else:
                        current_app.logger.info(f"DEBUG: Date regex did not match, trying backup patterns...")
                        # Try alternative date patterns
                        backup_patterns = [
                            r'^\d{1,2}/\d{1,2}/\d{4}$',  # DD/MM/YYYY
                            r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
                            r'^\d{1,2}-\d{1,2}-\d{4}$',  # DD-MM-YYYY
                        ]
                        for pattern in backup_patterns:
                            if re.match(pattern, val1):
                                current_app.logger.info(f"DEBUG: Found CaixaBank format with pattern {pattern}!")
                                actual_columns = {
                                    'description': 0,
                                    'date': 1,
                                    'amount': 2
                                }
                                found_columns = True
                                break
            
            # If we still haven't found columns but we have 3+ columns, use default structure
            if not found_columns and len(df.columns) >= 3:
                current_app.logger.info(f"DEBUG: Using default 3-column structure")
                actual_columns = {
                    'description': 0,
                    'date': 1,
                    'amount': 2
                }
                found_columns = True
        
        # Special handling for CaixaBank format where amount might be split across columns
        if found_columns and len(df.columns) >= 4 and all(isinstance(k, int) for k in actual_columns.values()):
            # Only do this reconstruction if we're using numeric column indices
            sample_rows = df.head(3)
            needs_amount_reconstruction = False
            
            for _, row in sample_rows.iterrows():
                amount_idx = actual_columns.get('amount', 2)
                if amount_idx + 1 < len(df.columns):
                    val1 = str(row.iloc[amount_idx]).strip()
                    val2 = str(row.iloc[amount_idx + 1]).strip()
                    # Check if both look like numbers and val2 is 1-2 digits
                    if (val1.replace('-', '').isdigit() and 
                        val2.isdigit() and len(val2) <= 2):
                        needs_amount_reconstruction = True
                        break
            
            if needs_amount_reconstruction:
                actual_columns['amount_needs_reconstruction'] = True
        
        current_app.logger.info(f"DEBUG: Found columns: {found_columns}, Actual columns: {actual_columns}")
        
        if not found_columns:
            # Find actual column names using headers - Enhanced for Revolut and other banks
            actual_columns = {}
            df_columns_lower = [col.lower().strip() for col in df.columns]
            current_app.logger.info(f"DEBUG: Looking for headers in columns: {df_columns_lower}")
            
            # Detect specific bank formats
            has_revolut_columns = any(col in df_columns_lower for col in ['completed date', 'started date']) and \
                                 'description' in df_columns_lower and \
                                 'amount' in df_columns_lower
            
            # Check for CaixaBank format: item, date, amount, balance
            has_caixabank_columns = (len(df_columns_lower) == 4 and 
                                   'item' in df_columns_lower and 
                                   'date' in df_columns_lower and
                                   'amount' in df_columns_lower and 
                                   'balance' in df_columns_lower)
            
            if has_revolut_columns:
                current_app.logger.info("DEBUG: Detected Revolut CSV format!")
                # Revolut uses 'Completed Date' for the transaction date
                actual_columns = {
                    'date': 'Completed Date',
                    'description': 'Description', 
                    'amount': 'Amount'
                }
                found_columns = True
            elif has_caixabank_columns:
                current_app.logger.info("DEBUG: Detected CaixaBank CSV format!")
                # CaixaBank format: Item (description), Date, Amount, Balance
                actual_columns = {
                    'description': 'Item',
                    'date': 'Date',
                    'amount': 'Amount'
                }
                found_columns = True
            else:
                # Standard column mapping for other banks
                for key, possible_names in column_mappings.items():
                    for name in possible_names:
                        if name in df_columns_lower:
                            actual_columns[key] = df.columns[df_columns_lower.index(name)]
                            current_app.logger.info(f"DEBUG: Mapped {key} to column '{df.columns[df_columns_lower.index(name)]}'")
                            break
                    
                    # Also try partial matching for amount columns
                    if key == 'amount' and key not in actual_columns:
                        for col_name in df_columns_lower:
                            if any(term in col_name for term in ['amount', 'betrag', 'total', 'sum', 'value']):
                                actual_columns[key] = df.columns[df_columns_lower.index(col_name)]
                                current_app.logger.info(f"DEBUG: Partial matched {key} to column '{df.columns[df_columns_lower.index(col_name)]}'")
                                break
                
                if len(actual_columns) >= 3:
                    found_columns = True
                    current_app.logger.info(f"DEBUG: Found header-based columns: {actual_columns}")
            
            if not all(key in actual_columns for key in ['date', 'description', 'amount']):
                # If we can't find standard columns, use the first few columns
                cols = list(df.columns)
                if len(cols) >= 3:
                    actual_columns = {
                        'date': cols[0],
                        'description': cols[1],
                        'amount': cols[2]
                    }
        
        processed_rows = 0
        skipped_rows = 0
        
        for row_idx, row in df.iterrows():
            try:
                processed_rows += 1
                current_app.logger.info(f"DEBUG: Processing row {row_idx}: {row.tolist()}")
                
                # Check if we have the required columns
                if 'date' not in actual_columns or 'amount' not in actual_columns or 'description' not in actual_columns:
                    current_app.logger.error(f"DEBUG: Missing required columns in actual_columns: {actual_columns}")
                    # Use default CaixaBank structure as fallback
                    actual_columns = {'description': 0, 'date': 1, 'amount': 2}
                    current_app.logger.info(f"DEBUG: Using fallback CaixaBank structure: {actual_columns}")
                
                # Skip rows where essential fields are empty  
                date_idx = actual_columns['date']
                amount_idx = actual_columns['amount']
                
                # Handle both numeric indices and column names
                if isinstance(date_idx, int):
                    date_val = row.iloc[date_idx] if date_idx < len(row) else None
                else:
                    date_val = row[date_idx] if date_idx in row.index else None
                    
                if isinstance(amount_idx, int):
                    amount_val = row.iloc[amount_idx] if amount_idx < len(row) else None
                else:
                    amount_val = row[amount_idx] if amount_idx in row.index else None
                
                current_app.logger.info(f"DEBUG: Row {row_idx} - date_val: '{date_val}', amount_val: '{amount_val}'")
                
                if pd.isna(date_val) or pd.isna(amount_val):
                    current_app.logger.info(f"DEBUG: Skipping row {row_idx} - empty date or amount")
                    skipped_rows += 1
                    continue
                
                # Parse date
                date_str = str(date_val).strip()
                current_app.logger.info(f"DEBUG: Parsing date: '{date_str}'")
                
                if not date_str or date_str.lower() == 'nan':
                    current_app.logger.info(f"DEBUG: Skipping row {row_idx} - invalid date string")
                    skipped_rows += 1
                    continue
                
                try:
                    parsed_date = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
                    if pd.isna(parsed_date):
                        current_app.logger.error(f"DEBUG: Failed to parse date '{date_str}' in row {row_idx}")
                        skipped_rows += 1
                        continue
                    date_obj = parsed_date.date()
                    current_app.logger.info(f"DEBUG: Successfully parsed date: {date_obj}")
                except (ValueError, TypeError, AttributeError) as e:
                    current_app.logger.error(f"DEBUG: Date parsing error for '{date_str}': {e}")
                    skipped_rows += 1
                    continue
                
                # Parse amount with improved cleaning
                if actual_columns.get('amount_needs_reconstruction'):
                    # Reconstruct amount from split columns (e.g., "-11" and "49" -> "-11,49")
                    amount_idx = actual_columns['amount']
                    if isinstance(amount_idx, int):
                        amount_part1 = str(row.iloc[amount_idx]).strip()
                        amount_part2 = str(row.iloc[amount_idx + 1]).strip() if amount_idx + 1 < len(row) else ""
                    else:
                        # This reconstruction only applies to numeric indices, skip for named columns
                        amount_part1 = str(amount_val).strip()
                        amount_part2 = ""
                    amount_str = f"{amount_part1},{amount_part2}" if amount_part2 else amount_part1
                else:
                    amount_str = str(amount_val).strip()
                
                current_app.logger.info(f"DEBUG: Parsing amount: '{amount_str}'")
                amount = clean_amount_string(amount_str)
                current_app.logger.info(f"DEBUG: Cleaned amount: {amount}")
                
                # Skip zero amounts (likely invalid data)
                if amount == 0.0:
                    current_app.logger.info(f"DEBUG: Skipping row {row_idx} - zero amount")
                    skipped_rows += 1
                    continue
                
                # Get description
                desc_idx = actual_columns['description']
                if isinstance(desc_idx, int):
                    desc_val = row.iloc[desc_idx] if desc_idx < len(row) else None
                else:
                    desc_val = row[desc_idx] if desc_idx in row.index else None
                description = str(desc_val).strip()
                if description.lower() == 'nan':
                    description = 'Unknown Transaction'
                
                current_app.logger.info(f"DEBUG: Description: '{description}'")
                
                # Auto-categorize
                category = categorize_transaction(description, amount)
                current_app.logger.info(f"DEBUG: Category: '{category}'")
                
                transactions.append({
                    'date': date_obj,
                    'description': description,
                    'amount': amount,
                    'category': category
                })
                
                current_app.logger.info(f"DEBUG: Successfully added transaction {len(transactions)}")
                
            except (ValueError, KeyError, TypeError) as e:
                current_app.logger.error(f"DEBUG: Error processing row {row_idx}: {e}")
                skipped_rows += 1
                continue  # Skip invalid rows
        
        current_app.logger.info(f"DEBUG: Processed {processed_rows} rows, skipped {skipped_rows}, created {len(transactions)} transactions")
                
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")
    
    return transactions

@finance_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process transactions"""
    current_app.logger.info(f"CSV UPLOAD: Starting upload process...")
    current_app.logger.info(f"CSV UPLOAD: Request files: {list(request.files.keys())}")
    current_app.logger.info(f"CSV UPLOAD: Request form data: {dict(request.form)}")
    
    if 'file' not in request.files:
        current_app.logger.error(f"CSV UPLOAD: No file provided in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    current_app.logger.info(f"CSV UPLOAD: File received: {file.filename} (size: {file.content_length if hasattr(file, 'content_length') else 'unknown'})")
    
    if file.filename == '':
        current_app.logger.error(f"CSV UPLOAD: Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        current_app.logger.error(f"CSV UPLOAD: File type not allowed: {file.filename}")
        return jsonify({'error': 'File type not allowed. Please upload CSV or PDF files.'}), 400
    
    try:
        # Ensure upload folder exists
        upload_path = ensure_upload_folder()
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Initialize categories if needed
        initialize_categories()
        
        # Process file based on type
        if filename.lower().endswith('.csv'):
            current_app.logger.info(f"CSV UPLOAD: Processing CSV file: {filename}")
            current_app.logger.info(f"CSV UPLOAD: File path: {file_path}")
            transactions_data = parse_csv_file(file_path)
            current_app.logger.info(f"CSV UPLOAD: Parsed {len(transactions_data)} transactions from CSV")
        else:
            # For PDF files, we'll need to implement PDF parsing
            current_app.logger.error(f"CSV UPLOAD: PDF processing attempted for: {filename}")
            return jsonify({'error': 'PDF processing not yet implemented'}), 400
        
        # Save transactions to database
        saved_count = 0
        for trans_data in transactions_data:
            # Check if transaction already exists (basic duplicate detection)
            existing = Transaction.query.filter_by(
                date=trans_data['date'],
                description=trans_data['description'],
                amount=trans_data['amount']
            ).first()
            
            if not existing:
                transaction = Transaction(
                    date=trans_data['date'],
                    description=trans_data['description'],
                    amount=trans_data['amount'],
                    category=trans_data['category']
                )
                db.session.add(transaction)
                saved_count += 1
        
        db.session.commit()
        
        # Detect and remove refund pairs
        refunds_removed, transactions_removed = detect_and_remove_refunds()
        
        # Clean up uploaded file
        os.remove(file_path)
        
        message = f'Successfully processed {saved_count} transactions'
        if refunds_removed > 0:
            message += f' (removed {refunds_removed} refund pairs, {transactions_removed} total transactions)'
        
        return jsonify({
            'message': message,
            'total_processed': len(transactions_data),
            'saved_count': saved_count,
            'refunds_removed': refunds_removed,
            'final_count': saved_count - transactions_removed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@finance_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filtering"""
    category = request.args.get('category')
    
    query = Transaction.query
    
    if category:
        query = query.filter_by(category=category)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    
    # Calculate summary for filtered transactions
    summary = {
        'total_amount': 0,
        'income_total': 0,
        'expense_total': 0,
        'transaction_count': len(transactions)
    }
    
    for transaction in transactions:
        amount = transaction.amount
        summary['total_amount'] += amount
        if amount > 0:
            summary['income_total'] += amount
        else:
            summary['expense_total'] += abs(amount)
    
    response_data = {
        'transactions': [t.to_dict() for t in transactions],
        'total': len(transactions),
        'summary': {
            'total_amount': round(summary['total_amount'], 2),
            'income_total': round(summary['income_total'], 2),
            'expense_total': round(summary['expense_total'], 2),
            'transaction_count': summary['transaction_count'],
            'net_amount': round(summary['income_total'] - summary['expense_total'], 2)
        }
    }
    
    # Add category info if filtering by category
    if category:
        response_data['filtered_by_category'] = category
    
    return jsonify(response_data)

@finance_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories])

@finance_bp.route('/analytics/spending-trends', methods=['GET'])
def get_spending_trends():
    """Get monthly spending trends"""
    months = request.args.get('months', 12, type=int)
    
    # Get transactions from the last N months
    from sqlalchemy import func, extract
    
    results = db.session.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.amount < 0  # Only expenses (negative amounts)
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date),
        Transaction.category
    ).order_by(
        extract('year', Transaction.date).desc(),
        extract('month', Transaction.date).desc()
    ).all()
    
    # Organize data by month
    trends = {}
    for result in results:
        month_key = f"{int(result.year)}-{int(result.month):02d}"
        if month_key not in trends:
            trends[month_key] = {}
        trends[month_key][result.category] = abs(result.total)
    
    return jsonify(trends)

@finance_bp.route('/analytics/category-summary', methods=['GET'])
def get_category_summary():
    """Get spending summary by category"""
    from sqlalchemy import func
    
    results = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.amount < 0  # Only expenses
    ).group_by(Transaction.category).all()
    
    summary = []
    for result in results:
        summary.append({
            'category': result.category,
            'total': abs(result.total),
            'count': result.count
        })
    
    return jsonify(summary)

@finance_bp.route('/reset/transactions', methods=['DELETE'])
def reset_transactions():
    """Reset all transactions - clear all transaction data"""
    try:
        # Delete all transactions
        Transaction.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All transactions have been reset successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error resetting transactions: {str(e)}'
        }), 500

@finance_bp.route('/reset/categories', methods=['DELETE'])
def reset_categories():
    """Reset all categories and reinitialize with defaults"""
    try:
        # Delete all existing categories
        Category.query.delete()
        db.session.commit()
        
        # Reinitialize with default categories
        initialize_categories()
        
        return jsonify({
            'success': True,
            'message': 'Categories have been reset to defaults successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error resetting categories: {str(e)}'
        }), 500

@finance_bp.route('/reset/all', methods=['DELETE'])
def reset_all():
    """Reset everything - transactions and categories"""
    try:
        # Delete all transactions
        Transaction.query.delete()
        
        # Delete all categories
        Category.query.delete()
        
        db.session.commit()
        
        # Reinitialize with default categories
        initialize_categories()
        
        return jsonify({
            'success': True,
            'message': 'All data has been reset successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error resetting all data: {str(e)}'
        }), 500

@finance_bp.route('/expenses/summary', methods=['GET'])
def get_expense_summary():
    """Get expense summary grouped by categories with amounts and percentages"""
    try:
        # Get all transactions with categories
        transactions = Transaction.query.all()
        
        # Group by category and calculate totals
        category_totals = {}
        uncategorized_total = 0
        income_total = 0
        
        for transaction in transactions:
            amount = transaction.amount
            category = transaction.category
            
            # Separate income from expenses
            if amount > 0:
                income_total += amount
            else:
                expense_amount = abs(amount)
                if category and category.strip():
                    if category not in category_totals:
                        category_totals[category] = 0
                    category_totals[category] += expense_amount
                else:
                    uncategorized_total += expense_amount
        
        # Sort categories by total amount (descending)
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate total expenses
        total_expenses = sum(category_totals.values()) + uncategorized_total
        
        return jsonify({
            'total_income': round(income_total, 2),
            'total_expenses': round(total_expenses, 2),
            'net_amount': round(income_total - total_expenses, 2),
            'categories': [
                {
                    'name': category,
                    'amount': round(amount, 2),
                    'percentage': round((amount / total_expenses * 100) if total_expenses > 0 else 0, 1)
                }
                for category, amount in sorted_categories
            ],
            'uncategorized': {
                'amount': round(uncategorized_total, 2),
                'percentage': round((uncategorized_total / total_expenses * 100) if total_expenses > 0 else 0, 1)
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get expense summary: {str(e)}'}), 500

@finance_bp.route('/remove-refunds', methods=['POST'])
def manual_refund_removal():
    """Manually trigger refund detection and removal"""
    try:
        refunds_removed, transactions_removed = detect_and_remove_refunds()
        
        return jsonify({
            'success': True,
            'message': f'Refund detection completed',
            'refunds_removed': refunds_removed,
            'transactions_removed': transactions_removed
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to remove refunds: {str(e)}'
        }), 500

