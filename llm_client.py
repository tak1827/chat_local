from typing import Optional, List, Dict, Any
import httpx

# `local` is used for llamacpp.
default_model = "local"

# The default time out is 30 minutes
# local infer is mostly super slow, as the local resources are limited
default_timeout = 30 * 60


class LLMClient:
    """HTTP client for LLM API endpoints (llamacpp, Ollama, OpenAI, etc.) using httpx."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        infer_model: str = default_model,
        emb_model: str = default_model,
        timeout: float = default_timeout,
    ):
        self.base_url = base_url or "http://127.0.0.1:8080"
        self.infer_model = infer_model
        self.emb_model = emb_model
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )

        if not self.is_healthy():
            raise ValueError(
                f"LLM API endpoint {self.base_url} is not reachable or healthy"
            )

    def is_healthy(self, timeout: float = 5.0) -> bool:
        try:
            response = self.client.get("/v1/models", timeout=timeout)
            response.raise_for_status()
            return True
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError):
            return False

    def get_embedding(self, input_text: str) -> List[float]:
        """
        Get embeddings for the input text.

        Args:
            input_text: Text to embed

        Returns:
            Response dictionary containing the embedding

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = "/v1/embeddings"
        payload = {"input": input_text}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        json_response = response.json()
        return json_response.get("data", [])[0].get("embedding")

    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Get chat completion from the model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters to pass to the API

        Returns:
            Response dictionary containing the completion

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response format is invalid
        """
        url = "/v1/chat/completions"
        payload = {"model": self.infer_model, "messages": messages, **kwargs}

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        json_response = response.json()

        return self._validate_chat_response(json_response)

    def chat_completion_with_image(
        self, text: str, image_url: str, role: str = "user", **kwargs
    ) -> str:
        """
        Convenience method for chat completion with text and image.

        Args:
            text: Text content
            image_url: Base64 encoded image URL (data URI format: "data:image/png;base64,...")
            role: Role of the message (default: "user")
            **kwargs: Additional parameters to pass to the API

        Returns:
            Response dictionary containing the completion
        """
        if not image_url.startswith("data:image/png;base64,"):
            image_url = f"data:image/png;base64,{image_url}"

        messages = [
            {
                "role": role,
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]
        return self.chat_completion(messages, **kwargs)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _validate_chat_response(self, json_response: Dict[str, Any]) -> str:
        try:
            choices = json_response.get("choices", [])
            if not choices:
                raise ValueError(
                    f"Invalid response format: no choices found in {json_response}"
                )

            message = choices[0].get("message", {})
            if not message:
                raise ValueError(
                    f"Invalid response format: no message found in {json_response}"
                )

            content = message.get("content")
            if content is None:
                raise ValueError(
                    f"Invalid response format: no content found in {json_response}"
                )

            return content
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Invalid response format: {json_response}") from e
