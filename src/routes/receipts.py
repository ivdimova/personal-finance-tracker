import os
import re
import time
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
import uuid
from pathlib import Path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import PyPDF2
from io import BytesIO
import numpy as np

receipts_bp = Blueprint('receipts', __name__)

# Supported file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'webp', 'heic', 'heif'}

def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_receipts_folder():
    """Create receipts directory structure"""
    receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    # Create month folders (01-12)
    for month in range(1, 13):
        month_folder = os.path.join(receipts_dir, f"{month:02d}")
        os.makedirs(month_folder, exist_ok=True)
    
    return receipts_dir

def preprocess_png_image(image):
    """Enhanced preprocessing specifically for PNG images to improve OCR accuracy"""
    processed_images = []
    
    try:
        # Convert to RGB if needed
        if image.mode in ('RGBA', 'LA', 'P'):
            # Handle transparency by converting to white background
            if 'transparency' in image.info:
                image = image.convert('RGBA')
                white_bg = Image.new('RGBA', image.size, (255, 255, 255, 255))
                image = Image.alpha_composite(white_bg, image)
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Original image (baseline)
        processed_images.append(image.copy())
        
        # Enhancement 1: Contrast and brightness adjustment
        contrast_enhancer = ImageEnhance.Contrast(image)
        bright_enhancer = ImageEnhance.Brightness(image)
        
        # High contrast version
        high_contrast = contrast_enhancer.enhance(2.0)  # Increase contrast
        processed_images.append(high_contrast)
        
        # Medium contrast with slight brightness increase
        med_contrast = contrast_enhancer.enhance(1.5)
        med_bright = bright_enhancer.enhance(1.1)
        enhanced_img = med_bright.enhance(1.2)  # Apply brightness to medium contrast
        processed_images.append(enhanced_img)
        
        # Enhancement 2: Sharpening filter
        sharp_filter = ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3)
        sharpened = image.filter(sharp_filter)
        processed_images.append(sharpened)
        
        # Enhancement 3: Noise reduction with slight blur then sharpen
        blurred = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        denoised = blurred.filter(sharp_filter)
        processed_images.append(denoised)
        
        # Enhancement 4: Convert to grayscale with auto-levels
        grayscale = ImageOps.grayscale(image)
        auto_contrast_gray = ImageOps.autocontrast(grayscale)
        # Convert back to RGB for OCR
        gray_rgb = auto_contrast_gray.convert('RGB')
        processed_images.append(gray_rgb)
        
        # Enhancement 5: Invert if image appears to be dark background with light text
        try:
            # Check if image might be inverted (dark background)
            np_img = np.array(image)
            mean_brightness = np.mean(np_img)
            if mean_brightness < 100:  # Dark image, might need inversion
                inverted = ImageOps.invert(image)
                processed_images.append(inverted)
        except:
            pass  # Skip if numpy operations fail
        
        # Enhancement 6: High contrast grayscale
        high_contrast_gray = ImageOps.grayscale(high_contrast)
        high_contrast_gray_rgb = high_contrast_gray.convert('RGB')
        processed_images.append(high_contrast_gray_rgb)
        
        current_app.logger.info(f"Generated {len(processed_images)} processed PNG variants for OCR")
        return processed_images
        
    except Exception as e:
        current_app.logger.error(f"PNG preprocessing error: {str(e)}")
        # Return original image if preprocessing fails
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return [image]

