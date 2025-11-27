"""Client validation domain service."""
from decimal import Decimal
import re

from app.domain.interfaces.services import IDomainService
from app.domain.entities import Client
from app.domain.value_objects import Money, Phone, Email
from app.domain.exceptions import ValidationError, BusinessRuleViolation


class ClientValidator(IDomainService):
    """
    Domain service for client validation and business rules.

    Encapsulates client-related business logic that doesn't naturally
    fit within the Client entity itself.
    """

    def validate_for_transaction(
        self,
        client: Client,
        transaction_amount: Money
    ) -> None:
        """
        Validate if client can proceed with a transaction.

        Args:
            client: The client
            transaction_amount: Transaction amount

        Raises:
            ValidationError: If client is not valid for transaction
            BusinessRuleViolation: If business rules prevent transaction
        """
        # Client must be active
        if client.status != "active":
            raise ValidationError(
                f"Client is {client.status}. Only active clients can make transactions."
            )

        # Client must not be deleted
        if client.is_deleted():
            raise ValidationError("Cannot transact with deleted client")

        # Check if WhatsApp is required and client has opted out
        if not client.whatsapp_opted_in:
            # This might be a warning rather than an error depending on business rules
            pass

        # Validate purchase amount
        if not client.can_make_purchase(transaction_amount):
            available = client.balance.available_credit
            raise BusinessRuleViolation(
                f"Transaction of {transaction_amount} would exceed available credit. "
                f"Available: {available}"
            )

    def calculate_credit_score(self, client: Client) -> float:
        """
        Calculate a simple credit score for the client.

        Args:
            client: The client

        Returns:
            Credit score (0.0 - 1.0)
        """
        score = 1.0

        # Penalize if in debt
        if client.owes_money:
            debt_ratio = client.balance.total_debt.amount / max(client.balance.credit_limit.amount, Decimal("1"))
            score -= float(min(debt_ratio * Decimal("0.5"), Decimal("0.5")))  # Max 50% penalty

        # Penalize if credit exceeded
        if client.credit_exceeded:
            score -= 0.3

        # Penalize if blocked
        if client.status == "blocked":
            score = 0.0

        # Penalize if inactive
        if client.status == "inactive":
            score *= 0.5

        return max(0.0, min(1.0, score))

    def recommend_credit_limit(self, client: Client, purchase_history_total: Money) -> Money:
        """
        Recommend a credit limit based on purchase history.

        Args:
            client: The client
            purchase_history_total: Total purchase amount in history

        Returns:
            Recommended credit limit
        """
        # Simple recommendation: 30% of total historical purchases
        # Minimum: current balance if in debt
        # Maximum: 10x current limit

        recommended = purchase_history_total * Decimal("0.3")

        # Ensure minimum
        if client.owes_money:
            minimum = client.balance.total_debt
            if recommended < minimum:
                recommended = minimum

        # Ensure maximum
        if client.balance.credit_limit.amount > 0:
            maximum = client.balance.credit_limit * Decimal("10")
            if recommended > maximum:
                recommended = maximum

        return recommended

    def should_send_credit_warning(self, client: Client) -> bool:
        """
        Determine if a credit warning should be sent to the client.

        Args:
            client: The client

        Returns:
            True if warning should be sent
        """
        # Send warning if at 90% of credit limit or exceeded
        return client.balance.is_at_credit_limit or client.credit_exceeded

    def validate_for_credit_increase(
        self,
        client: Client,
        new_limit: Money
    ) -> None:
        """
        Validate if credit limit can be increased.

        Args:
            client: The client
            new_limit: Proposed new credit limit

        Raises:
            ValidationError: If increase is not allowed
        """
        if new_limit.is_negative():
            raise ValidationError("Credit limit cannot be negative")

        if new_limit.currency != client.balance.credit_limit.currency:
            raise ValidationError("Currency mismatch")

        # Business rule: Cannot decrease limit if client is in debt
        if new_limit < client.balance.credit_limit and client.owes_money:
            raise BusinessRuleViolation(
                "Cannot decrease credit limit while client has outstanding debt"
            )

        # Business rule: Client must be active
        if client.status != "active":
            raise BusinessRuleViolation(
                f"Cannot modify credit limit for {client.status} client"
            )

    def validate_phone(self, phone: str) -> None:
        """
        Validate phone number format.

        Args:
            phone: Phone number string to validate

        Raises:
            ValidationError: If phone format is invalid
        """
        try:
            Phone.create(phone)
        except (ValidationError, ValueError) as e:
            raise ValidationError(f"Invalid phone format: {str(e)}")

    def validate_email(self, email: str) -> None:
        """
        Validate email format.

        Args:
            email: Email string to validate

        Raises:
            ValidationError: If email format is invalid
        """
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")

    def validate_credit_limit(self, limit: Decimal) -> None:
        """
        Validate credit limit value.

        Args:
            limit: Credit limit to validate

        Raises:
            ValidationError: If credit limit is invalid
        """
        if limit < 0:
            raise ValidationError("Credit limit cannot be negative")

    def validate_status(self, status: str) -> None:
        """
        Validate client status.

        Args:
            status: Client status to validate

        Raises:
            ValidationError: If status is invalid
        """
        valid_statuses = ["active", "inactive", "blocked", "suspended"]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid client status: {status}")
