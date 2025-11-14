"""Ollama API client wrapper with error handling and retry logic."""

import os
import json
import logging
import requests
from typing import Dict, Optional, Any
from time import sleep

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for communicating with Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout: int = 30,
        max_retries: int = 2
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API endpoint
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.generate_url = f"{self.base_url}/api/generate"

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
        Generate text completion from Ollama.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0-1.0)
            format_json: Whether to request JSON format output

        Returns:
            Generated text or None if failed
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if format_json:
            payload["format"] = "json"

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Ollama API call (attempt {attempt + 1}/{self.max_retries + 1})")

                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=self.timeout
                )

                response.raise_for_status()
                result = response.json()

                generated_text = result.get("response", "").strip()

                if generated_text:
                    logger.debug(f"Generated response: {generated_text[:100]}...")
                    return generated_text
                else:
                    logger.warning("Empty response from Ollama")

            except requests.exceptions.Timeout:
                logger.warning(f"Ollama request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    sleep(1 * (attempt + 1))  # Exponential backoff
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama request failed: {e}")
                if attempt < self.max_retries:
                    sleep(1 * (attempt + 1))
                    continue

            except Exception as e:
                logger.error(f"Unexpected error in Ollama client: {e}")
                break

        return None

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Generate JSON response from Ollama.

        Args:
            prompt: The prompt to send

        Returns:
            Parsed JSON dict or None if failed
        """
        response_text = self.generate(prompt, format_json=True)

        if not response_text:
            return None

        try:
            # Try to parse as JSON
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")

            # Try to extract JSON from text (sometimes model adds extra text)
            try:
                # Find JSON object in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx + 1]
                    return json.loads(json_str)
            except Exception:
                pass

            return None


def get_ollama_client() -> OllamaClient:
    """
    Get configured Ollama client instance.

    Returns:
        OllamaClient instance with settings from environment
    """
    base_url = os.getenv("AI_ENDPOINT", "http://localhost:11434")
    model = os.getenv("AI_MODEL", "llama3.2:3b")
    timeout = int(os.getenv("AI_TIMEOUT", "30"))

    return OllamaClient(
        base_url=base_url,
        model=model,
        timeout=timeout
    )
