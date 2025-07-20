"""Discord integration helpers for awesome-backend-client"""

from collections.abc import Awaitable
import functools
from typing import Any, Callable, ParamSpec, TypeVar

from awesome_backend_client.client import UAProjectClient
from awesome_backend_client.core.config import settings

try:
    from disnake import ApplicationCommandInteraction
    from disnake.ext.commands import Context

    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False  # pyright: ignore[reportConstantRedefinition]
    # Create dummy types for type hints
    ApplicationCommandInteraction = Any
    Context = Any

P = ParamSpec("P")
T = TypeVar("T")


if DISCORD_AVAILABLE:

    class EnhancedInteraction(ApplicationCommandInteraction):
        """Interaction with UAP attributes"""

        uap_user: Any  # UserSchemaResponse or None
        uap_client: UAProjectClient

    class EnhancedContext(Context):
        """Context with UAP attributes"""

        uap_user: Any  # UserSchemaResponse or None
        uap_client: UAProjectClient
else:
    # Dummy classes when Discord is not available
    class EnhancedInteraction:
        uap_user: Any
        uap_client: UAProjectClient

    class EnhancedContext:
        uap_user: Any
        uap_client: UAProjectClient


class DiscordIntegration:
    """Discord integration for UAProject client"""

    def __init__(self, base_client: UAProjectClient):
        self.base_client = base_client

    async def _enhance_discord_object(
        self, obj, fallback_to_base: bool, fetch_user: bool
    ):
        """Common logic for enhancing interaction/context with UAP attributes"""
        if fetch_user:
            discord_id = obj.author.id
            try:
                user_data = await self.base_client.users.get_by_discord_id(
                    discord_id, _raise=False
                )

                if user_data:
                    user_client = UAProjectClient.with_impersonation(
                        user_id=user_data.id
                    )
                    obj.uap_user = user_data
                    obj.uap_client = user_client
                elif fallback_to_base:
                    obj.uap_user = None
                    obj.uap_client = self.base_client
                else:
                    raise ValueError(f"User not found for Discord ID {discord_id}")

            except Exception as e:
                if fallback_to_base:
                    obj.uap_user = None
                    obj.uap_client = self.base_client
                else:
                    raise e
        else:
            # Skip user fetch, just add base client
            obj.uap_user = None
            obj.uap_client = self.base_client

    def with_user_from_interaction(
        self,
        fallback_to_base: bool = True,
        fetch_user: bool = True,
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """
        Decorator that injects uap_user and uap_client into interaction

        Args:
            fallback_to_base: If True, use base client when user not found
            fetch_user: If False, skip user fetch and set uap_user to None
        """
        if not DISCORD_AVAILABLE:
            raise ImportError("disnake is required for Discord integration")

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                new_args = []
                interaction = None

                for arg in args:
                    if isinstance(arg, ApplicationCommandInteraction):
                        interaction = arg
                        await self._enhance_discord_object(
                            interaction, fallback_to_base, fetch_user
                        )
                        new_args.append(interaction)
                    else:
                        new_args.append(arg)

                if not interaction:
                    raise ValueError(
                        "No ApplicationCommandInteraction found in arguments"
                    )

                return await func(*new_args, **kwargs)

            return wrapper

        return decorator

    def with_user_from_context(
        self,
        fallback_to_base: bool = True,
        fetch_user: bool = True,
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """
        Decorator that injects uap_user and uap_client into context

        Args:
            fallback_to_base: If True, use base client when user not found
            fetch_user: If False, skip user fetch and set uap_user to None
        """
        if not DISCORD_AVAILABLE:
            raise ImportError("disnake is required for Discord integration")

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                new_args = []
                ctx = None

                for arg in args:
                    if isinstance(arg, Context):
                        ctx = arg
                        await self._enhance_discord_object(
                            ctx, fallback_to_base, fetch_user
                        )
                        new_args.append(ctx)
                    else:
                        new_args.append(arg)

                if not ctx:
                    raise ValueError("No Context found in arguments")

                return await func(*new_args, **kwargs)

            return wrapper

        return decorator


def with_uap_user(fallback_to_base: bool = True, fetch_user: bool = True):
    """Short decorator for interaction commands with UAP user"""
    base_client = UAProjectClient(api_key=settings.BACKEND_API_KEY)
    integration = DiscordIntegration(base_client)
    return integration.with_user_from_interaction(fallback_to_base, fetch_user)


def with_uap_ctx(fallback_to_base: bool = True, fetch_user: bool = True):
    """Short decorator for context commands with UAP user"""
    base_client = UAProjectClient(api_key=settings.BACKEND_API_KEY)
    integration = DiscordIntegration(base_client)
    return integration.with_user_from_context(fallback_to_base, fetch_user)
