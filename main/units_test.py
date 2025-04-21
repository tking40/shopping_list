import unittest
from unit import (
    CountUnit,
    VolumeUnit,
    MassUnit,
    convert_count,
    convert_volume,
    convert_mass,
    convert_unit,
    Quantity,
)


class TestUnitConversions(unittest.TestCase):
    def test_convert_count(self):
        self.assertEqual(convert_count(CountUnit.ITEM, CountUnit.ITEM, 5), 5)
        with self.assertRaises(ValueError):
            convert_count(CountUnit.ITEM, None, 1)

    def test_convert_volume(self):
        # 1 cup = 16 tbsp
        self.assertAlmostEqual(
            convert_volume(VolumeUnit.CUP, VolumeUnit.TABLESPOON, 1), 16
        )
        # 2 tbsp = 0.125 cup
        self.assertAlmostEqual(
            convert_volume(VolumeUnit.TABLESPOON, VolumeUnit.CUP, 2), 0.125
        )
        # 1 tsp = 1/48 cup
        self.assertAlmostEqual(
            convert_volume(VolumeUnit.TEASPOON, VolumeUnit.CUP, 1), 1 / 48
        )
        # 1 oz = 2 tbsp
        self.assertAlmostEqual(
            convert_volume(VolumeUnit.OUNCE, VolumeUnit.TABLESPOON, 1), 2
        )

    def test_convert_mass(self):
        # 1 pound = 16 ounces
        self.assertAlmostEqual(convert_mass(MassUnit.POUND, MassUnit.OUNCE, 1), 16)
        # 1 kilogram = 2.20462 pounds
        self.assertAlmostEqual(
            convert_mass(MassUnit.KILOGRAM, MassUnit.POUND, 1), 2.20462, places=5
        )
        # 1000 mg = 1 g
        self.assertAlmostEqual(convert_mass(MassUnit.MILLIGRAM, MassUnit.GRAM, 1000), 1)
        # 1 ounce = 28.3495 grams
        self.assertAlmostEqual(
            convert_mass(MassUnit.OUNCE, MassUnit.GRAM, 1), 28.3495, places=4
        )

    def test_convert_unit(self):
        # Volume
        self.assertAlmostEqual(
            convert_unit(VolumeUnit.CUP, VolumeUnit.TABLESPOON, 1), 16
        )
        # Mass
        self.assertAlmostEqual(convert_unit(MassUnit.POUND, MassUnit.OUNCE, 1), 16)
        # Count
        self.assertEqual(convert_unit(CountUnit.ITEM, CountUnit.ITEM, 3), 3)
        # Error on mismatched types
        with self.assertRaises(ValueError):
            convert_unit(VolumeUnit.CUP, MassUnit.POUND, 1)


class TestQuantity(unittest.TestCase):
    def test_quantity_add_same_unit(self):
        q1 = Quantity(VolumeUnit.CUP, 1)
        q2 = Quantity(VolumeUnit.CUP, 2)
        result = q1 + q2
        self.assertEqual(result.amount, 3)
        self.assertEqual(result.unit, VolumeUnit.CUP)

    def test_quantity_add_different_unit(self):
        q1 = Quantity(VolumeUnit.CUP, 1)
        q2 = Quantity(VolumeUnit.TABLESPOON, 2)
        result = q1 + q2
        # 2 tbsp = 0.125 cup, so 1 + 0.125 = 1.125
        self.assertAlmostEqual(result.amount, 1.125)
        self.assertEqual(result.unit, VolumeUnit.CUP)

    def test_quantity_add_error(self):
        q1 = Quantity(VolumeUnit.CUP, 1)
        q2 = Quantity(MassUnit.POUND, 1)
        with self.assertRaises(ValueError):
            _ = q1 + q2

    def test_quantity_convert(self):
        q1 = Quantity(MassUnit.POUND, 2)
        q2 = Quantity(MassUnit.KILOGRAM, 0)  # target unit
        result = Quantity.convert(q1, q2)
        # 2 pounds = 0.907184 kg
        self.assertAlmostEqual(result.amount, 0.907184, places=5)
        self.assertEqual(result.unit, MassUnit.KILOGRAM)

    def test_quantity_str(self):
        q = Quantity(VolumeUnit.CUP, 1.5)
        self.assertEqual(str(q), "1.5 cup")

    def test_quantity_eq(self):
        # same unit and amount
        q1 = Quantity(VolumeUnit.CUP, 1)
        q2 = Quantity(VolumeUnit.CUP, 1)
        self.assertTrue(q1 == q2)
        # same unit, different amount
        q3 = Quantity(VolumeUnit.CUP, 2)
        self.assertFalse(q1 == q3)
        # different unit type
        q4 = Quantity(MassUnit.POUND, 1)
        self.assertFalse(q1 == q4)
        # different unit
        q5 = Quantity(VolumeUnit.TABLESPOON, 1)
        self.assertFalse(q1 == q5)
        # different unit and amount
        q6 = Quantity(VolumeUnit.TABLESPOON, 2)
        self.assertFalse(q1 == q6)


if __name__ == "__main__":
    unittest.main()
