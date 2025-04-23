import pandas as pd
from typing import Dict, Optional
from ingredient import Ingredient


class ShoppingList:
    def __init__(self, recipe_ingredients: Dict[str, Dict[str, Ingredient]] = None):
        """Initialize a new shopping list."""
        self.recipe_ingredients = (
            recipe_ingredients if recipe_ingredients is not None else {}
        )

    def ingredients(self) -> Dict[str, Ingredient]:
        """Returns a dictionary of all ingredients in the shopping list."""
        all_ingredients = (
            ing
            for recipe in self.recipe_ingredients.values()
            for ing in recipe.values()
        )
        combined_ingredients = {}
        for ingredient in all_ingredients:
            if ingredient.name in combined_ingredients:
                combined_ingredients[ingredient.name] = (
                    combined_ingredients[ingredient.name] + ingredient
                )
            else:
                combined_ingredients[ingredient.name] = ingredient.copy()
        return combined_ingredients

    def add_ingredient(
        self, name: str, units: str, amount: float, recipe_name: str = "general"
    ) -> None:
        """Add an ingredient for a specific recipe."""
        ingredient = Ingredient.from_args(name, units, amount)

        if recipe_name not in self.recipe_ingredients:
            self.recipe_ingredients[recipe_name] = {}

        if ingredient.name in self.recipe_ingredients[recipe_name]:
            # Add to existing amount for this recipe
            existing_ingredient = self.recipe_ingredients[recipe_name][ingredient.name]
            self.recipe_ingredients[recipe_name][ingredient.name] = (
                existing_ingredient + ingredient
            )
        else:
            self.recipe_ingredients[recipe_name][ingredient.name] = ingredient

    def find_ingredient(self, ingredient_name: str) -> Optional[Ingredient]:
        """Returns the combined ingredient across all recipes"""
        return self.ingredients().get(ingredient_name)

    def for_recipe(self, recipe_name: str) -> "ShoppingList":
        """Returns a new shopping list with only the ingredients for the given recipe"""
        recipe_ingredients = self.recipe_ingredients.get(recipe_name, {})
        if not recipe_ingredients:
            raise ValueError(f"No ingredients found for recipe: {recipe_name}")
        return ShoppingList({recipe_name: recipe_ingredients})

    def remove_recipe(self, recipe_name: str) -> None:
        """Remove all ingredients for a specific recipe"""
        self.recipe_ingredients.pop(recipe_name, None)

    def as_dataframe(self) -> pd.DataFrame:
        """Convert the shopping list to a pandas DataFrame."""
        ingredients_series = [
            ingredient.to_series() for ingredient in self.ingredients().values()
        ]
        return pd.DataFrame(ingredients_series)

    def __str__(self) -> str:
        """Print the shopping list contents in a simplified format."""
        ingredients_str = [
            str(ingredient) for ingredient in self.ingredients().values()
        ]
        return "\n".join(ingredients_str)

    def to_file(self, filename: str) -> None:
        """Save the shopping list to csv"""
        self.as_dataframe().to_csv(filename, index=False)


if __name__ == "__main__":
    # Example usage
    shopping_list = ShoppingList()

    # Add ingredients with recipe amounts
    shopping_list.add_ingredient("apple", "item", 2, "recipe1")
    shopping_list.add_ingredient("apple", "item", 3, "recipe2")
    shopping_list.add_ingredient("banana", "item", 1, "recipe2")
    shopping_list.add_ingredient("apple", "item", 2)
    shopping_list.add_ingredient("banana", "item", 3)

    shopping_list.remove_recipe("recipe2")
    # print(shopping_list.find_ingredient("apple"))
    print(shopping_list)
    # print(shopping_list.as_dataframe())

    # print(shopping_list.for_recipe("general"))
