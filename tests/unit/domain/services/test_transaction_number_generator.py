"""Unit tests for TransactionNumberGenerator domain service."""
from datetime import date

import pytest  # type: ignore

from app.domain.services.transaction_number_generator import TransactionNumberGenerator


class TestTransactionNumberGeneration:
    """Test transaction number generation."""

    def test_generate_invoice_number(self):
        """Should generate invoice number with INV prefix."""
        generator = TransactionNumberGenerator()

        number = generator.generate("invoice", sequence=1, transaction_date=date(2024, 1, 15))

        assert number == "INV-20240115-0001"
        assert number.startswith("INV-")

    def test_generate_payment_number(self):
        """Should generate payment number with PAY prefix."""
        generator = TransactionNumberGenerator()

        number = generator.generate("payment", sequence=42, transaction_date=date(2024, 3, 20))

        assert number == "PAY-20240320-0042"
        assert number.startswith("PAY-")

    def test_generate_credit_note_number(self):
        """Should generate credit note number with CN prefix."""
        generator = TransactionNumberGenerator()

        number = generator.generate("credit_note", sequence=7, transaction_date=date(2024, 5, 10))

        assert number == "CN-20240510-0007"
        assert number.startswith("CN-")

    def test_generate_debit_note_number(self):
        """Should generate debit note number with DN prefix."""
        generator = TransactionNumberGenerator()

        number = generator.generate("debit_note", sequence=15, transaction_date=date(2024, 7, 25))

        assert number == "DN-20240725-0015"
        assert number.startswith("DN-")

    def test_generate_with_high_sequence_number(self):
        """Should pad sequence number to 4 digits."""
        generator = TransactionNumberGenerator()

        number = generator.generate("invoice", sequence=9999)

        assert "9999" in number

    def test_generate_with_sequence_over_9999(self):
        """Should handle sequence numbers over 9999."""
        generator = TransactionNumberGenerator()

        number = generator.generate("invoice", sequence=10000)

        assert "10000" in number  # More than 4 digits

    def test_generate_uses_today_when_no_date_provided(self):
        """Should use today's date when no date provided."""
        generator = TransactionNumberGenerator()
        today = date.today()

        number = generator.generate("invoice", sequence=1)

        expected_date = today.strftime("%Y%m%d")
        assert expected_date in number

    def test_generate_with_invalid_type_raises_error(self):
        """Should raise KeyError for invalid transaction type."""
        generator = TransactionNumberGenerator()

        with pytest.raises(KeyError):
            generator.generate("invalid_type", sequence=1)

    def test_sequence_padding_with_various_lengths(self):
        """Should correctly pad sequences of various lengths."""
        generator = TransactionNumberGenerator()
        test_date = date(2024, 1, 1)

        # 1 digit → 4 digits
        num1 = generator.generate("invoice", sequence=1, transaction_date=test_date)
        assert num1.endswith("-0001")

        # 2 digits → 4 digits
        num2 = generator.generate("invoice", sequence=42, transaction_date=test_date)
        assert num2.endswith("-0042")

        # 3 digits → 4 digits
        num3 = generator.generate("invoice", sequence=123, transaction_date=test_date)
        assert num3.endswith("-0123")

        # 4 digits → 4 digits
        num4 = generator.generate("invoice", sequence=9999, transaction_date=test_date)
        assert num4.endswith("-9999")

    def test_date_formatting(self):
        """Should format date as YYYYMMDD."""
        generator = TransactionNumberGenerator()

        number = generator.generate("invoice", sequence=1, transaction_date=date(2024, 12, 31))

        assert "20241231" in number

    def test_full_format_structure(self):
        """Should follow PREFIX-YYYYMMDD-NNNN format."""
        generator = TransactionNumberGenerator()

        number = generator.generate("invoice", sequence=42, transaction_date=date(2024, 6, 15))

        parts = number.split("-")
        assert len(parts) == 3
        assert parts[0] == "INV"
        assert parts[1] == "20240615"
        assert parts[2] == "0042"


class TestTransactionNumberUniqueness:
    """Test transaction number uniqueness characteristics."""

    def test_different_types_same_sequence_different_numbers(self):
        """Different transaction types should produce different numbers."""
        generator = TransactionNumberGenerator()
        test_date = date(2024, 1, 1)

        invoice_num = generator.generate("invoice", sequence=1, transaction_date=test_date)
        payment_num = generator.generate("payment", sequence=1, transaction_date=test_date)

        assert invoice_num != payment_num
        assert invoice_num.startswith("INV-")
        assert payment_num.startswith("PAY-")

    def test_same_type_different_sequences_different_numbers(self):
        """Same type with different sequences should be different."""
        generator = TransactionNumberGenerator()
        test_date = date(2024, 1, 1)

        num1 = generator.generate("invoice", sequence=1, transaction_date=test_date)
        num2 = generator.generate("invoice", sequence=2, transaction_date=test_date)

        assert num1 != num2

    def test_same_type_same_sequence_different_dates_different_numbers(self):
        """Same type and sequence but different dates should be different."""
        generator = TransactionNumberGenerator()

        num1 = generator.generate("invoice", sequence=1, transaction_date=date(2024, 1, 1))
        num2 = generator.generate("invoice", sequence=1, transaction_date=date(2024, 1, 2))

        assert num1 != num2
        assert "20240101" in num1
        assert "20240102" in num2
