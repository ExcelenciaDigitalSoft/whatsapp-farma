"""Phone value object for phone number handling."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Phone:
    """
    Phone value object representing a phone number.

    Immutable value object that ensures phone number validity and provides
    normalization for WhatsApp integration.

    Attributes:
        value: The raw phone number
        normalized: The normalized phone number (E.164 format)
    """

    value: str
    normalized: str

    def __post_init__(self):
        """Validate phone number after initialization."""
        if not self.value:
            raise ValueError("Phone number cannot be empty")

        if not self.normalized:
            raise ValueError("Normalized phone number cannot be empty")

        # Validate format (basic validation)
        if not re.match(r"^\+?[\d\s\-\(\)]+$", self.value):
            raise ValueError(f"Invalid phone number format: {self.value}")

    @classmethod
    def create(cls, phone: str, country_code: str = "+54") -> "Phone":
        """
        Create a Phone value object with automatic normalization.

        Args:
            phone: The raw phone number
            country_code: Country code (default: +54 for Argentina)

        Returns:
            Phone value object

        Raises:
            ValueError: If phone number is invalid
        """
        if not phone:
            raise ValueError("Phone number cannot be empty")

        # Remove common separators
        cleaned = re.sub(r"[\s\-\(\)]", "", phone)

        # Normalize to E.164 format
        if cleaned.startswith("+"):
            normalized = cleaned
        elif cleaned.startswith("54") and len(cleaned) > 10:
            # Already has country code without +
            normalized = f"+{cleaned}"
        elif cleaned.startswith("9") and len(cleaned) == 10:
            # Mobile number without country code
            normalized = f"{country_code}9{cleaned[1:]}"
        elif cleaned.startswith("0"):
            # Remove leading 0
            normalized = f"{country_code}{cleaned[1:]}"
        else:
            # Assume local number
            normalized = f"{country_code}{cleaned}"

        return cls(value=phone, normalized=normalized)

    @classmethod
    def from_normalized(cls, normalized: str) -> "Phone":
        """
        Create a Phone from an already normalized number.

        Args:
            normalized: The normalized phone number

        Returns:
            Phone value object
        """
        return cls(value=normalized, normalized=normalized)

    @property
    def international_format(self) -> str:
        """Get phone number in international format (+54 9 11 1234 5678)."""
        if not self.normalized.startswith("+54"):
            return self.normalized

        # Format: +54 9 XX XXXX XXXX
        digits = self.normalized[3:]  # Remove +54
        if len(digits) >= 10:
            return f"+54 {digits[0]} {digits[1:3]} {digits[3:7]} {digits[7:]}"
        return self.normalized

    @property
    def local_format(self) -> str:
        """Get phone number in local format (11 1234 5678)."""
        if not self.normalized.startswith("+54"):
            return self.value

        digits = self.normalized[4:]  # Remove +549
        if len(digits) >= 10:
            return f"{digits[:2]} {digits[2:6]} {digits[6:]}"
        return self.value

    @property
    def whatsapp_format(self) -> str:
        """Get phone number in WhatsApp format (without + and spaces)."""
        return self.normalized.replace("+", "").replace(" ", "")

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare phones by normalized value."""
        if not isinstance(other, Phone):
            return False
        return self.normalized == other.normalized

    def __hash__(self) -> int:
        """Hash by normalized value."""
        return hash(self.normalized)