def preprocess_jpeg_image(image):
    """Enhanced preprocessing specifically for JPEG images to improve OCR accuracy"""
    processed_images = []
    
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # OPTIMIZATION: Resize large images for faster processing
        width, height = image.size
        max_dimension = 1600  # Reasonable size for OCR
        if width > max_dimension or height > max_dimension:
            scale_factor = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            current_app.logger.info(f"Resized image from {width}x{height} to {image.size[0]}x{image.size[1]}")
        
        # Original image (baseline)
        processed_images.append(image.copy())
        
        # Enhancement 1: High contrast version (most effective for receipts)
        contrast_enhancer = ImageEnhance.Contrast(image)
        high_contrast = contrast_enhancer.enhance(2.0)
        processed_images.append(high_contrast)
        
        # Enhancement 2: Grayscale with auto-contrast (often best for text)
        grayscale = ImageOps.grayscale(image)
        auto_gray = ImageOps.autocontrast(grayscale)
        processed_images.append(auto_gray.convert('RGB'))
        
        # Enhancement 3: Combined contrast + brightness boost
        brightness_enhancer = ImageEnhance.Brightness(image)
        bright_contrast = brightness_enhancer.enhance(1.3)
        bright_contrast = ImageEnhance.Contrast(bright_contrast).enhance(1.7)
        processed_images.append(bright_contrast)
        
        # Enhancement 4: Sharpening (helps with blurry phone photos)
        sharpness_enhancer = ImageEnhance.Sharpness(image)
        sharpened = sharpness_enhancer.enhance(1.5)
        processed_images.append(sharpened)
        
        # Enhancement 5: Check if image needs inversion (dark background)
        try:
            np_img = np.array(image)
            mean_brightness = np.mean(np_img)
            if mean_brightness < 120:  # Dark image
                inverted = ImageOps.invert(image)
                processed_images.append(inverted)
                current_app.logger.info("Added inverted variant for dark image")
        except:
            pass
        
        current_app.logger.info(f"Generated {len(processed_images)} optimized JPEG variants for OCR")
        return processed_images
        
    except Exception as e:
        current_app.logger.error(f"JPEG preprocessing error: {str(e)}")
        # Return original image if preprocessing fails
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return [image]

def extract_text_from_file(file_path, filename):
    """Extract text from image or PDF using OCR"""
    try:
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            # Extract text from PDF
            text = extract_text_from_pdf(file_path)
        elif file_extension in ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif']:
            # Extract text from image using OCR
            text = extract_text_from_image(file_path)
        else:
            return ""
        
        current_app.logger.info(f"Extracted text length: {len(text)} characters")
        return text
        
    except Exception as e:
        current_app.logger.error(f"Error extracting text from {filename}: {str(e)}")
        return ""

