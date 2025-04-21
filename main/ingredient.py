import pandas as pd
from dataclasses import dataclass
from units import Quantity, VolumeUnit


@dataclass
class Ingredient:
    name: str
    quantity: Quantity

    def __str__(self) -> str:
        return f"{self.quantity} {self.name}"

    def __add__(self, other: "Ingredient") -> "Ingredient":
        """Add two ingredients by combining their quantities"""
        assert (
            self.name == other.name
        ), f"Cannot add ingredients with different names: {self.name} and {other.name}"

        return Ingredient(self.name, self.quantity + other.quantity)

    def to_dict(self, flatten: bool = False) -> dict:
        """Convert the ingredient to a dictionary. Cannot recover with from_dict if flatten is True."""
        if flatten:
            out_dict = {"name": self.name}
            out_dict.update(self.quantity.to_dict())
            return out_dict
        else:
            return {"name": self.name, "quantity": self.quantity.to_dict()}

    @staticmethod
    def from_dict(d: dict) -> "Ingredient":
        quantity = Quantity.from_dict(d["quantity"])
        return Ingredient(name=d["name"], quantity=quantity)

    def to_series(self) -> pd.Series:
        """Convert the ingredient to a pandas Series."""
        return pd.Series(self.to_dict(flatten=True))


if __name__ == "__main__":
    i1 = Ingredient("broth", Quantity(VolumeUnit.CUP, 1))
    i2 = Ingredient("broth", Quantity(VolumeUnit.TABLESPOON, 2))
    print(i1 + i2)
    print(i1.to_dict(True))
    print(i1.to_series())
