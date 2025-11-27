"""Transaction repository interface."""
from abc import abstractmethod
from uuid import UUID
from datetime import date

from .base import IRepository
from app.domain.entities import Transaction
from app.domain.value_objects import Money


class ITransactionRepository(IRepository[Transaction, Transaction, Transaction]):
    """
    Transaction repository interface.

    Extends the base repository with transaction-specific query methods.
    """

    @abstractmethod
    async def find_by_transaction_number(
        self,
        transaction_number: str
    ) -> Transaction | None:
        """
        Find a transaction by its unique number.

        Args:
            transaction_number: Transaction number

        Returns:
            Transaction if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_client(
        self,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find all transactions for a client.

        Args:
            client_id: Client ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of transactions
        """
        pass

    @abstractmethod
    async def find_by_pharmacy(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find all transactions for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of transactions
        """
        pass

    @abstractmethod
    async def find_pending_payments(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find pending payment transactions.

        Args:
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of pending transactions
        """
        pass

    @abstractmethod
    async def find_overdue(
        self,
        pharmacy_id: UUID,
        as_of_date: date | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find overdue transactions.

        Args:
            pharmacy_id: Pharmacy ID
            as_of_date: Date to check (defaults to today)
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of overdue transactions
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        pharmacy_id: UUID,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find transactions within a date range.

        Args:
            pharmacy_id: Pharmacy ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of transactions
        """
        pass

    @abstractmethod
    async def find_by_type(
        self,
        transaction_type: str,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Transaction]:
        """
        Find transactions by type.

        Args:
            transaction_type: Transaction type (invoice, payment, etc.)
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of transactions
        """
        pass

    @abstractmethod
    async def get_total_by_client(
        self,
        client_id: UUID,
        transaction_type: str | None = None
    ) -> Money:
        """
        Get total transaction amount for a client.

        Args:
            client_id: Client ID
            transaction_type: Optional filter by type

        Returns:
            Total amount
        """
        pass

    @abstractmethod
    async def get_next_sequence_number(
        self,
        pharmacy_id: UUID,
        transaction_type: str,
        transaction_date: date
    ) -> int:
        """
        Get next sequence number for transaction numbering.

        Args:
            pharmacy_id: Pharmacy ID
            transaction_type: Transaction type
            transaction_date: Transaction date

        Returns:
            Next sequence number
        """
        pass

    @abstractmethod
    async def count_by_pharmacy(
        self,
        pharmacy_id: UUID,
        transaction_type: str | None = None
    ) -> int:
        """
        Count transactions for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID
            transaction_type: Optional filter by type

        Returns:
            Number of transactions
        """
        pass
