"""Unified HTTP Client for UAProject API"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, TypeVar, Union
from urllib.parse import urljoin

import httpx
from awesome_errors import BackendError, ErrorDetail, ErrorResponseParser
from pydantic import BaseModel

from .core.config import settings
from .core.errors import (
    APIAuthenticationError,
    APIConnectionError,
    APIPermissionError,
    APIRateLimitError,
    APIServerError,
)

# Type aliases for API responses
JSONDict = dict[str, Any]
JSONList = list[JSONDict]
APIResponse = Union[JSONDict, JSONList, str]

T = TypeVar("T", bound=APIResponse)

logger = logging.getLogger(__name__)


class HTTPClient:
    """Unified HTTP client with retry logic and awesome-errors integration"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        impersonate_user_id: int | None = None,
        impersonate_discord_id: int | None = None,
        settings_override: dict[str, Any] | None = None,
    ):
        # Apply environment-specific config
        env_config = settings.ENVIRONMENT_CONFIG
        self.base_url = (
            base_url
            or (env_config.get("API_BASE_URL") if env_config else None)
            or settings.FULL_API_URL
        )
        self.api_key = api_key or settings.BACKEND_API_KEY
        self.impersonate_user_id = impersonate_user_id
        self.impersonate_discord_id = impersonate_discord_id
        self._client: httpx.AsyncClient | None = None

        # Override settings if provided
        if settings_override:
            for key, value in settings_override.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

        if not self.api_key:
            msg = "API key is required"
            raise ValueError(msg)

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
        
        if self.impersonate_discord_id:
            headers["X-Impersonate-Discord-ID"] = str(self.impersonate_discord_id)

        return headers

    def set_impersonation(self, user_id: int | None) -> None:
        """Set user impersonation for this client"""
        self.impersonate_user_id = user_id
        if self._client and not self._client.is_closed:
            if user_id:
                self._client.headers["X-Impersonate-User-ID"] = str(user_id)
            elif "X-Impersonate-User-ID" in self._client.headers:
                del self._client.headers["X-Impersonate-User-ID"]

    def _prepare_request_data(
        self, data: dict[str, Any] | BaseModel | None
    ) -> dict[str, Any] | None:
        """Prepare request data for sending"""
        if data is None:
            return None

        if isinstance(data, BaseModel):
            return data.model_dump(exclude_unset=True, exclude_none=True)
        return data

    def _handle_http_error(self, e: httpx.HTTPStatusError, endpoint: str) -> None:
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
        if e.response.status_code == 403:
            raise APIPermissionError(endpoint, str(backend_error)) from e
        if e.response.status_code in {404, 422}:
            raise backend_error from e
        if e.response.status_code == 429:
            retry_after = self._get_retry_after(e.response.headers)
            raise APIRateLimitError(endpoint, retry_after) from e
        if e.response.status_code >= 500:
            raise APIServerError(
                endpoint, e.response.status_code, str(backend_error)
            ) from e
        raise APIConnectionError(
            str(backend_error), endpoint, e.response.status_code
        ) from e

    def _get_retry_after(self, headers: httpx.Headers) -> int | None:
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
        data: dict[str, Any] | BaseModel | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> APIResponse:
        """Make HTTP request with retry logic and error handling"""
        # Ensure base_url has trailing slash for proper urljoin behavior
        if not self.base_url.endswith("/"):
            base = self.base_url + "/"
        else:
            base = self.base_url
        url = urljoin(base, endpoint.lstrip("/"))
        request_headers = headers or {}
        request_data = self._prepare_request_data(data)

        # DEBUG: Log impersonation headers
        final_headers = {**self._get_default_headers(), **request_headers}
        if "X-Impersonate-User-ID" in final_headers:
            print(
                f"[DEBUG HTTP] {method} {endpoint} with impersonation: {final_headers['X-Impersonate-User-ID']}"
            )
            print(f"[DEBUG HTTP] Full headers: {final_headers}")
        else:
            print(f"[DEBUG HTTP] {method} {endpoint} without impersonation")
            print(f"[DEBUG HTTP] Full headers: {final_headers}")

        last_exception: Exception | None = None
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
                try:
                    self._handle_http_error(e, endpoint)
                except APIServerError as server_error:
                    if attempt < max_retries:
                        last_exception = server_error
                        delay = min(
                            settings.RETRY_DELAY
                            * (settings.RETRY_BACKOFF_FACTOR**attempt),
                            settings.MAX_RETRY_DELAY,
                        )
                        logger.warning(
                            f"Server error, retrying in {delay}s: {server_error}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise server_error from e
                except Exception as client_error:
                    raise client_error from e

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = APIConnectionError(
                    f"Connection error: {e!s}", endpoint, None
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

        raise last_exception or APIConnectionError("All retries failed", endpoint, None)

    def _create_fallback_error(
        self, e: httpx.HTTPStatusError, endpoint: str
    ) -> BackendError:
        """Create fallback error when awesome-errors parsing fails"""
        return BackendError(
            error=ErrorDetail(
                code=f"HTTP {e.response.status_code} error at {endpoint}",
                message=e.response.text,
                request_id=e.response.headers.get("x-request-id", "unknown"),
                timestamp=datetime.now(timezone.utc),
                details={
                    "status_code": e.response.status_code,
                    "headers": dict(e.response.headers),
                    "text": e.response.text,
                },
            ),
            status_code=e.response.status_code,
        )

    async def _handle_response(
        self, response: httpx.Response, endpoint: str
    ) -> APIResponse:
        """Handle HTTP response"""
        if response.status_code == 204:
            return {}

        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            json_response = response.json()
            return json_response  # type: ignore[no-any-return]
        if "text/html" in content_type:
            return response.text
        return response.text

    # HTTP Methods
    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> APIResponse:
        """GET request"""

        return await self._make_request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | BaseModel | None = None,
        **kwargs: Any,
    ) -> APIResponse:
        """POST request"""
        return await self._make_request("POST", endpoint, data=data, **kwargs)

    async def put(
        self,
        endpoint: str,
        data: dict[str, Any] | BaseModel | None = None,
        **kwargs: Any,
    ) -> APIResponse:
        """PUT request"""
        return await self._make_request("PUT", endpoint, data=data, **kwargs)

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any] | BaseModel | None = None,
        **kwargs: Any,
    ) -> APIResponse:
        """PATCH request"""
        return await self._make_request("PATCH", endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> APIResponse:
        """DELETE request"""
        return await self._make_request("DELETE", endpoint, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "HTTPClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
