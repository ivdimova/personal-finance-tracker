"""AI-powered receipt data extraction using Ollama."""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
from src.ai.client import get_ollama_client
from src.ai.prompts import RECEIPT_PARSING_PROMPT

logger = logging.getLogger(__name__)


def extract_receipt_data(
    ocr_text: str,
    min_confidence: float = 0.75
) -> Optional[Dict[str, any]]:
    """
    Use AI to extract structured data from receipt text.

    Args:
        ocr_text: Raw OCR text from receipt
        min_confidence: Minimum confidence to return result

    Returns:
        Dict with merchant, date, amount, currency, confidence
        Example: {
            'merchant': 'Starbucks',
            'date': '2025-11-14',
            'amount': 4.50,
            'currency': 'EUR',
            'confidence': 0.90
        }
    """
    # Check if AI is enabled
    ai_enabled = os.getenv("AI_ENABLED", "true").lower() == "true"
    if not ai_enabled:
        logger.debug("AI receipt parsing disabled")
        return None

    # Validate input
    if not ocr_text or len(ocr_text.strip()) < 10:
        logger.warning("OCR text too short for AI parsing")
        return None

    try:
        # Get Ollama client
        client = get_ollama_client()

        # Check if service is available
        if not client.is_available():
            logger.warning("Ollama service not available for receipt parsing")
            return None

        # Format the prompt (truncate very long text to avoid token limits)
        max_text_length = 2000
        if len(ocr_text) > max_text_length:
            ocr_text = ocr_text[:max_text_length] + "..."
            logger.info("Truncated OCR text for AI processing")

        prompt = RECEIPT_PARSING_PROMPT.format(ocr_text=ocr_text)

        # Generate response
        result = client.generate_json(prompt)

        if not result:
            logger.warning("Failed to get AI receipt parsing response")
            return None

        # Extract and validate fields
        merchant = result.get('merchant', 'Unknown')
        date_str = result.get('date')
        amount = result.get('amount')
        currency = result.get('currency', 'EUR')
        confidence = float(result.get('confidence', 0.0))

        # Validate merchant is not a personal name
        if merchant and merchant != 'Unknown':
            # Check if merchant looks like a personal name (no business indicators)
            business_indicators = [
                'ltd', 'inc', 'llc', 'corp', 'gmbh', 's.a.', 'plc', 'pte',
                'co.', 'company', 'limited', 'store', 'shop', 'cafe', 'restaurant',
                'hotel', 'market', 'center', 'service', 'group', '&', 'and'
            ]

            merchant_lower = merchant.lower()
            has_business_indicator = any(
                indicator in merchant_lower for indicator in business_indicators
            )

            # Check if it looks like a personal name (2-3 words, all capitalized first letters)
            words = merchant.split()
            looks_like_personal_name = (
                len(words) == 2 or len(words) == 3
            ) and all(
                word[0].isupper() and word[1:].islower() for word in words if word
            )

            # Reject if it looks like a personal name without business indicators
            if looks_like_personal_name and not has_business_indicator:
                logger.warning(
                    f"Rejected merchant '{merchant}' - appears to be a personal name"
                )
                merchant = 'Unknown'
                confidence = 0.5  # Lower confidence since we rejected the merchant

        # Validate confidence
        if not (0.0 <= confidence <= 1.0):
            logger.warning(f"Invalid confidence value: {confidence}")
            confidence = 0.5

        # Check minimum confidence threshold
        if confidence < min_confidence:
            logger.info(
                f"AI confidence {confidence:.2f} below threshold {min_confidence}"
            )
            return None

        # Validate and parse date
        parsed_date = None
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format from AI: {date_str}")
                parsed_date = None

        # Validate amount
        parsed_amount = None
        if amount is not None:
            try:
                parsed_amount = float(amount)
                if parsed_amount <= 0 or parsed_amount > 1000000:
                    logger.warning(f"Suspicious amount from AI: {parsed_amount}")
                    parsed_amount = None
            except (ValueError, TypeError):
                logger.warning(f"Invalid amount from AI: {amount}")
                parsed_amount = None

        result_data = {
            'merchant': merchant if merchant != 'Unknown' else None,
            'date': parsed_date,
            'amount': parsed_amount,
            'currency': currency,
            'confidence': confidence
        }

        logger.info(
            f"AI extracted receipt data: {result_data['merchant']}, "
            f"{result_data['date']}, ${result_data['amount']} "
            f"(confidence: {confidence:.2f})"
        )

        return result_data

    except Exception as e:
        logger.error(f"Error in AI receipt parsing: {e}", exc_info=True)
        return None
