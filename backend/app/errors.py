"""Domain errors shared by validation, services, and the HTTP layer."""


class DomainError(Exception):
    """A business-rule failure the caller can correct or report."""

    def __init__(self, code: str, message: str, fields: dict[str, str] | None = None) -> None:
        self.code = code
        self.message = message
        self.fields = fields or {}
        super().__init__(message)
