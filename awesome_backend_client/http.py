"""Unified HTTP Client for UAProject API"""

import asyncio
import logging
from typing import Any, Optional, Union
from urllib.parse import urljoin

import httpx
from awesome_errors import BackendError, ErrorResponseParser
from pydantic import BaseModel

from .core.config import settings
from .core.errors import (
    APIAuthenticationError,
    APIConnectionError,
    APIPermissionError,
    APIRateLimitError,
    APIServerError,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """Unified HTTP client with retry logic and awesome-errors integration"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        impersonate_user_id: Optional[int] = None,
        settings_override: Optional[dict] = None,
    ):
        # Apply environment-specific config
        env_config = settings.ENVIRONMENT_CONFIG
        self.base_url = base_url or env_config.get(
            "API_BASE_URL", settings.FULL_API_URL
        )
        self.api_key = api_key or settings.BACKEND_API_KEY
        self.impersonate_user_id = impersonate_user_id
        self._client: Optional[httpx.AsyncClient] = None

        # Override settings if provided
        if settings_override:
            for key, value in settings_override.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

        if not self.api_key:
            raise ValueError("API key is required")

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create httpx client"""
        if self._client is None or self._client.is_closed:
            headers = self._get_default_headers()
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=settings.REQUEST_TIMEOUT,
                limits=httpx.Limits(
                    max_connections=settings.MAX_CONNECTIONS,
                    max_keepalive_connections=settings.MAX_CONNECTIONS // 5,
                ),
            )
        return self._client

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for requests"""
        headers = settings.HTTP_HEADERS.copy()
        headers["Authorization"] = f"{settings.BEARER_TOKEN_PREFIX} {self.api_key}"

        if self.impersonate_user_id:
            headers["X-Impersonate-User-ID"] = str(self.impersonate_user_id)

        return headers

    def set_impersonation(self, user_id: Optional[int]):
        """Set user impersonation for this client"""
        self.impersonate_user_id = user_id
        if self._client and not self._client.is_closed:
            if user_id:
                self._client.headers["X-Impersonate-User-ID"] = str(user_id)
            elif "X-Impersonate-User-ID" in self._client.headers:
                del self._client.headers["X-Impersonate-User-ID"]

    def _prepare_request_data(
        self, data: Optional[Union[dict[str, Any], BaseModel]]
    ) -> Optional[dict[str, Any]]:
        """Prepare request data for sending"""
        if data is None:
            return None

        if isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True, exclude_none=True)
        return data

    def _handle_http_error(self, e: httpx.HTTPStatusError, endpoint: str):
        """Handle HTTP status errors and convert to appropriate exceptions"""
        try:
            backend_error = ErrorResponseParser.parse_response(
                response_body=e.response.text,
                status_code=e.response.status_code,
                headers=dict(e.response.headers),
            )
        except Exception:
            backend_error = self._create_fallback_error(e, endpoint)

        # Convert to client-specific exceptions
        if e.response.status_code == 401:
            raise APIAuthenticationError(endpoint, str(backend_error)) from e
        elif e.response.status_code == 403:
            raise APIPermissionError(endpoint, str(backend_error)) from e
        elif e.response.status_code == 404:
            raise backend_error from e
        elif e.response.status_code == 422:
            raise backend_error from e
        elif e.response.status_code == 429:
            retry_after = self._get_retry_after(e.response.headers)
            raise APIRateLimitError(endpoint, retry_after) from e
        elif e.response.status_code >= 500:
            return APIServerError(endpoint, e.response.status_code, str(backend_error))
        else:
            raise APIConnectionError(
                str(backend_error), endpoint, e.response.status_code
            ) from e

    def _get_retry_after(self, headers) -> Optional[int]:
        """Extract retry-after header value"""
        if "Retry-After" not in headers:
            return None
        try:
            return int(headers["Retry-After"])
        except ValueError:
            return None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[dict[str, Any], BaseModel]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """Make HTTP request with retry logic and error handling"""
        url = urljoin(self.base_url, endpoint.lstrip("/"))
        request_headers = headers or {}
        request_data = self._prepare_request_data(data)

        last_exception = None
        max_retries = settings.MAX_RETRIES

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=request_data,
                    params=params,
                    headers=request_headers,
                    **kwargs,
                )
                return await self._handle_response(response, endpoint)

            except httpx.HTTPStatusError as e:
                error = self._handle_http_error(e, endpoint)
                if isinstance(error, APIServerError) and attempt < max_retries:
                    last_exception = error
                    delay = min(
                        settings.RETRY_DELAY * (settings.RETRY_BACKOFF_FACTOR**attempt),
                        settings.MAX_RETRY_DELAY,
                    )
                    logger.warning(f"Server error, retrying in {delay}s: {error}")
                    await asyncio.sleep(delay)
                else:
                    raise error from e

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = APIConnectionError(
                    f"Connection error: {str(e)}", endpoint
                )
                if attempt < max_retries:
                    delay = min(
                        settings.RETRY_DELAY * (settings.RETRY_BACKOFF_FACTOR**attempt),
                        settings.MAX_RETRY_DELAY,
                    )
                    logger.warning(f"Connection error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    break

        raise last_exception or APIConnectionError("All retries failed", endpoint)

    def _create_fallback_error(
        self, e: httpx.HTTPStatusError, endpoint: str
    ) -> BackendError:
        """Create fallback error when awesome-errors parsing fails"""
        return BackendError(
            f"HTTP {e.response.status_code} error at {endpoint}: {e.response.text}"
        )

    async def _handle_response(
        self, response: httpx.Response, endpoint: str
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """Handle HTTP response"""
        if response.status_code == 204:
            return {}

        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.json()
        elif "text/html" in content_type:
            return response.text
        else:
            return response.text

    # HTTP Methods
    async def get(
        self, endpoint: str, params: Optional[dict[str, Any]] = None, **kwargs
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """GET request"""
        return await self._make_request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: Optional[Union[dict[str, Any], BaseModel]] = None,
        **kwargs,
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """POST request"""
        return await self._make_request("POST", endpoint, data=data, **kwargs)

    async def put(
        self,
        endpoint: str,
        data: Optional[Union[dict[str, Any], BaseModel]] = None,
        **kwargs,
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """PUT request"""
        return await self._make_request("PUT", endpoint, data=data, **kwargs)

    async def patch(
        self,
        endpoint: str,
        data: Optional[Union[dict[str, Any], BaseModel]] = None,
        **kwargs,
    ) -> Union[dict[str, Any], list[dict[str, Any]], str]:
        """PATCH request"""
        return await self._make_request("PATCH", endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Union[dict[str, Any], str]:
        """DELETE request"""
        return await self._make_request("DELETE", endpoint, **kwargs)

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # noqa: U100
        await self.close()
