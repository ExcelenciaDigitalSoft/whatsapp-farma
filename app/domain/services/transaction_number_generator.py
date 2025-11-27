"""Transaction number generation domain service."""
from datetime import date

from app.domain.interfaces.services import IDomainService


class TransactionNumberGenerator(IDomainService):
    """
    Domain service for generating unique transaction numbers.

    Generates sequential transaction numbers in the format:
    {PREFIX}-{YEAR}{MONTH}{DAY}-{SEQUENCE}

    Example: INV-20250118-0001
    """

    PREFIX_MAP = {
        "invoice": "INV",
        "payment": "PAY",
        "credit_note": "CN",
        "debit_note": "DN",
    }

    def generate(
        self,
        transaction_type: str,
        sequence: int,
        transaction_date: date | None = None
    ) -> str:
        """
        Generate a transaction number.

        Args:
            transaction_type: Type of transaction (invoice, payment, etc.)
            sequence: Sequential number for the day
            transaction_date: Transaction date (defaults to today)

        Returns:
            Formatted transaction number

        Raises:
            ValueError: If transaction type is invalid
        """
        if transaction_type not in self.PREFIX_MAP:
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        prefix = self.PREFIX_MAP[transaction_type]
        date_part = (transaction_date or date.today()).strftime("%Y%m%d")
        sequence_part = str(sequence).zfill(4)

        return f"{prefix}-{date_part}-{sequence_part}"

    def parse(self, transaction_number: str) -> dict:
        """
        Parse a transaction number into its components.

        Args:
            transaction_number: Transaction number to parse

        Returns:
            Dictionary with prefix, date, and sequence

        Raises:
            ValueError: If format is invalid
        """
        parts = transaction_number.split("-")

        if len(parts) != 3:
            raise ValueError(f"Invalid transaction number format: {transaction_number}")

        prefix, date_str, sequence_str = parts

        # Validate prefix
        if prefix not in self.PREFIX_MAP.values():
            raise ValueError(f"Invalid prefix: {prefix}")

        # Parse date
        try:
            transaction_date = date(
                int(date_str[0:4]),
                int(date_str[4:6]),
                int(date_str[6:8])
            )
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {date_str}")

        # Parse sequence
        try:
            sequence = int(sequence_str)
        except ValueError:
            raise ValueError(f"Invalid sequence: {sequence_str}")

        # Get transaction type
        transaction_type = next(
            (k for k, v in self.PREFIX_MAP.items() if v == prefix),
            None
        )

        return {
            "transaction_type": transaction_type,
            "date": transaction_date,
            "sequence": sequence,
            "prefix": prefix,
        }
