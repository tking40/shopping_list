import unittest
import json
from unittest.mock import patch, Mock, MagicMock
from recipe_parser import (
    parse_ingredients,
    llm_parse_ingredients,
    ParsedIngredient,
    parse_recipe,
    main,
)


EXAMPLE_EXTRACTED_RECIPE = """
 Here's the information extracted from the recipe:

**Ingredients:**

*   1¾ cups water or broth
*   1 cup quinoa, long-grain white rice or a mix of the two, rinsed
*   Salt and black pepper
*   1 (14-ounce) can of any beans
*   1 small garlic clove
*   2 tablespoons extra-virgin olive oil
*   1 bunch collard greens, kale, spinach or other hearty dark leafy green
*   1 lemon
*   Toppings (optional): toasted nuts or seeds, fresh herbs, grated or crumbled cheese, soft-boiled egg, avocado, hot sauce or other sauces and so on

**Instructions:**

1.  In a large pot or Dutch oven, bring the water, quinoa and a generous pinch each of salt and pepper to a boil over high. Cover, reduce heat to low and simmer for 13 minutes.
2.  While the quinoa cooks, drain and rinse the beans, then transfer to a small bowl. Finely grate the garlic over the beans, then add the oil and a pinch each of salt and pepper, and stir to combine. Set aside. Remove and discard any tough stems from the greens, then roughly chop the leaves.
3.  After 13 minutes, arrange the greens on top of the quinoa and season well with salt and pepper. Cover and cook until the quinoa is tender, 5 to 7 minutes. (When the quinoa is tender, it's also translucent and has a thin white tail.) Remove the pot from heat, scrape the beans over the greens, then cover the pot and let sit for 5 minutes.
4.  Finely grate some of the lemon zest over the beans and greens, then cut the lemon into wedges. Eat the beans, greens and grains with a squeeze of lemon juice, salt and pepper to taste and any toppings you like.
"""

EXAMPLE_EXTRACTED_INGREDIENTS = """
```json
[
  {
    "amount": 1.75,
    "unit": "cups",
    "name": "water or broth"
  },
  {
    "amount": 1.0,
    "unit": "cup",
    "name": "quinoa"
  },
  {
    "amount": 14.0,
    "unit": "ounces",
    "name": "canned beans"
  },
  {
    "amount": 1.0,
    "unit": "item",
    "name": "small garlic clove"
  },
  {
    "amount": 2.0,
    "unit": "tablespoons",
    "name": "extra-virgin olive oil"
  },
  {
    "amount": 1.0,
    "unit": "bunch",
    "name": "collard greens"
  },
  {
    "amount": 1.0,
    "unit": "item",
    "name": "lemon"
  }
]
```
"""


