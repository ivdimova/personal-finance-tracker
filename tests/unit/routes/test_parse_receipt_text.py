"""Tests for the POST /api/receipts/parse-text endpoint."""
import pytest
from unittest.mock import patch


RECEIPT_TEXT = "STARBUCKS\n123 Main St\nDate: 2026-05-10\nCoffee 4.50\nTotal: 4.50 EUR"
AI_RESULT = {
    "merchant": "Starbucks",
    "date": "2026-05-10",
    "amount": 4.50,
    "currency": "EUR",
    "confidence": 0.95,
}


class TestParseReceiptText:

    @pytest.mark.unit
    def test_returns_ai_result_on_success(self, client):
        """Returns parsed fields when AI succeeds."""
        with patch('src.ai.receipt_parser.extract_receipt_data', return_value=AI_RESULT):
            response = client.post(
                '/api/receipts/parse-text',
                json={'text': RECEIPT_TEXT},
            )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['merchant'] == 'Starbucks'
        assert data['amount'] == 4.50

    @pytest.mark.unit
    def test_returns_failure_when_ai_returns_none(self, client):
        """Returns success:false (not 500) when AI cannot parse the receipt."""
        with patch('src.ai.receipt_parser.extract_receipt_data', return_value=None):
            response = client.post(
                '/api/receipts/parse-text',
                json={'text': RECEIPT_TEXT},
            )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False

    @pytest.mark.unit
    def test_returns_400_on_missing_text(self, client):
        """Returns 400 when text field is absent."""
        response = client.post('/api/receipts/parse-text', json={})
        assert response.status_code == 400

    @pytest.mark.unit
    def test_returns_400_on_short_text(self, client):
        """Returns 400 when text is too short to be a real receipt."""
        response = client.post('/api/receipts/parse-text', json={'text': 'hi'})
        assert response.status_code == 400

    @pytest.mark.unit
    def test_returns_400_on_empty_body(self, client):
        """Returns 400 when request body is missing entirely."""
        response = client.post(
            '/api/receipts/parse-text',
            content_type='application/json',
        )
        assert response.status_code == 400

    @pytest.mark.unit
    def test_returns_failure_when_ai_disabled(self, client, app):
        """Returns success:false when ai_enabled is set to false in UserSettings."""
        with app.app_context():
            from src.models.user import UserSettings
            UserSettings.set('ai_enabled', 'false')

        with patch('src.ai.receipt_parser.extract_receipt_data') as mock_ai:
            response = client.post(
                '/api/receipts/parse-text',
                json={'text': RECEIPT_TEXT},
            )
        # AI should not be called and endpoint returns gracefully
        mock_ai.assert_not_called()
        assert response.status_code == 200
        assert response.get_json()['success'] is False

        # cleanup
        with app.app_context():
            from src.models.user import UserSettings
            UserSettings.set('ai_enabled', 'true')

    @pytest.mark.unit
    def test_returns_failure_gracefully_on_ai_exception(self, client):
        """Returns success:false (not 500) when AI raises an unexpected exception."""
        with patch('src.ai.receipt_parser.extract_receipt_data', side_effect=RuntimeError("boom")):
            response = client.post(
                '/api/receipts/parse-text',
                json={'text': RECEIPT_TEXT},
            )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
