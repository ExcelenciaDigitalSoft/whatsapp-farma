"""Tax ID value object for DNI/CUIT/CUIL."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TaxId:
    """
    Tax ID value object for DNI, CUIT, or CUIL.

    Immutable value object that handles Argentinian tax identification numbers.

    Attributes:
        value: The tax ID number
        type: The type of tax ID (DNI, CUIT, CUIL)
    """

    value: str
    type: str

    def __post_init__(self):
        """Validate tax ID after initialization."""
        if not self.value:
            raise ValueError("Tax ID cannot be empty")

        if self.type not in ["DNI", "CUIT", "CUIL"]:
            raise ValueError(f"Invalid tax ID type: {self.type}")

        # Remove non-numeric characters for validation
        numeric = re.sub(r"\D", "", self.value)

        if self.type == "DNI":
            if not (7 <= len(numeric) <= 8):
                raise ValueError(f"Invalid DNI length: {self.value}")
        elif self.type in ["CUIT", "CUIL"]:
            if len(numeric) != 11:
                raise ValueError(f"Invalid {self.type} length: {self.value}")

    @classmethod
    def create(cls, value: str, type: str = "DNI") -> "TaxId":
        """
        Create a TaxId value object.

        Args:
            value: The tax ID number
            type: The type (DNI, CUIT, CUIL)

        Returns:
            TaxId value object
        """
        # Clean the value
        cleaned = value.strip()

        # Auto-detect type if not specified
        numeric = re.sub(r"\D", "", cleaned)

        if type == "DNI":
            # Keep as DNI
            pass
        elif len(numeric) == 11:
            # Likely CUIT/CUIL
            type = "CUIT"  # Default to CUIT
        elif 7 <= len(numeric) <= 8:
            type = "DNI"

        return cls(value=cleaned, type=type.upper())

    @classmethod
    def from_dni(cls, dni: str) -> "TaxId":
        """Create from DNI."""
        return cls.create(dni, "DNI")

    @classmethod
    def from_cuit(cls, cuit: str) -> "TaxId":
        """Create from CUIT."""
        return cls.create(cuit, "CUIT")

    @classmethod
    def from_cuil(cls, cuil: str) -> "TaxId":
        """Create from CUIL."""
        return cls.create(cuil, "CUIL")

    @property
    def numeric(self) -> str:
        """Get numeric-only representation."""
        return re.sub(r"\D", "", self.value)

    @property
    def formatted(self) -> str:
        """
        Get formatted representation.

        Returns:
            Formatted tax ID (XX-XXXXXXXX-X for CUIT/CUIL, XXXXXXXX for DNI)
        """
        numeric = self.numeric

        if self.type in ["CUIT", "CUIL"] and len(numeric) == 11:
            return f"{numeric[0:2]}-{numeric[2:10]}-{numeric[10]}"

        return numeric

    @property
    def is_dni(self) -> bool:
        """Check if this is a DNI."""
        return self.type == "DNI"

    @property
    def is_cuit(self) -> bool:
        """Check if this is a CUIT."""
        return self.type == "CUIT"

    @property
    def is_cuil(self) -> bool:
        """Check if this is a CUIL."""
        return self.type == "CUIL"

    def __str__(self) -> str:
        """String representation."""
        return self.formatted

    def __eq__(self, other: object) -> bool:
        """Compare by numeric value."""
        if not isinstance(other, TaxId):
            return False
        return self.numeric == other.numeric

    def __hash__(self) -> int:
        """Hash by numeric value."""
        return hash(self.numeric)
