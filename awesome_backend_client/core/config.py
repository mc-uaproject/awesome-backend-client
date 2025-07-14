from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AwesomeBackendClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="AWESOME_BACKEND_CLIENT_",
    )

    # Core API Settings
    API_VERSION: str = "v3"
    API_BASE_URL: str = "https://api.uaproject.xyz"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = False

    # Authentication
    BACKEND_API_KEY: str | None = None
    CALLBACK_SECRET: str | None = None

    # HTTP Client Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    RETRY_BACKOFF_FACTOR: float = 2.0
    MAX_RETRY_DELAY: float = 60.0
    REQUEST_TIMEOUT: float = 30.0
    MAX_CONNECTIONS: int = 100
    KEEPALIVE_TIMEOUT: int = 30

    # Library Constants
    USER_AGENT: str = "UAProject-PyLibrary/1.0"
    BEARER_TOKEN_PREFIX: str = "Bearer"
    API_KEY_HEADER: str = "Authorization"

    # Webhook Headers
    WEBHOOK_SIGNATURE_HEADER: str = "X-Webhook-Signature"
    WEBHOOK_EVENT_HEADER: str = "X-Webhook-Event"
    WEBHOOK_TIMESTAMP_HEADER: str = "X-Webhook-Timestamp"

    # Webhook Auto-Registration
    WEBHOOK_AUTO_REGISTER: bool = True
    WEBHOOK_ENDPOINT_URL: str | None = None
    WEBHOOK_SECRET: str | None = None
    WEBHOOK_VERIFY_SIGNATURE: bool = False

    # Webhook Retry Configuration
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_DELAY: int = 60
    WEBHOOK_TIMEOUT: int = 30

    # Webhook Templates Configuration
    WEBHOOK_ENABLE_USER_EVENTS: bool = True
    WEBHOOK_ENABLE_APPLICATION_EVENTS: bool = True
    WEBHOOK_ENABLE_TRANSACTION_EVENTS: bool = True
    WEBHOOK_ENABLE_TICKET_EVENTS: bool = False
    WEBHOOK_ENABLE_NEWS_EVENTS: bool = False

    # Webhook Security
    WEBHOOK_HMAC_ALGORITHM: str = "sha256"
    WEBHOOK_SIGNATURE_TOLERANCE: int = 300  # 5 minutes

    # WebSocket Configuration
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_AUTO_RECONNECT: bool = True
    WEBSOCKET_MAX_RECONNECT_ATTEMPTS: int = 5
    WEBSOCKET_RECONNECT_DELAY: float = 1.0
    WEBSOCKET_RECONNECT_BACKOFF_FACTOR: float = 2.0
    WEBSOCKET_MAX_RECONNECT_DELAY: float = 30.0
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    WEBSOCKET_CONNECTION_TIMEOUT: float = 10.0
    WEBSOCKET_ENDPOINT: str = "/ws"

    # Cache Configuration
    CACHE_ENABLED: bool = False  # Disabled until awesome-redis is added back
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_USER: int = 600  # 10 minutes
    CACHE_TTL_ROLE: int = 1800  # 30 minutes
    CACHE_PREFIX: str = "uaproject:client:"

    # Event System Configuration
    EVENT_HANDLERS_MAX: int = 100
    EVENT_HANDLER_TIMEOUT: float = 30.0
    EVENT_QUEUE_MAX_SIZE: int = 1000

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_SECOND: float = 10.0
    RATE_LIMIT_BURST_SIZE: int = 50

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_HTTP_REQUESTS: bool = False
    LOG_WEBSOCKET_MESSAGES: bool = False

    # Model Validation
    MODEL_VALIDATION_STRICT: bool = True
    MODEL_CACHE_SCHEMAS: bool = True

    # Development/Debug Features
    DEV_MODE: bool = False
    DEV_MOCK_RESPONSES: bool = False
    DEV_SAVE_RESPONSES: bool = False

    # Computed Properties
    @computed_field
    @property
    def API_PREFIX(self) -> str:
        return f"/{self.API_VERSION}"

    @computed_field
    @property
    def FULL_API_URL(self) -> str:
        return f"{self.API_BASE_URL.rstrip('/')}{self.API_PREFIX}"

    @computed_field
    @property
    def RETRYABLE_STATUS_CODES(self) -> set[int]:
        """HTTP status codes that should trigger retries"""
        return {429, 500, 502, 503, 504}

    @computed_field
    @property
    def WEBSOCKET_URL(self) -> str:
        """WebSocket URL for real-time events"""
        ws_scheme = "wss" if self.API_BASE_URL.startswith("https") else "ws"
        base_url = self.API_BASE_URL.replace("https://", "").replace("http://", "")
        return f"{ws_scheme}://{base_url}{self.API_PREFIX}{self.WEBSOCKET_ENDPOINT}"

    @computed_field
    @property
    def HTTP_HEADERS(self) -> dict[str, str]:
        """Default HTTP headers for all requests"""
        headers = {
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return headers

    @computed_field
    @property
    def ENVIRONMENT_CONFIG(self) -> dict[str, str]:
        """Environment-specific configuration"""
        configs = {
            "local": {
                "API_BASE_URL": "http://localhost:8001",
                "LOG_LEVEL": "DEBUG",
                "DEV_MODE": True,
            },
            "staging": {
                "API_BASE_URL": "https://staging-api.uaproject.xyz",
                "LOG_LEVEL": "INFO",
            },
            "production": {
                "API_BASE_URL": "https://api.uaproject.xyz",
                "LOG_LEVEL": "WARNING",
                "RATE_LIMIT_ENABLED": True,
            },
        }
        return configs.get(self.ENVIRONMENT, {})

    def get_cache_key(self, resource: str, identifier: str) -> str:
        """Generate cache key for resource"""
        return f"{self.CACHE_PREFIX}{resource}:{identifier}"

    def get_cache_ttl(self, resource: str) -> int:
        """Get TTL for specific resource type"""
        ttl_map = {
            "user": self.CACHE_TTL_USER,
            "role": self.CACHE_TTL_ROLE,
        }
        return ttl_map.get(resource, self.CACHE_TTL_DEFAULT)

    def is_retryable_status(self, status_code: int) -> bool:
        """Check if status code should trigger retry"""
        return status_code in self.RETRYABLE_STATUS_CODES


settings = AwesomeBackendClientSettings()
