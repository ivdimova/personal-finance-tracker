"""Unit tests for the Ollama AI client."""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai.client import OllamaClient, get_ollama_client


class TestOllamaClientAvailability:

    def test_is_available_returns_true_when_reachable(self):
        """is_available returns True when Ollama responds 200."""
        client = OllamaClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch('src.ai.client.requests.get', return_value=mock_response):
            assert client.is_available() is True

    def test_is_available_returns_false_when_unreachable(self):
        """is_available returns False when connection fails."""
        client = OllamaClient()
        with patch('src.ai.client.requests.get', side_effect=Exception("Connection refused")):
            assert client.is_available() is False

    def test_is_available_returns_false_on_non_200(self):
        """is_available returns False when Ollama returns non-200."""
        client = OllamaClient()
        mock_response = MagicMock()
        mock_response.status_code = 503
        with patch('src.ai.client.requests.get', return_value=mock_response):
            assert client.is_available() is False


class TestOllamaClientGenerate:

    def _make_stream_response(self, content: str):
        """Build a mock streaming response with Ollama /api/chat format."""
        lines = [
            json.dumps({"message": {"content": chunk}, "done": False}).encode()
            for chunk in content
        ]
        lines.append(json.dumps({"message": {"content": ""}, "done": True}).encode())
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = lines
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_generate_returns_content(self):
        """generate() assembles streamed chunks into a full response."""
        client = OllamaClient(model="qwen3.5:9b")
        mock_resp = self._make_stream_response('{"ok": true}')
        with patch('src.ai.client.requests.post', return_value=mock_resp) as mock_post:
            result = client.generate("test prompt", format_json=True)
        assert result == '{"ok": true}'

    def test_generate_sends_think_false(self):
        """generate() always sends think:false to disable Qwen3 reasoning."""
        client = OllamaClient(model="qwen3.5:9b")
        mock_resp = self._make_stream_response("hello")
        with patch('src.ai.client.requests.post', return_value=mock_resp) as mock_post:
            client.generate("test")
        payload = mock_post.call_args.kwargs['json']
        assert payload.get('think') is False

    def test_generate_sends_format_json_when_requested(self):
        """generate() includes format:json in payload when format_json=True."""
        client = OllamaClient()
        mock_resp = self._make_stream_response("{}")
        with patch('src.ai.client.requests.post', return_value=mock_resp) as mock_post:
            client.generate("test", format_json=True)
        payload = mock_post.call_args.kwargs['json']
        assert payload.get('format') == 'json'

    def test_generate_omits_format_when_not_requested(self):
        """generate() omits format field when format_json=False."""
        client = OllamaClient()
        mock_resp = self._make_stream_response("plain text")
        with patch('src.ai.client.requests.post', return_value=mock_resp) as mock_post:
            client.generate("test", format_json=False)
        payload = mock_post.call_args.kwargs['json']
        assert 'format' not in payload

    def test_generate_strips_think_blocks(self):
        """generate() strips <think>...</think> blocks from the response."""
        client = OllamaClient()
        raw = '<think>reasoning here</think>{"answer": 42}'
        mock_resp = self._make_stream_response(raw)
        with patch('src.ai.client.requests.post', return_value=mock_resp):
            result = client.generate("test")
        assert '<think>' not in result
        assert result == '{"answer": 42}'

    def test_generate_returns_none_on_timeout(self):
        """generate() returns None when the request times out."""
        import requests as req
        client = OllamaClient(max_retries=0)
        with patch('src.ai.client.requests.post', side_effect=req.exceptions.Timeout):
            result = client.generate("test")
        assert result is None

    def test_generate_returns_none_on_empty_stream(self):
        """generate() returns None when the stream produces no content."""
        client = OllamaClient(max_retries=0)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines.return_value = [
            json.dumps({"message": {"content": ""}, "done": True}).encode()
        ]
        with patch('src.ai.client.requests.post', return_value=mock_resp):
            result = client.generate("test")
        assert result is None


class TestOllamaClientGenerateJson:

    def _mock_generate(self, client, return_value):
        return patch.object(client, 'generate', return_value=return_value)

    def test_generate_json_parses_valid_json(self):
        """generate_json() returns a dict for a valid JSON response."""
        client = OllamaClient()
        with self._mock_generate(client, '{"merchant": "Starbucks", "amount": 4.5}'):
            result = client.generate_json("parse this receipt")
        assert result == {"merchant": "Starbucks", "amount": 4.5}

    def test_generate_json_extracts_json_from_prose(self):
        """generate_json() extracts JSON embedded in surrounding text."""
        client = OllamaClient()
        with self._mock_generate(client, 'Here is the result: {"merchant": "Lidl"} done.'):
            result = client.generate_json("parse this")
        assert result == {"merchant": "Lidl"}

    def test_generate_json_returns_none_when_generate_fails(self):
        """generate_json() returns None when generate() returns None."""
        client = OllamaClient()
        with self._mock_generate(client, None):
            result = client.generate_json("test")
        assert result is None

    def test_generate_json_returns_none_on_invalid_json(self):
        """generate_json() returns None when response is not parseable JSON."""
        client = OllamaClient()
        with self._mock_generate(client, "this is not json at all"):
            result = client.generate_json("test")
        assert result is None


class TestGetOllamaClient:

    def test_uses_user_settings_over_env(self, app):
        """get_ollama_client() prefers UserSettings values over env vars."""
        with app.app_context():
            from src.models.user import UserSettings
            UserSettings.set('ai_model', 'custom-model:7b')
            UserSettings.set('ai_endpoint', 'http://custom-host:11434')
            client = get_ollama_client()
            assert client.model == 'custom-model:7b'
            assert 'custom-host' in client.base_url
            # cleanup
            UserSettings.set('ai_model', 'qwen3.5:9b')
            UserSettings.set('ai_endpoint', 'http://localhost:11434')

    def test_falls_back_to_env_when_no_user_settings(self):
        """get_ollama_client() falls back to env vars when UserSettings raises."""
        with patch('src.models.user.UserSettings.get', side_effect=Exception("DB unavailable")):
            with patch.dict('os.environ', {'AI_MODEL': 'fallback-model', 'AI_ENDPOINT': 'http://localhost:11434'}):
                client = get_ollama_client()
        assert client.model == 'fallback-model'
