"""Email value object."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Email value object representing an email address.

    Immutable value object that ensures email validity.

    Attributes:
        value: The email address
    """

    value: str

    def __post_init__(self):
        """Validate email after initialization."""
        if not self.value:
            raise ValueError("Email cannot be empty")

        # Basic email validation regex
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    @classmethod
    def create(cls, email: str) -> "Email":
        """
        Create an Email value object.

        Args:
            email: The email address

        Returns:
            Email value object

        Raises:
            ValueError: If email is invalid
        """
        return cls(value=email.strip().lower())

    @property
    def domain(self) -> str:
        """Get the email domain."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get the local part (before @)."""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)
