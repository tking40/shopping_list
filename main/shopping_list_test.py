import unittest
from shopping_list import ShoppingList
from ingredient import Ingredient
import pandas as pd


class TestShoppingList(unittest.TestCase):
    def setUp(self):
        self.sl = ShoppingList()
        self.apple = Ingredient.from_args("apple", "item", 2)
        self.banana = Ingredient.from_args("banana", "item", 3)
        self.cup_flour = Ingredient.from_args("flour", "cup", 1)

    def test_add_and_aggregate_ingredients(self):
        self.sl.add_ingredient("apple", "item", 2, "recipe1")
        self.sl.add_ingredient("apple", "item", 3, "recipe2")
        self.sl.add_ingredient("banana", "item", 1, "recipe2")
        self.sl.add_ingredient("apple", "item", 2)
        self.sl.add_ingredient("banana", "item", 3)
        ingredients = self.sl.ingredients()
        self.assertEqual(ingredients["apple"].quantity.amount, 7)
        self.assertEqual(ingredients["banana"].quantity.amount, 4)

    def test_remove_recipe(self):
        self.sl.add_ingredient("apple", "item", 2, "recipe1")
        self.sl.add_ingredient("banana", "item", 3, "recipe2")
        self.sl.remove_recipe("recipe2")
        ingredients = self.sl.ingredients()
        self.assertIn("apple", ingredients)
        self.assertNotIn("banana", ingredients)

    def test_for_recipe(self):
        self.sl.add_ingredient("apple", "item", 2, "recipe1")
        self.sl.add_ingredient("banana", "item", 3, "recipe2")
        recipe1_list = self.sl.for_recipe("recipe1")
        self.assertIn("apple", recipe1_list.ingredients())
        self.assertNotIn("banana", recipe1_list.ingredients())
        with self.assertRaises(ValueError):
            self.sl.for_recipe("nonexistent")

    def test_as_dataframe(self):
        self.sl.add_ingredient("apple", "item", 2)
        self.sl.add_ingredient("banana", "item", 3)
        df = self.sl.as_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("apple", df["name"].values)
        self.assertIn("banana", df["name"].values)

    def test_str(self):
        self.sl.add_ingredient("apple", "item", 2)
        self.sl.add_ingredient("banana", "item", 3)
        s = str(self.sl)
        self.assertIn("apple", s)
        self.assertIn("banana", s)

    def test_find_ingredient(self):
        self.sl.add_ingredient("apple", "item", 2)
        found = self.sl.find_ingredient("apple")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "apple")
        self.assertEqual(found.quantity.amount, 2)
        not_found = self.sl.find_ingredient("carrot")
        self.assertIsNone(not_found)


if __name__ == "__main__":
    unittest.main()
