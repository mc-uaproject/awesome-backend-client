# UAProject Python Library

A discord.py-inspired Python library for the UAProject API with support for real-time events, user impersonation, and intelligent caching.

## Features

- **Discord.py-like API** - Familiar patterns for Python developers
- **Real-time Events** - WebSocket integration with automatic reconnection
- **User Impersonation** - Perform actions as specific users with proper permission checking
- **Smart Caching** - Redis-powered caching with automatic invalidation
- **Type Safety** - Full integration with uaproject-backend-schemas
- **Error Handling** - Robust error handling with awesome-errors integration
- **Event-Driven** - Rich event system for real-time notifications

## Installation

1. Install with Poetry:
    ```bash
    poetry add git+https://github.com/mc-uaproject/uaproject-backend-pylibrary.git
    ```

2. Or clone for development:
    ```bash
    git clone https://github.com/mc-uaproject/uaproject-backend-pylibrary.git
    cd uaproject-backend-pylibrary
    poetry install
    ```

## Quick Start

```python
import asyncio
from uap_backend import UAProjectClient

async def main():
    # Create client
    client = UAProjectClient(enable_cache=True)
    
    # Event handlers (discord.py style)
    @client.event
    async def on_ready():
        print("Client ready!")
    
    @client.event
    async def on_user_create(user_data):
        print(f"New user: {user_data['minecraft_nickname']}")
    
    # Start client with WebSocket
    async with client:
        # Fetch user (discord.py style)
        user = await client.fetch_user(123)
        if user:
            print(f"User: {user.minecraft_nickname}")
            
            # User convenience methods
            balance = await user.get_balance()
            applications = await user.get_applications()
            
        # Search users
        users = await client.search_users("test", limit=5)
        
        # Wait for events
        new_user = await client.wait_for('user_create', timeout=30.0)

if __name__ == "__main__":
    asyncio.run(main())
```

## User Impersonation

One of the key features is the ability to impersonate users, allowing actions to be performed with their permissions:

```python
async with UAProjectClient() as bot_client:
    # Bot operations
    all_users = await bot_client.fetch_users(limit=100)
    
    # Impersonate a specific user
    user_client = bot_client.as_user(123)
    
    async with user_client:
        # Now all operations are performed as user 123
        # with their permissions and restrictions
        my_applications = await user_client.applications.get_many()
        
        # User can only see what they have access to
        try:
            restricted_data = await user_client.fetch_user(456)
        except PermissionError:
            print("User 123 cannot access user 456's data")
```

## Event System

Real-time event handling with WebSocket integration:

```python
client = UAProjectClient()

@client.event
async def on_user_create(user_data):
    user = User(UserSchema.model_validate(user_data), client=client)
    print(f"Welcome {user.minecraft_nickname}!")

@client.event  
async def on_application_create(app_data):
    print(f"New application: {app_data}")

@client.listen('transaction_create')
async def handle_transaction(tx_data):
    amount = tx_data.get('amount', 0)
    print(f"Transaction: {amount}")

# Wait for specific events
async with client:
    try:
        event_data = await client.wait_for('user_update', timeout=60.0)
        print(f"User updated: {event_data}")
    except asyncio.TimeoutError:
        print("No user updates in 60 seconds")
```

## Caching

Intelligent Redis-powered caching with automatic invalidation:

```python
client = UAProjectClient(enable_cache=True)

async with client:
    # First call hits the API
    user1 = await client.get_user(123)  # API call + cache
    
    # Second call uses cache
    user2 = await client.get_user(123)  # Cache hit
    
    # Force refresh from API
    user3 = await client.fetch_user(123)  # API call
    
    # CRUD operations automatically invalidate cache
    await client.users.update(123, {'minecraft_nickname': 'NewName'})
    # Cache for user 123 is now invalidated
```

## CRUD Operations

Direct access to all API resources:

```python
async with UAProjectClient() as client:
    # Users
    users = await client.users.get_many(
        filters={'is_active': True}, 
        limit=50
    )
    
    new_user = await client.users.create({
        'minecraft_nickname': 'TestUser',
        'discord_id': '123456789'
    })
    
    # Applications  
    applications = await client.applications.get_many(
        filters={'status': 'pending'}
    )
    
    # Services
    services = await client.services.get_many()
    
    # All CRUD services support:
    # - get(id) / get_many(filters=...)
    # - create(data) / update(id, data) / delete(id)
    # - Automatic caching and invalidation
    # - User impersonation
```

## Error Handling

Robust error handling with awesome-errors integration:

```python
from uap_backend import UAProjectClient, CRUDNotFoundError

async with UAProjectClient() as client:
    try:
        user = await client.fetch_user(999999)
    except CRUDNotFoundError:
        print("User not found")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Configuration

Environment variables and settings:

```python
# Use custom API endpoint
client = UAProjectClient(
    api_key="your-api-key",
    base_url="https://api.yourproject.com",
    enable_cache=True
)

# Or use environment variables:
# BACKEND_API_KEY=your-key
# FULL_API_URL=https://api.yourproject.com
client = UAProjectClient()
```

## Architecture

The library follows these principles:

- **No Code Duplication** - Reuses existing schemas and patterns from the backend
- **Type Safety** - Full integration with `uaproject-backend-schemas`
- **Performance** - Smart caching with Redis and connection pooling
- **Reliability** - Automatic reconnection and error handling
- **Compatibility** - Works alongside discord.py or as standalone library

## Examples

See the `examples/` directory for more comprehensive examples:

- `basic_usage.py` - Getting started guide
- `user_impersonation.py` - Advanced impersonation patterns
- `real_time_events.py` - Event handling examples
- `caching_strategies.py` - Caching best practices

## Development

To contribute:

1. Fork the repository
2. Install development dependencies: `poetry install`
3. Run tests: `poetry run pytest`
4. Follow the existing patterns and architecture
5. Submit a pull request

## Requirements

- Python 3.12+
- Redis (for caching)
- Access to UAProject backend API

## License

This project is part of the UAProject ecosystem.
