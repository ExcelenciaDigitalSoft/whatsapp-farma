"""Domain exceptions."""


class DomainException(Exception):
    """Base exception for domain-related errors."""

    pass


class ValidationError(DomainException):
    """Raised when domain validation fails."""

    pass


class BusinessRuleViolation(DomainException):
    """Raised when a business rule is violated."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class DuplicateEntityError(DomainException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field}='{value}' already exists")


class CreditLimitExceededError(BusinessRuleViolation):
    """Raised when a transaction would exceed client credit limit."""

    pass


class InsufficientFundsError(BusinessRuleViolation):
    """Raised when there are insufficient funds for an operation."""

    pass


class InvalidStateTransitionError(BusinessRuleViolation):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Cannot transition from '{from_state}' to '{to_state}'")


class ServiceUnavailableError(DomainException):
    """Raised when an external service is unavailable."""

    pass


class ExternalServiceError(DomainException):
    """Raised when an external integration returns an error response."""

    pass


class PaymentGatewayError(DomainException):
    """Raised when payment gateway operations fail."""

    pass


class DocumentGenerationError(DomainException):
    """Raised when document generation fails."""

    pass


__all__ = [
    "DomainException",
    "ValidationError",
    "BusinessRuleViolation",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "CreditLimitExceededError",
    "InsufficientFundsError",
    "InvalidStateTransitionError",
    "ServiceUnavailableError",
    "ExternalServiceError",
    "PaymentGatewayError",
    "DocumentGenerationError",
]
