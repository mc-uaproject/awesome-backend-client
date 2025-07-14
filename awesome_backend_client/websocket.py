"""
WebSocket client for real-time events from UAProject API

Integrates with the backend's WebSocket endpoint for real-time notifications.
Uses websockets library for WebSocket connections and
AwesomeBackendClientSettings for configuration.
"""

import asyncio
import json
import logging
from typing import Any, Callable
from urllib.parse import urlparse

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus, WebSocketException

from .core.config import settings

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    WebSocket client for UAProject events with settings-based configuration

    Connects to the backend's WebSocket endpoint and handles
    real-time event subscriptions with automatic reconnection.
    """

    def __init__(self, client):
        self.client = client
        self._websocket: websockets.WebSocketServerProtocol | None = None
        self._listen_task: asyncio.Task | None = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = settings.WEBSOCKET_MAX_RECONNECT_ATTEMPTS
        self._connected = False
        self._enabled = settings.WEBSOCKET_ENABLED
        self._should_reconnect = True

        # Event listeners
        self._listeners: dict[str, list[Callable]] = {}

    async def connect(self) -> bool:
        """Connect to WebSocket endpoint"""
        if not self._enabled:
            logger.info("WebSocket disabled in settings")
            return False

        try:
            # Build WebSocket URL
            ws_url = self._build_websocket_url()

            # Prepare headers with authentication
            headers = {
                "Authorization": (
                    f"{settings.BEARER_TOKEN_PREFIX} {self.client.api_key}"
                ),
            }

            # Add user impersonation header if needed
            if self.client.impersonate_user_id:
                headers["X-Impersonate-User-ID"] = str(self.client.impersonate_user_id)

            logger.info(f"Connecting to WebSocket: {ws_url}")

            # Connect to WebSocket with settings-based configuration
            self._websocket = await websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=settings.WEBSOCKET_HEARTBEAT_INTERVAL,
                ping_timeout=settings.WEBSOCKET_CONNECTION_TIMEOUT,
                close_timeout=settings.WEBSOCKET_CONNECTION_TIMEOUT,
                max_size=2**20,  # 1MB max message size
                max_queue=settings.EVENT_QUEUE_MAX_SIZE,
            )

            self._connected = True
            self._reconnect_attempts = 0
            self._should_reconnect = True

            # Start listening task
            self._listen_task = asyncio.create_task(self._listen_loop())

            logger.info("WebSocket connected successfully")
            return True

        except (InvalidStatus, OSError, WebSocketException) as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during WebSocket connection: {e}")
            return False

    async def disconnect(self):
        """Disconnect from WebSocket"""
        logger.info("Disconnecting WebSocket")

        self._connected = False
        self._should_reconnect = False

        # Cancel listening task
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket connection
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()

        self._websocket = None
        self._listen_task = None

    def add_listener(self, event: str, callback: Callable):
        """Add event listener"""
        if event not in self._listeners:
            self._listeners[event] = []

        if len(self._listeners[event]) >= settings.EVENT_HANDLERS_MAX:
            logger.warning(
                f"Maximum event handlers ({settings.EVENT_HANDLERS_MAX}) "
                f"reached for event '{event}'"
            )
            return

        self._listeners[event].append(callback)
        logger.debug(f"Added listener for event: {event}")

    def remove_listener(self, event: str, callback: Callable):
        """Remove event listener"""
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)
            logger.debug(f"Removed listener for event: {event}")

    async def send_message(self, message: dict[str, Any]):
        """Send message to WebSocket"""
        if not self._connected or not self._websocket:
            logger.warning("Cannot send message: WebSocket not connected")
            return False

        try:
            await self._websocket.send(json.dumps(message))
            return True
        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False

    async def subscribe_events(self, events: list[str]):
        """Subscribe to specific events via WebSocket"""
        message = {"action": "subscribe", "events": events}
        success = await self.send_message(message)
        if success:
            logger.debug(f"Subscribed to events: {events}")
        return success

    async def unsubscribe_events(self, events: list[str]):
        """Unsubscribe from specific events via WebSocket"""
        message = {"action": "unsubscribe", "events": events}
        success = await self.send_message(message)
        if success:
            logger.debug(f"Unsubscribed from events: {events}")
        return success

    def _build_websocket_url(self) -> str:
        """Build WebSocket URL from HTTP URL"""
        # Parse the base URL
        parsed = urlparse(self.client.base_url)

        # Convert scheme
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"

        # Build WebSocket URL
        ws_url = f"{ws_scheme}://{parsed.netloc}{settings.API_PREFIX}{settings.WEBSOCKET_ENDPOINT}"

        return ws_url

    async def _listen_loop(self):
        """Main WebSocket listening loop"""
        try:
            async for message in self._websocket:
                try:
                    # Parse JSON message
                    if isinstance(message, str):
                        data = json.loads(message)
                    else:
                        # Handle binary messages if needed
                        data = json.loads(message.decode("utf-8"))

                    await self._handle_message(data)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")

        except ConnectionClosed as e:
            logger.info(f"WebSocket connection closed: {e}")
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            logger.error(f"WebSocket listen loop error: {e}")
        finally:
            self._connected = False
            await self._handle_disconnect()

    async def _handle_disconnect(self):
        """Handle WebSocket disconnection and potential reconnection"""
        if not self._should_reconnect:
            return

        # Attempt reconnection if enabled and not manually disconnected
        if (
            self._reconnect_attempts < self._max_reconnect_attempts
            and settings.WEBSOCKET_AUTO_RECONNECT
            and self._enabled
        ):
            self._reconnect_attempts += 1
            delay = min(
                settings.WEBSOCKET_RECONNECT_DELAY
                * (
                    settings.WEBSOCKET_RECONNECT_BACKOFF_FACTOR
                    ** self._reconnect_attempts
                ),
                settings.WEBSOCKET_MAX_RECONNECT_DELAY,
            )

            logger.info(
                f"Attempting WebSocket reconnection in {delay}s "
                f"({self._reconnect_attempts}/{self._max_reconnect_attempts})"
            )

            await asyncio.sleep(delay)

            # Only reconnect if we should still be connected
            if self._should_reconnect:
                await self.connect()

    async def _handle_message(self, data: dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            event_type = data.get("type") or data.get("event")
            event_data = data.get("data", {})

            if settings.LOG_WEBSOCKET_MESSAGES:
                logger.debug(f"WebSocket message received: {data}")

            if not event_type:
                logger.warning(f"WebSocket message missing event type: {data}")
                return

            # Call event listeners
            listeners = self._listeners.get(event_type, [])
            if not listeners:
                logger.debug(f"No listeners for event type: {event_type}")
                return

            # Execute event handlers
            for callback in listeners:
                try:
                    # Handle both sync and async callbacks with timeout
                    if asyncio.iscoroutinefunction(callback):
                        await asyncio.wait_for(
                            callback(event_data), timeout=settings.EVENT_HANDLER_TIMEOUT
                        )
                    else:
                        # Run sync callback in thread pool to avoid blocking
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, callback, event_data)

                except asyncio.TimeoutError:
                    logger.error(
                        f"Event handler for '{event_type}' timed out after "
                        f"{settings.EVENT_HANDLER_TIMEOUT}s"
                    )
                except Exception as e:
                    logger.error(
                        f"Error in WebSocket event callback for {event_type}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected and self._websocket and not self._websocket.closed

    @property
    def is_enabled(self) -> bool:
        """Check if WebSocket is enabled in settings"""
        return self._enabled

    @property
    def connection_info(self) -> dict[str, Any]:
        """Get connection information"""
        return {
            "connected": self.is_connected,
            "enabled": self.is_enabled,
            "reconnect_attempts": self._reconnect_attempts,
            "max_reconnect_attempts": self._max_reconnect_attempts,
            "listeners_count": sum(
                len(handlers) for handlers in self._listeners.values()
            ),
            "event_types": list(self._listeners.keys()),
        }

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        listeners_count = sum(len(handlers) for handlers in self._listeners.values())
        return f"<WebSocketClient {status}, listeners: {listeners_count}>"
