from typing import Any


class ServiceError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        return {"error": self.message, "status_code": self.status_code}


class APIError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class UserDataNotFoundError(Exception):
    """Raised when user not found in db"""

    def __init__(self, user_id=None, username=None, message=None):
        self.user_id = user_id
        self.username = username
        self.message = (
            message
            or f"User {f'@{username}' if username else ''} "
            f"{f'(ID: {user_id})' if user_id else ''} not found in database"
        )
        super().__init__(self.message)


class RequestError(Exception):
    def __init__(
        self,
        message: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        original_error: str | None = None,
    ):
        self.message = message
        self.endpoint = endpoint
        self.params = params
        self.original_error = original_error
        super().__init__(self.__str__())

    def __str__(self):
        error_details = (
            f"RequestError: {self.message}\n"
            f"Endpoint: {self.endpoint}\n"
            f"Params: {self.params}"
        )
        if self.original_error:
            error_details += f"\nOriginal Error: {self.original_error}"
        return error_details
