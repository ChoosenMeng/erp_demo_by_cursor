from typing import Any


class AppError(Exception):
    """Business / application error with API-friendly fields."""

    def __init__(
        self,
        message: str,
        *,
        code: int = 40000,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在", *, details: Any = None) -> None:
        super().__init__(message, code=40400, status_code=404, details=details)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "未认证", *, details: Any = None) -> None:
        super().__init__(message, code=40100, status_code=401, details=details)


class ForbiddenError(AppError):
    def __init__(self, message: str = "无权限", *, details: Any = None) -> None:
        super().__init__(message, code=40300, status_code=403, details=details)
