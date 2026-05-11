"""Ollama API client wrapper with streaming and think:false for fast Qwen3 responses."""

import os
import json
import logging
import re
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for communicating with Ollama API via the native /api/chat endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3.5:9b",
        timeout: int = 30,
        max_retries: int = 1
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API endpoint
            model: Model name to use
            timeout: Per-chunk read timeout in seconds (not total response time)
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.chat_url = f"{self.base_url}/api/chat"

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        format_json: bool = True
    ) -> Optional[str]:
        """
        Generate a response via the Ollama /api/chat endpoint with streaming.

        Uses think:false to disable Qwen3 chain-of-thought reasoning, which reduces
        response time from minutes to seconds.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            format_json: Whether to request JSON format output

        Returns:
            Generated text or None if failed
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "think": False,  # Reason: disables Qwen3 reasoning mode — without this, responses take minutes
            "options": {"temperature": temperature},
        }

        if format_json:
            payload["format"] = "json"

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Ollama chat call (attempt {attempt + 1}), model={self.model}")

                # Reason: timeout=(connect, read) — read timeout acts as per-chunk activity timeout
                response = requests.post(
                    self.chat_url,
                    json=payload,
                    stream=True,
                    timeout=(5, self.timeout)
                )
                response.raise_for_status()

                content = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            content += delta
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

                # Strip <think>...</think> blocks that some models emit even with think:false
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()

                if content:
                    logger.debug(f"Generated response: {content[:100]}...")
                    return content
                else:
                    logger.warning("Empty response from Ollama")

            except requests.exceptions.Timeout:
                logger.warning(f"Ollama chunk timeout after {self.timeout}s (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama request failed: {e}")
                if attempt < self.max_retries:
                    continue

            except Exception as e:
                logger.error(f"Unexpected error in Ollama client: {e}")
                break

        return None

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Generate a JSON response from Ollama.

        Args:
            prompt: The prompt to send

        Returns:
            Parsed JSON dict or None if failed
        """
        response_text = self.generate(prompt, format_json=True)

        if not response_text:
            return None

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.debug(f"Direct JSON parse failed, trying extraction. Raw: {response_text[:200]}")

            # Extract JSON object from text if model added surrounding prose
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    return json.loads(response_text[start_idx:end_idx + 1])
            except Exception:
                pass

            logger.error(f"Failed to extract JSON from response: {response_text[:200]}")
            return None


def get_ollama_client() -> OllamaClient:
    """
    Get configured Ollama client instance.
    UserSettings override .env values when set.

    Returns:
        OllamaClient instance with settings from UserSettings or environment
    """
    # Reason: import here to avoid circular imports at module load time
    try:
        from src.models.user import UserSettings
        base_url = UserSettings.get('ai_endpoint') or os.getenv("AI_ENDPOINT", "http://localhost:11434")
        model = UserSettings.get('ai_model') or os.getenv("AI_MODEL", "qwen3.5:9b")
    except Exception:
        base_url = os.getenv("AI_ENDPOINT", "http://localhost:11434")
        model = os.getenv("AI_MODEL", "qwen3.5:9b")

    # Per-chunk timeout — 30s with no new tokens = hung request
    timeout = int(os.getenv("AI_TIMEOUT", "30"))

    return OllamaClient(base_url=base_url, model=model, timeout=timeout)
