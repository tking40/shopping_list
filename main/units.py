from enum import Enum
from dataclasses import dataclass
import copy


class CountUnit(Enum):
    """Enumeration for count-based units."""

    ITEM = 0


class VolumeUnit(Enum):
    """Enumeration for volume-based units."""

    CUP = 0
    TABLESPOON = 1
    TEASPOON = 2
    OUNCE = 3


class MassUnit(Enum):
    """Enumeration for mass-based units."""

    POUND = 0
    OUNCE = 1
    GRAM = 2
    MILLIGRAM = 3
    KILOGRAM = 4


# TODO: Add LITER to the volume table
VOLUME_TABLE = [
    [1, 16, 48, 8],
    [1 / 16, 1, 3, 1 / 2],
    [1 / 48, 1 / 3, 1, 1 / 6],
    [1 / 8, 2, 6, 1],
]

MASS_TABLE = [
    [1, 16, 453.592, 453592, 0.453592],
    [1 / 16, 1, 28.3495, 28349.5, 0.0283495],
    [1 / 453.592, 1 / 28.3495, 1, 1000, 0.001],
    [1 / 453592, 1 / 28349.5, 1 / 1000, 1, 0.000001],
    [2.20462, 35.274, 1000, 1000000, 1],
]


def convert_count(from_unit: CountUnit, to_unit: CountUnit, amount: float) -> float:
    """Convert between count units. Currently only supports ITEM to ITEM."""
    if from_unit == to_unit:
        return amount

    if from_unit == CountUnit.ITEM and to_unit == CountUnit.ITEM:
        return amount

    raise ValueError(
        f"Conversion between {from_unit} and {to_unit} is not supported yet"
    )


def convert_volume(from_unit: VolumeUnit, to_unit: VolumeUnit, amount: float) -> float:
    """Convert between volume units using the VOLUME_TABLE."""
    if from_unit == to_unit:
        return amount

    return amount * VOLUME_TABLE[from_unit.value][to_unit.value]


def convert_mass(from_unit: MassUnit, to_unit: MassUnit, amount: float) -> float:
    """Convert between mass units using the MASS_TABLE."""
    if from_unit == to_unit:
        return amount

    return amount * MASS_TABLE[from_unit.value][to_unit.value]


def convert_unit(
    from_unit: VolumeUnit | MassUnit | CountUnit,
    to_unit: VolumeUnit | MassUnit | CountUnit,
    amount: float,
) -> float:
    """Convert between compatible units of the same type (volume, mass, or count)."""
    if from_unit == to_unit:
        return amount

    if not isinstance(from_unit, type(to_unit)):
        raise ValueError(
            f"Cannot convert between {type(from_unit)} and {type(to_unit)}"
        )

    if isinstance(from_unit, VolumeUnit):
        return convert_volume(from_unit, to_unit, amount)
    elif isinstance(from_unit, MassUnit):
        return convert_mass(from_unit, to_unit, amount)
    elif isinstance(from_unit, CountUnit):
        return convert_count(from_unit, to_unit, amount)
    else:
        raise ValueError(f"Unsupported unit type: {type(from_unit)}")


@dataclass
class Quantity:
    """Represents a quantity with a unit and an amount."""

    unit: VolumeUnit | MassUnit | CountUnit
    amount: float

    @staticmethod
    def convert(from_quantity: "Quantity", to_quantity: "Quantity") -> "Quantity":
        """Convert from_quantity to the unit of to_quantity."""
        if type(from_quantity.unit) != type(to_quantity.unit):
            raise ValueError(
                f"Cannot convert {type(from_quantity.unit).__name__} to {type(to_quantity.unit).__name__}"
            )

        converted_amount = convert_unit(
            from_quantity.unit, to_quantity.unit, from_quantity.amount
        )

        return Quantity(to_quantity.unit, converted_amount)

    def __add__(self, other: "Quantity") -> "Quantity":
        """
        Add two quantities together. Result will have the same unit as the first quantity.
        """
        if type(self.unit) != type(other.unit):
            raise ValueError(
                f"Cannot add {type(self.unit).__name__} to {type(other.unit).__name__}"
            )
        converted_other = other
        if self.unit != other.unit:
            converted_other = self.convert(other, self)

        return Quantity(self.unit, self.amount + converted_other.amount)

    def __sub__(self, other: "Quantity") -> "Quantity":
        """
        Subtract one quantity from another. Result will have the same unit as the first quantity.
        """
        if type(self.unit) != type(other.unit):
            raise ValueError(
                f"Cannot subtract {type(other.unit).__name__} from {type(self.unit).__name__}"
            )
        converted_other = other
        if self.unit != other.unit:
            converted_other = self.convert(other, self)

        return Quantity(self.unit, self.amount - converted_other.amount)

    def __eq__(self, other: "Quantity") -> bool:
        """Check explicit equality between two quantities (same unit and amount)"""
        if type(self.unit) != type(other.unit):
            return False
        if self.unit == other.unit:
            return self.amount == other.amount

        return False

    def __str__(self) -> str:
        return f"{self.amount} {self.unit.name.lower()}"

    def to_dict(self) -> dict:
        return {"unit": self.unit.name.lower(), "amount": self.amount}

    @staticmethod
    def from_args(unit_str: str, amount: float) -> "Quantity":
        # Try to match the unit string to one of the Enums
        for enum_cls in (VolumeUnit, MassUnit, CountUnit):
            try:
                unit = enum_cls[unit_str.upper()]
                return Quantity(unit, amount)
            except KeyError:
                continue
        raise ValueError(f"Unknown unit: {unit_str}")

    @staticmethod
    def from_dict(d: dict) -> "Quantity":
        unit_str = d["unit"].upper()
        amount = d["amount"]
        return Quantity.from_args(unit_str, amount)

    def copy(self) -> "Quantity":
        """Return a copy of the quantity."""
        return Quantity(self.unit, self.amount)


if __name__ == "__main__":
    unit_1 = Quantity(VolumeUnit.CUP, 1)
    unit_2 = Quantity(VolumeUnit.TABLESPOON, 2)
    print(unit_1)
    print(unit_2)
    print(f"{unit_1} + {unit_2} = {unit_1 + unit_2}")
    print(f"{unit_2} + {unit_1} = {unit_2 + unit_1}")

    unit_3 = Quantity(MassUnit.POUND, 1)
    unit_4 = Quantity(MassUnit.KILOGRAM, 2)
    print(unit_3)
    print(unit_4)
    print(f"{unit_3} + {unit_4} = {unit_3 + unit_4}")
    print(f"{unit_4} + {unit_3} = {unit_4 + unit_3}")
