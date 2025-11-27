"""Address value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """
    Address value object representing a physical address.

    Immutable value object for address information.

    Attributes:
        street: Street address
        city: City name
        state: State/province
        postal_code: Postal/ZIP code
        country: Country code (ISO 3166-1 alpha-2)
    """

    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "AR"

    def __post_init__(self):
        """Validate address after initialization."""
        if self.country and len(self.country) != 2:
            raise ValueError(f"Invalid country code: {self.country}")

    @classmethod
    def create(
        cls,
        street: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        country: str = "AR",
    ) -> "Address":
        """
        Create an Address value object.

        Args:
            street: Street address
            city: City name
            state: State/province
            postal_code: Postal code
            country: Country code (default: AR)

        Returns:
            Address value object
        """
        return cls(
            street=street.strip() if street else None,
            city=city.strip() if city else None,
            state=state.strip() if state else None,
            postal_code=postal_code.strip() if postal_code else None,
            country=country.upper(),
        )

    @classmethod
    def empty(cls) -> "Address":
        """Create an empty address."""
        return cls()

    def is_complete(self) -> bool:
        """Check if address has all required fields."""
        return all([self.street, self.city, self.state, self.postal_code])

    def is_empty(self) -> bool:
        """Check if address is empty."""
        return not any([self.street, self.city, self.state, self.postal_code])

    def formatted(self, single_line: bool = False) -> str:
        """
        Get formatted address string.

        Args:
            single_line: Format as single line (default: False)

        Returns:
            Formatted address string
        """
        parts = []

        if self.street:
            parts.append(self.street)

        if self.city and self.state:
            parts.append(f"{self.city}, {self.state}")
        elif self.city:
            parts.append(self.city)
        elif self.state:
            parts.append(self.state)

        if self.postal_code:
            parts.append(self.postal_code)

        if not parts:
            return ""

        separator = ", " if single_line else "\n"
        return separator.join(parts)

    def __str__(self) -> str:
        """String representation."""
        return self.formatted(single_line=True)

    def __bool__(self) -> bool:
        """Boolean evaluation."""
        return not self.is_empty()
