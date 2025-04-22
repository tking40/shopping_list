import unittest
from ingredient import Ingredient
from units import Quantity, VolumeUnit
import pandas as pd


class TestIngredient(unittest.TestCase):
    def setUp(self):
        self.q1 = Quantity(VolumeUnit.CUP, 1)
        self.q2 = Quantity(VolumeUnit.TABLESPOON, 2)
        self.ingredient1 = Ingredient("broth", self.q1)
        self.ingredient2 = Ingredient("broth", self.q2)

    def test_str(self):
        self.assertEqual(str(self.ingredient1), f"{self.q1} broth")

    def test_add(self):
        result = self.ingredient1 + self.ingredient2
        self.assertEqual(result.name, "broth")
        self.assertEqual(result.quantity, self.q1 + self.q2)

    def test_to_dict_flatten(self):
        d = self.ingredient1.to_dict(flatten=True)
        self.assertIn("name", d)
        self.assertIn("unit", d)
        self.assertIn("amount", d)
        self.assertEqual(d["name"], "broth")

    def test_to_dict_nested(self):
        d = self.ingredient1.to_dict(flatten=False)
        self.assertIn("name", d)
        self.assertIn("quantity", d)
        self.assertIsInstance(d["quantity"], dict)

    def test_from_dict(self):
        d = self.ingredient1.to_dict(flatten=False)
        ing = Ingredient.from_dict(d)
        self.assertEqual(ing, self.ingredient1)

    def test_to_series(self):
        s = self.ingredient1.to_series()
        self.assertIsInstance(s, pd.Series)
        self.assertEqual(s["name"], "broth")
        self.assertEqual(s["unit"], "cup")
        self.assertEqual(s["amount"], 1)


class TestIngredientFromArgs(unittest.TestCase):
    def test_from_args_valid(self):
        ing = Ingredient.from_args("carrot", "cup", 2)
        self.assertEqual(ing.name, "carrot")
        self.assertEqual(str(ing.quantity), "2 cup")

        ing2 = Ingredient.from_args("egg", "item", 3)
        self.assertEqual(ing2.name, "egg")
        self.assertEqual(str(ing2.quantity), "3 item")

    def test_from_args_invalid_unit(self):
        with self.assertRaises(ValueError):
            Ingredient.from_args("carrot", "banana", 2)


if __name__ == "__main__":
    unittest.main()
