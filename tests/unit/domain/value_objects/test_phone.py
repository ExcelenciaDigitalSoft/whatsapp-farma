"""Unit tests for Phone value object."""
import pytest  # type: ignore

from app.domain.value_objects.phone import Phone
from app.domain.exceptions import ValidationError


class TestPhoneCreation:
    """Test phone number creation and normalization."""

    def test_create_with_full_international_format(self):
        """Should create phone with full international format."""
        phone = Phone.create("+54 9 11 1234 5678")

        assert phone.value == "+54 9 11 1234 5678"
        assert phone.normalized == "+5491112345678"

    def test_create_with_country_code_without_plus(self):
        """Should add plus sign if missing."""
        phone = Phone.create("54 9 11 1234 5678")

        assert phone.normalized == "+5491112345678"

    def test_create_with_local_format(self):
        """Should add country code for local numbers."""
        phone = Phone.create("11 1234 5678", country_code="+54")

        assert phone.normalized.startswith("+54")

    def test_create_removes_formatting_characters(self):
        """Should remove spaces, dashes, and parentheses."""
        phone = Phone.create("+54 (9-11) 1234-5678")

        assert phone.normalized == "+5491112345678"
        assert " " not in phone.normalized
        assert "-" not in phone.normalized
        assert "(" not in phone.normalized

    def test_create_with_empty_string_raises_error(self):
        """Should raise ValidationError for empty string."""
        with pytest.raises(ValidationError, match="Phone number cannot be empty"):
            Phone.create("")

    def test_create_with_invalid_characters_raises_error(self):
        """Should raise ValidationError for invalid characters."""
        with pytest.raises(ValidationError, match="Invalid phone number format"):
            Phone.create("+54 abc 1234")

    def test_create_with_too_short_number_raises_error(self):
        """Should raise ValidationError for numbers too short."""
        with pytest.raises(ValidationError, match="Phone number too short"):
            Phone.create("+54 123")


class TestPhoneEquality:
    """Test phone equality and comparison."""

    def test_phones_with_same_normalized_are_equal(self):
        """Two phones with same normalized value should be equal."""
        phone1 = Phone.create("+54 9 11 1234 5678")
        phone2 = Phone.create("54-9-11-1234-5678")

        assert phone1 == phone2

    def test_phones_with_different_normalized_are_not_equal(self):
        """Two phones with different normalized values should not be equal."""
        phone1 = Phone.create("+54 9 11 1234 5678")
        phone2 = Phone.create("+54 9 11 8765 4321")

        assert phone1 != phone2

    def test_phone_hash_consistency(self):
        """Phone objects should be hashable and consistent."""
        phone1 = Phone.create("+54 9 11 1234 5678")
        phone2 = Phone.create("54-9-11-1234-5678")

        # Can be used in sets and dicts
        phone_set = {phone1, phone2}
        assert len(phone_set) == 1  # Same normalized value


class TestPhoneImmutability:
    """Test phone immutability."""

    def test_phone_is_frozen(self):
        """Should not allow modification after creation."""
        phone = Phone.create("+54 9 11 1234 5678")

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            phone.value = "new value"  # type: ignore

    def test_phone_fields_are_read_only(self):
        """Should not allow field reassignment."""
        phone = Phone.create("+54 9 11 1234 5678")

        with pytest.raises(Exception):
            phone.normalized = "+1234567890"  # type: ignore


class TestPhoneStringRepresentation:
    """Test string representation."""

    def test_str_returns_original_value(self):
        """Should return original formatted value."""
        original = "+54 9 11 1234 5678"
        phone = Phone.create(original)

        assert str(phone) == original

    def test_repr_shows_both_values(self):
        """Should show both original and normalized in repr."""
        phone = Phone.create("+54 9 11 1234 5678")
        repr_str = repr(phone)

        assert "Phone" in repr_str
        assert phone.value in repr_str or phone.normalized in repr_str


class TestPhoneFromNormalized:
    """Test creating phone from normalized format."""

    def test_from_normalized_creates_valid_phone(self):
        """Should create phone from normalized E.164 format."""
        normalized = "+5491112345678"
        phone = Phone.from_normalized(normalized)

        assert phone.normalized == normalized
        assert phone.value == normalized

    def test_from_normalized_validates_format(self):
        """Should validate E.164 format."""
        with pytest.raises(ValidationError, match="must start with"):
            Phone.from_normalized("5491112345678")  # Missing +


class TestPhoneEdgeCases:
    """Test edge cases and special scenarios."""

    def test_whitespace_only_raises_error(self):
        """Should raise error for whitespace-only input."""
        with pytest.raises(ValidationError):
            Phone.create("   ")

    def test_special_characters_in_middle_are_removed(self):
        """Should handle special characters in middle of number."""
        phone = Phone.create("+54.9.11.1234.5678")

        assert "." not in phone.normalized

    def test_different_country_codes(self):
        """Should handle different country codes."""
        # USA
        phone_us = Phone.create("+1 555 123 4567")
        assert phone_us.normalized.startswith("+1")

        # Mexico
        phone_mx = Phone.create("+52 55 1234 5678")
        assert phone_mx.normalized.startswith("+52")

        # Spain
        phone_es = Phone.create("+34 91 123 4567")
        assert phone_es.normalized.startswith("+34")