class TestRecipeParser(unittest.TestCase):

    def test_parse_ingredients_with_example_output(self):
        """Test that parse_ingredients correctly parses the example output format."""
        ingredients = parse_ingredients(EXAMPLE_EXTRACTED_INGREDIENTS)

        # Check that we get the expected number of ingredients
        self.assertEqual(len(ingredients), 7)

        # Check the first ingredient
        first_ingredient = ingredients[0]
        self.assertIsInstance(first_ingredient, ParsedIngredient)
        self.assertEqual(first_ingredient.amount, 1.75)
        self.assertEqual(first_ingredient.unit, "cups")
        self.assertEqual(first_ingredient.name, "water or broth")

        # Check the last ingredient
        last_ingredient = ingredients[-1]
        self.assertEqual(last_ingredient.amount, 1.0)
        self.assertEqual(last_ingredient.unit, "item")
        self.assertEqual(last_ingredient.name, "lemon")

        # Verify all ingredients have the expected structure
        for ingredient in ingredients:
            self.assertIsInstance(ingredient.amount, float)
            self.assertIsInstance(ingredient.unit, str)
            self.assertIsInstance(ingredient.name, str)
            self.assertGreater(ingredient.amount, 0.0)
            self.assertNotEqual(ingredient.unit, "")
            self.assertNotEqual(ingredient.name, "")

    def test_parse_ingredients_handles_json_extraction(self):
        """Test that parse_ingredients correctly extracts JSON from code fences."""
        test_input = """
        Here are the ingredients:
        ```json
        [
          {
            "amount": 1.0,
            "unit": "cup",
            "name": "flour"
          }
        ]
        ```
        """

        ingredients = parse_ingredients(test_input)
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(ingredients[0].name, "flour")
        self.assertEqual(ingredients[0].amount, 1.0)
        self.assertEqual(ingredients[0].unit, "cup")

    def test_parse_ingredients_without_code_fences(self):
        """Test parsing JSON without code fences."""
        test_input = """
        [
          {
            "amount": 2.0,
            "unit": "cups",
            "name": "sugar"
          }
        ]
        """

        ingredients = parse_ingredients(test_input)
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(ingredients[0].name, "sugar")
        self.assertEqual(ingredients[0].amount, 2.0)
        self.assertEqual(ingredients[0].unit, "cups")

    def test_parse_ingredients_invalid_json(self):
        """Test that parse_ingredients raises appropriate error for invalid JSON."""
        with self.assertRaises(ValueError) as context:
            parse_ingredients("not valid json")

        self.assertIn("Failed to parse ingredients", str(context.exception))

    def test_parse_ingredients_empty_response(self):
        """Test that parse_ingredients raises error for empty response."""
        with self.assertRaises(ValueError) as context:
            parse_ingredients("")

        self.assertIn("No JSON found in response", str(context.exception))

    def test_parse_ingredients_missing_fields(self):
        """Test parsing with missing required fields."""
        test_input = """
        [
          {
            "amount": 1.0,
            "name": "incomplete ingredient"
          }
        ]
        """

        with self.assertRaises(ValueError):
            parse_ingredients(test_input)

    @patch("recipe_parser.requests.get")
    @patch("recipe_parser.litellm.completion")
    def test_parse_recipe_success(self, mock_completion, mock_get):
        """Test successful recipe parsing from URL."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <h1>Test Recipe</h1>
                <ul>
                    <li>1 cup flour</li>
                    <li>2 eggs</li>
                </ul>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = EXAMPLE_EXTRACTED_RECIPE
        mock_completion.return_value = mock_llm_response

        result = parse_recipe("https://example.com/recipe")

        # Verify HTTP request was made
        mock_get.assert_called_once_with("https://example.com/recipe")

        # Verify LLM was called
        mock_completion.assert_called_once()

        # Verify result
        self.assertEqual(result, EXAMPLE_EXTRACTED_RECIPE)

    @patch("recipe_parser.litellm.completion")
    def test_llm_parse_ingredients_success(self, mock_completion):
        """Test successful LLM parsing of ingredients."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = EXAMPLE_EXTRACTED_INGREDIENTS
        mock_completion.return_value = mock_llm_response

        result = llm_parse_ingredients(EXAMPLE_EXTRACTED_RECIPE)

        # Verify LLM was called with correct parameters
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        self.assertEqual(call_args[1]["model"], "openai/gpt-4.1-2025-04-14")
        self.assertEqual(call_args[1]["temperature"], 0.0)
        self.assertEqual(len(call_args[1]["messages"]), 2)

        # Verify result
        self.assertEqual(result, EXAMPLE_EXTRACTED_INGREDIENTS)

    def test_llm_parse_ingredients_content_too_long(self):
        """Test that llm_parse_ingredients raises error for content that's too long."""
        long_content = "x" * 10001  # Over the 10000 character limit

        with self.assertRaises(AssertionError) as context:
            llm_parse_ingredients(long_content)

        self.assertIn("Response content is too long", str(context.exception))

    @patch("recipe_parser.parse_recipe")
    @patch("recipe_parser.llm_parse_ingredients")
    @patch("recipe_parser.parse_ingredients")
    @patch("recipe_parser.argparse.ArgumentParser")
    def test_main_function(
        self, mock_argparse, mock_parse_ingredients, mock_llm_parse, mock_parse_recipe
    ):
        """Test the main function with mocked dependencies."""
        # Mock command line arguments
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.url = "https://example.com/recipe"
        mock_parser.parse_args.return_value = mock_args
        mock_argparse.return_value = mock_parser

        # Mock function returns
        mock_parse_recipe.return_value = EXAMPLE_EXTRACTED_RECIPE
        mock_llm_parse.return_value = EXAMPLE_EXTRACTED_INGREDIENTS
        mock_parse_ingredients.return_value = [
            ParsedIngredient(1.75, "cups", "water or broth"),
            ParsedIngredient(1.0, "cup", "quinoa"),
        ]

        # Capture print output
        with patch("builtins.print") as mock_print:
            main()

        # Verify function calls
        mock_parse_recipe.assert_called_once_with("https://example.com/recipe")
        mock_llm_parse.assert_called_once_with(EXAMPLE_EXTRACTED_RECIPE)
        mock_parse_ingredients.assert_called_once_with(EXAMPLE_EXTRACTED_INGREDIENTS)

        # Verify output
        expected_calls = [
            unittest.mock.call("1.75 cups water or broth"),
            unittest.mock.call("1.0 cup quinoa"),
        ]
        mock_print.assert_has_calls(expected_calls)

    def test_parse_ingredients_with_different_json_formats(self):
        """Test parsing ingredients with various JSON formatting scenarios."""
        # Test with extra whitespace
        test_input_whitespace = """
        
        ```json
        
        [
          {
            "amount": 1.5,
            "unit": "cups",
            "name": "milk"
          }
        ]
        
        ```
        
        """

        ingredients = parse_ingredients(test_input_whitespace)
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(ingredients[0].amount, 1.5)

        # Test without json marker in code fence
        test_input_no_marker = """
        ```
        [
          {
            "amount": 0.5,
            "unit": "tsp",
            "name": "vanilla"
          }
        ]
        ```
        """

        ingredients = parse_ingredients(test_input_no_marker)
        self.assertEqual(len(ingredients), 1)
        self.assertEqual(ingredients[0].unit, "tsp")

    def test_parsed_ingredient_dataclass(self):
        """Test the ParsedIngredient dataclass."""
        ingredient = ParsedIngredient(2.5, "cups", "flour")

        self.assertEqual(ingredient.amount, 2.5)
        self.assertEqual(ingredient.unit, "cups")
        self.assertEqual(ingredient.name, "flour")

        # Test string representation
        self.assertIn("2.5", str(ingredient))
        self.assertIn("cups", str(ingredient))
        self.assertIn("flour", str(ingredient))


if __name__ == "__main__":
    unittest.main()