def extract_text_from_image(file_path):
    """Extract text from image using Tesseract OCR with enhanced preprocessing"""
    try:
        # Open and preprocess image
        image = Image.open(file_path)
        file_extension = file_path.lower().split('.')[-1]
        
        current_app.logger.info(f"Processing image: {file_path}, format: {file_extension}, mode: {image.mode}, size: {image.size}")
        
        # Enhanced preprocessing for all image types
        if file_extension in ['png']:
            processed_images = preprocess_png_image(image)
        elif file_extension in ['jpg', 'jpeg']:
            processed_images = preprocess_jpeg_image(image)
        else:
            # Convert to RGB if necessary for other formats
            if image.mode != 'RGB':
                image = image.convert('RGB')
            processed_images = [image]
        
        current_app.logger.info(f"Generated {len(processed_images)} processed image variants")
        
        # Try the most effective OCR configurations for receipts
        ocr_configs = [
            '--psm 6',  # Uniform block of text (best for most receipts)
            '--psm 4',  # Single column of text  
            '--psm 11', # Sparse text (good for receipts with scattered text)
            '--psm 3',  # Fully automatic page segmentation
        ]
        
        best_text = ""
        max_length = 0
        best_config = ""
        
        # Try each processed image with each OCR configuration
        for i, img in enumerate(processed_images):
            for config in ocr_configs:
                try:
                    text = pytesseract.image_to_string(img, config=config, lang='eng').strip()
                    current_app.logger.debug(f"Variant {i}, config {config}: extracted {len(text)} characters")
                    if len(text) > max_length:
                        max_length = len(text)
                        best_text = text
                        best_config = f"variant_{i}_{config}"
                except Exception as ocr_error:
                    current_app.logger.debug(f"OCR failed for variant {i}, config {config}: {str(ocr_error)}")
                    continue
        
        current_app.logger.info(f"Best OCR result: {max_length} characters using {best_config}")
        current_app.logger.info(f"OCR extracted text sample: {best_text[:200]}...")
        return best_text
        
    except Exception as e:
        current_app.logger.error(f"Image OCR error: {str(e)}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return ""

def extract_text_from_pdf(file_path):
    """Extract text from PDF"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text.strip()
        
    except Exception as e:
        current_app.logger.error(f"PDF text extraction error: {str(e)}")
        return ""

def extract_receipt_info(file_path, filename):
    """Extract information from receipt using OCR and text analysis"""
    current_app.logger.info(f"Processing receipt: {filename}")
    
    try:
        # Extract text from file using OCR
        extracted_text = extract_text_from_file(file_path, filename)
        current_app.logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
        
        # Combine filename analysis with OCR text analysis
        merchant_from_filename = detect_merchant_from_filename(filename)
        merchant_from_text = detect_merchant_from_text(extracted_text)
        current_app.logger.info(f"Merchants: filename='{merchant_from_filename}', OCR='{merchant_from_text}'")
        
        # Prefer OCR-detected merchant if found, otherwise use filename
        merchant = merchant_from_text if merchant_from_text != 'Unknown' else merchant_from_filename
        
        # Try to detect date from OCR text first, then filename
        receipt_date = detect_date_from_text(extracted_text)
        current_app.logger.info(f"Date from OCR: {receipt_date}")
        
        if not receipt_date:
            receipt_date = detect_date_from_filename(filename)
            current_app.logger.info(f"Date from filename: {receipt_date}")
            
        if not receipt_date:
            receipt_date = datetime.now().strftime('%Y-%m-%d')
            current_app.logger.info(f"Using current date as fallback: {receipt_date}")
        
        # Detect amount from OCR text
        amount = detect_amount_from_text(extracted_text)
        current_app.logger.info(f"Amount detected: {amount}")
        
        return {
            'success': True,
            'merchant': merchant,
            'date': receipt_date,
            'amount': amount,
            'extracted_text_length': len(extracted_text),
        }
    except Exception as e:
        current_app.logger.error(f"Error processing receipt {filename}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def detect_merchant_from_text(text):
    """Detect merchant name from OCR text with enhanced parsing for stylized fonts"""
    if not text:
        return 'Unknown'
    
    text_lower = text.lower()
    
    # Common merchant patterns in receipt text
    merchants = {
        'uber': ['uber', 'uber eats', 'ubereats'],
        'starbucks': ['starbucks', 'sbux', 'star bucks'],
        'mcdonalds': ['mcdonalds', "mcdonald's", 'mcd', 'mc donald'],
        'amazon': ['amazon', 'amzn'],
        'walmart': ['walmart', 'wal-mart', 'wal mart'],
        'target': ['target'],
        'costco': ['costco'],
        'shell': ['shell'],
        'bp': ['bp ', ' bp'],
        'exxon': ['exxon', 'mobil'],
        'cvs': ['cvs'],
        'walgreens': ['walgreens'],
        'safeway': ['safeway'],
        'kroger': ['kroger'],
        'whole foods': ['whole foods', 'wholefoods'],
        'subway': ['subway'],
        'kfc': ['kfc', 'kentucky fried'],
        'burger king': ['burger king', 'bk '],
        'pizza hut': ['pizza hut'],
        'dominos': ['dominos', "domino's"],
        'taco bell': ['taco bell'],
        'chipotle': ['chipotle'],
        'panera': ['panera'],
        'dunkin': ['dunkin', 'dunkin donuts'],
        'seven eleven': ['7-eleven', '7 eleven', 'seven eleven'],
        'home depot': ['home depot'],
        'lowes': ['lowes', "lowe's"],
        'pier market': ['pier', 'pier market', 'piermarket'],
        'whole foods': ['whole foods', 'wholefoods'],
        'trader joes': ['trader joe', 'trader joes'],
    }
    
    # First check for exact merchant matches
    for merchant, keywords in merchants.items():
        for keyword in keywords:
            if keyword in text_lower:
                current_app.logger.info(f"Found merchant '{merchant}' via keyword '{keyword}'")
                return merchant.title()
    
    # Enhanced parsing for fragmented OCR text
    # Look for website patterns (common on receipts)
    website_patterns = [
        r'www\.([a-zA-Z]+)(?:market|store|shop|food|restaurant)?\.com?',
        r'([a-zA-Z]+)(?:market|store|shop|food|restaurant)\.com?',
        r'www\.([a-zA-Z]+)\.com?',
    ]
    
    for pattern in website_patterns:
        match = re.search(pattern, text_lower)
        if match:
            potential_name = match.group(1)
            if len(potential_name) > 2:  # Avoid single letters
                current_app.logger.info(f"Found merchant '{potential_name}' via website pattern")
                return potential_name.title()
    
    # Look for business-like phrases in the text
    # Clean up the text by removing common OCR artifacts
    cleaned_text = re.sub(r'[—_=\-]{2,}', ' ', text)  # Remove long dashes/underscores
    cleaned_text = re.sub(r'[^\w\s\.\,\&\']', ' ', cleaned_text)  # Keep only letters, spaces, common punctuation
    
    lines = cleaned_text.split('\n')[:10]  # Check first 10 lines
    
    for line in lines:
        line = line.strip()
        if 5 <= len(line) <= 35:  # Reasonable merchant name length
            # Skip common receipt words
            skip_words = {'receipt', 'invoice', 'bill', 'total', 'date', 'time', 'phone', 'address', 
                         'server', 'ticket', 'table', 'inside', 'order', 'thank you', 'thanks',
                         'visit', 'customer', 'store', 'location'}
            
            # Skip lines that are mostly numbers or timestamps
            if re.match(r'^[\d\s/:,\-\.]+$', line):
                continue
                
            if not any(word in line.lower() for word in skip_words):
                # Look for lines with mostly letters (potential business names)
                letter_ratio = sum(c.isalpha() for c in line) / len(line) if line else 0
                if letter_ratio > 0.6:  # At least 60% letters
                    # Clean up the line
                    clean_name = re.sub(r'[^\w\s&\'-]', '', line).strip()
                    if len(clean_name) > 3:
                        current_app.logger.info(f"Found potential merchant '{clean_name}' from text parsing")
                        return clean_name.title()
    
    # Last resort: look for any capitalized words that might be merchant names
    words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
    if words:
        # Filter out common non-merchant words
        business_words = []
        skip_caps = {'RECEIPT', 'INVOICE', 'TOTAL', 'DATE', 'TIME', 'SERVER', 'TABLE', 'TICKET',
                    'INSIDE', 'OUTSIDE', 'CARD', 'CASH', 'CHANGE', 'SUBTOTAL', 'TAX', 'TIP'}
        
        for word in words[:5]:  # Check first few capitalized words
            if word.upper() not in skip_caps and len(word) > 3:
                business_words.append(word)
        
        if business_words:
            potential_name = ' '.join(business_words[:2])  # Take first 1-2 words
            current_app.logger.info(f"Found potential merchant '{potential_name}' from capitalized words")
            return potential_name.title()
    
    current_app.logger.info("No merchant detected from OCR text")
    return 'Unknown'

def detect_date_from_text(text):
    """Detect date from OCR text using comprehensive patterns for international formats"""
    if not text:
        return None
    
    current_app.logger.info(f"Looking for dates in text sample: {text[:300]}...")
    
    # Comprehensive date patterns for international receipts
    date_patterns = [
        # Numeric formats with various separators
        r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})',          # DD/MM/YYYY, MM/DD/YYYY, DD.MM.YYYY, DD-MM-YYYY
        r'(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})',          # YYYY/MM/DD, YYYY.MM.DD, YYYY-MM-DD
        r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{2})',          # DD/MM/YY, MM/DD/YY
        r'(\d{2})[./\-](\d{1,2})[./\-](\d{1,2})',          # YY/MM/DD
        
        # Text month formats (English)
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{2,4})',  # DD Mon YYYY
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{2,4})', # Mon DD, YYYY
        
        # Common receipt date formats
        r'Date[:\s]*(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})',     # Date: DD/MM/YYYY
        r'Date[:\s]*(\d{2,4})[./\-](\d{1,2})[./\-](\d{1,2})',     # Date: YYYY/MM/DD
        r'Time[:\s]*\d{1,2}:\d{2}[:\d{2}]*\s*[APap][Mm]\s*(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})', # Time context
        
        # European formats
        r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})',                       # DD.MM.YYYY
        r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{2,4})', # Italian
        r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{2,4})', # Spanish
        r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{2,4})', # French
        
        # Compact formats often found on receipts
        r'(\d{2})(\d{2})(\d{2})',                                 # DDMMYY
        r'(\d{2})(\d{2})(\d{4})',                                 # DDMMYYYY
        r'(\d{4})(\d{2})(\d{2})',                                 # YYYYMMDD
        
        # Asian formats
        r'(\d{2,4})[年](\d{1,2})[月](\d{1,2})[日]',               # Japanese/Chinese
        r'(\d{2,4})/(\d{1,2})/(\d{1,2})',                         # Common Asian format
    ]
    
    month_maps = {
        # English months
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
        # Italian months
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
        'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
        # Spanish months
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        # French months
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
        'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12,
    }
    
    found_dates = []
    
    for i, pattern in enumerate(date_patterns):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                current_app.logger.info(f"Pattern {i} found groups: {groups}")
                
                if len(groups) == 3:
                    year, month, day = None, None, None
                    
                    # Handle different group patterns
                    if all(g.isdigit() for g in groups):
                        # All numeric
                        g1, g2, g3 = int(groups[0]), int(groups[1]), int(groups[2])
                        
                        # Determine format based on values and pattern
                        if len(groups[0]) == 4:  # First is year
                            year, month, day = g1, g2, g3
                        elif len(groups[2]) == 4:  # Last is year
                            if g1 > 12:  # First must be day
                                day, month, year = g1, g2, g3
                            elif g2 > 12:  # Second must be day
                                month, day, year = g1, g2, g3
                            else:
                                # Ambiguous - prefer DD/MM/YYYY for European receipts
                                day, month, year = g1, g2, g3
                        elif len(groups[2]) == 2:  # Two digit year
                            year = 2000 + g3 if g3 < 50 else 1900 + g3
                            if g1 > 12:
                                day, month = g1, g2
                            else:
                                day, month = g2, g1  # Assume DD/MM/YY
                    else:
                        # Text month format
                        for group in groups:
                            group_lower = group.lower().strip('.,')
                            if group_lower in month_maps:
                                month = month_maps[group_lower]
                                # Find the other two numeric values
                                nums = [int(g) for g in groups if g.isdigit()]
                                if len(nums) == 2:
                                    if nums[0] > 31:  # Must be year
                                        year, day = nums[0], nums[1]
                                    elif nums[1] > 31:  # Must be year
                                        day, year = nums[0], nums[1]
                                    else:
                                        # Assume smaller is day, larger is year
                                        if nums[0] > nums[1]:
                                            year, day = nums[0], nums[1]
                                        else:
                                            day, year = nums[0], nums[1]
                                break
                    
                    # Handle 2-digit years
                    if year and year < 100:
                        year = 2000 + year if year < 50 else 1900 + year
                    
                    # Validate and create date
                    if year and month and day:
                        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2030:
                            try:
                                date_obj = datetime(year, month, day)
                                found_date = date_obj.strftime('%Y-%m-%d')
                                current_app.logger.info(f"Found valid date: {found_date}")
                                found_dates.append((date_obj, found_date))
                            except ValueError:
                                continue
                                
            except (ValueError, AttributeError) as e:
                current_app.logger.debug(f"Date parsing error: {e}")
                continue
    
    if found_dates:
        # Return the most recent date found (likely the transaction date)
        found_dates.sort(key=lambda x: x[0], reverse=True)
        return found_dates[0][1]
    
    current_app.logger.info("No valid dates found in OCR text")
    return None

def detect_amount_from_text(text):
    """Detect total amount from OCR text"""
    if not text:
        return None
    
    # Look for total amount patterns
    amount_patterns = [
        r'total[:\s]*\$?([0-9]+\.?[0-9]*)',
        r'amount[:\s]*\$?([0-9]+\.?[0-9]*)',
        r'total due[:\s]*\$?([0-9]+\.?[0-9]*)',
        r'balance[:\s]*\$?([0-9]+\.?[0-9]*)',
        r'\$([0-9]+\.?[0-9]*)',  # Any dollar amount
        r'([0-9]+\.[0-9]{2})',   # Decimal amounts like 12.34
    ]
    
    found_amounts = []
    
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1)
                amount = float(amount_str)
                if 0.01 <= amount <= 10000:  # Reasonable amount range
                    found_amounts.append(amount)
            except (ValueError, IndexError):
                continue
    
    if found_amounts:
        # Return the largest amount found (likely to be the total)
        return max(found_amounts)
    
    return None

def detect_merchant_from_filename(filename):
    """Detect merchant name from filename using common patterns"""
    filename_lower = filename.lower()
    
    # Common merchant patterns
    merchants = {
        'uber': ['uber', 'ubereat', 'ubr'],
        'starbucks': ['starbucks', 'sbux'],
        'mcdonalds': ['mcdonalds', 'mcdonald', 'mcd'],
        'amazon': ['amazon', 'amzn'],
        'netflix': ['netflix'],
        'spotify': ['spotify'],
        'grocery': ['grocery', 'market', 'supermarket'],
        'restaurant': ['restaurant', 'rest', 'cafe', 'coffee'],
        'gas': ['gas', 'fuel', 'petrol', 'shell', 'bp'],
        'pharmacy': ['pharmacy', 'cvs', 'walgreens'],
        'hotel': ['hotel', 'motel', 'inn'],
        'airline': ['airline', 'flight', 'airport'],
    }
    
    for merchant, keywords in merchants.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return merchant.title()
    
    # Try to extract from common receipt naming patterns
    # Look for patterns like "receipt_merchant_date" or "merchant_invoice"
    parts = re.split(r'[-_\s]+', filename_lower.replace('.pdf', '').replace('.jpg', '').replace('.png', ''))
    
    # Skip common words
    skip_words = {'receipt', 'invoice', 'bill', 'scan', 'img', 'photo', 'screenshot', 'document'}
    potential_merchants = [part for part in parts if part not in skip_words and len(part) > 2]
    
    if potential_merchants:
        return potential_merchants[0].title()
    
    return 'Unknown'

def detect_date_from_filename(filename):
    """Try to detect date from filename"""
    # Look for various date patterns
    date_patterns = [
        r'(\d{4})[_-](\d{1,2})[_-](\d{1,2})',  # YYYY-MM-DD or YYYY_MM_DD
        r'(\d{1,2})[_-](\d{1,2})[_-](\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
        r'(\d{4})(\d{2})(\d{2})',              # YYYYMMDD
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.group(1)) == 4:  # First group is year
                    year, month, day = match.groups()
                else:  # Assume MM-DD-YYYY format
                    month, day, year = match.groups()
                
                # Validate date
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    return None

def generate_receipt_filename(merchant, date_str, original_extension, target_folder):
    """Generate standardized filename: YYYY-MM-DD-merchant-XX.ext"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        base_name = f"{date_obj.strftime('%Y-%m-%d')}-{merchant.lower().replace(' ', '-')}"
        
        # Check for existing files and add counter
        counter = 1
        while True:
            filename = f"{base_name}-{counter:02d}.{original_extension}"
            full_path = os.path.join(target_folder, filename)
            if not os.path.exists(full_path):
                break
            counter += 1
        
        return filename
    except ValueError:
        # Fallback if date parsing fails
        timestamp = int(time.time())
        return f"receipt-{merchant.lower().replace(' ', '-')}-{timestamp}.{original_extension}"

@receipts_bp.route('/upload', methods=['POST'])
def upload_receipts():
    """Handle multiple receipt uploads with processing"""
    start_time = time.time()
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    try:
        receipts_dir = create_receipts_folder()
        results = []
        successful = 0
        failed = 0
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Secure the filename
                    original_filename = secure_filename(file.filename)
                    original_extension = original_filename.rsplit('.', 1)[1].lower()
                    
                    # Save temporary file for processing
                    temp_filename = f"temp_{uuid.uuid4().hex}.{original_extension}"
                    temp_path = os.path.join(receipts_dir, temp_filename)
                    file.save(temp_path)
                    
                    # Process the receipt to extract information
                    receipt_info = extract_receipt_info(temp_path, original_filename)
                    
                    if receipt_info['success']:
                        # Determine target folder based on receipt date
                        try:
                            date_obj = datetime.strptime(receipt_info['date'], '%Y-%m-%d')
                            month_folder = f"{date_obj.month:02d}"
                        except ValueError:
                            # Default to current month if date parsing fails
                            month_folder = f"{datetime.now().month:02d}"
                        
                        target_folder = os.path.join(receipts_dir, month_folder)
                        
                        # Generate new filename
                        new_filename = generate_receipt_filename(
                            receipt_info['merchant'],
                            receipt_info['date'],
                            original_extension,
                            target_folder
                        )
                        
                        # Move file to final location
                        final_path = os.path.join(target_folder, new_filename)
                        os.rename(temp_path, final_path)
                        
                        results.append({
                            'success': True,
                            'original_name': file.filename,
                            'new_name': new_filename,
                            'merchant': receipt_info['merchant'],
                            'date': receipt_info['date'],
                            'amount': receipt_info['amount'],
                            'file_path': f"receipts/{month_folder}/{new_filename}",
                        })
                        successful += 1
                    else:
                        # Clean up temp file on failure
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        results.append({
                            'success': False,
                            'original_name': file.filename,
                            'error': receipt_info['error'],
                        })
                        failed += 1
                        
                except Exception as e:
                    current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
                    
                    # Clean up temp file on error
                    temp_path = os.path.join(receipts_dir, f"temp_{uuid.uuid4().hex}.tmp")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    results.append({
                        'success': False,
                        'original_name': file.filename,
                        'error': f"Processing error: {str(e)}",
                    })
                    failed += 1
            else:
                results.append({
                    'success': False,
                    'original_name': file.filename if file.filename else 'Unknown',
                    'error': 'Invalid file type or empty file',
                })
                failed += 1
        
        processing_time = round(time.time() - start_time, 2)
        
        return jsonify({
            'success': True,
            'receipts': results,
            'summary': {
                'total_files': len(files),
                'successful': successful,
                'failed': failed,
                'processing_time': processing_time,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@receipts_bp.route('/list', methods=['GET'])
def list_receipts():
    """List all receipts organized by month folders"""
    try:
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'receipts')
        
        if not os.path.exists(receipts_dir):
            return jsonify({'folders': [], 'total_receipts': 0})
        
        folders = []
        total_receipts = 0
        
        # List month folders
        for month in range(1, 13):
            month_folder = f"{month:02d}"
            month_path = os.path.join(receipts_dir, month_folder)
            
            if os.path.exists(month_path):
                files = [f for f in os.listdir(month_path) 
                        if os.path.isfile(os.path.join(month_path, f)) and 
                        allowed_file(f)]
                
                if files:  # Only include folders with files
                    month_names = [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]
                    
                    folders.append({
                        'name': f"{month_folder} ({month_names[month-1]})",
                        'path': month_folder,
                        'count': len(files),
                        'files': sorted(files)
                    })
                    total_receipts += len(files)
        
        return jsonify({
            'folders': folders,
            'total_receipts': total_receipts,
            'receipts_dir': receipts_dir
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing receipts: {str(e)}")
        return jsonify({'error': f'Failed to list receipts: {str(e)}'}), 500

@receipts_bp.route('/folder/<month>', methods=['GET'])
def get_folder_contents(month):
    """Get contents of a specific month folder"""
    try:
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'receipts')
        month_path = os.path.join(receipts_dir, month)
        
        if not os.path.exists(month_path):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(month_path):
            file_path = os.path.join(month_path, filename)
            if os.path.isfile(file_path) and allowed_file(filename):
                stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': f"receipts/{month}/{filename}"
                })
        
        return jsonify({
            'month': month,
            'files': sorted(files, key=lambda x: x['modified'], reverse=True)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting folder contents: {str(e)}")
        return jsonify({'error': f'Failed to get folder contents: {str(e)}'}), 500