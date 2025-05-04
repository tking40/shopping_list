import unittest
from unittest.mock import patch, MagicMock
from ingredient_parser import IngredientParser, ParsedIngredient


class TestIngredientParser(unittest.TestCase):
    def setUp(self):
        self.parser = IngredientParser()

    @patch("ingredient_parser.litellm.completion")
    def test_parse_ingredient_normal(self, mock_completion):
        # Tests parsing a standard ingredient string.
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"amount": 2.0, "unit": "cups", "name": "oats"}'
                )
            )
        ]
        mock_completion.return_value = mock_response
        result = self.parser.parse_ingredient("2 cups oats")
        self.assertEqual(result, ParsedIngredient(amount=2.0, unit="cups", name="oats"))

    @patch("ingredient_parser.litellm.completion")
    def test_parse_ingredient_with_code_fence(self, mock_completion):
        # Tests parsing when the response is wrapped in a code fence.
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='```json\n{"amount": 100.0, "unit": "grams", "name": "flour"}\n```'
                )
            )
        ]
        mock_completion.return_value = mock_response
        result = self.parser.parse_ingredient("100g of flour")
        self.assertEqual(
            result, ParsedIngredient(amount=100.0, unit="grams", name="flour")
        )

    @patch("ingredient_parser.litellm.completion")
    def test_parse_ingredient_missing_fields(self, mock_completion):
        # Tests parsing when amount and unit are missing in the input.
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"amount": 1.0, "unit": "item", "name": "egg"}'
                )
            )
        ]
        mock_completion.return_value = mock_response
        result = self.parser.parse_ingredient("egg")
        self.assertEqual(result, ParsedIngredient(amount=1.0, unit="item", name="egg"))

    @patch("ingredient_parser.litellm.completion")
    def test_parse_ingredient_invalid_json(self, mock_completion):
        # Tests error handling when the response is not valid JSON.
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not a json"))]
        mock_completion.return_value = mock_response
        with self.assertRaises(ValueError):
            self.parser.parse_ingredient("invalid string")

    @patch("ingredient_parser.litellm.completion")
    def test_batch_parse_ingredients(self, mock_completion):
        # Tests batch parsing of multiple ingredient strings.
        def side_effect(*args, **kwargs):
            content_map = {
                "2 cups oats": '{"amount": 2.0, "unit": "cups", "name": "oats"}',
                "100g of flour": '{"amount": 100.0, "unit": "grams", "name": "flour"}',
            }
            # Always get the user content from kwargs
            user_content = kwargs["messages"][1]["content"]
            mock_resp = MagicMock()
            mock_resp.choices = [
                MagicMock(message=MagicMock(content=content_map[user_content]))
            ]
            return mock_resp

        mock_completion.side_effect = side_effect
        ingredients = ["2 cups oats", "100g of flour"]
        results = self.parser.batch_parse_ingredients(ingredients)
        self.assertEqual(
            results[0], ParsedIngredient(amount=2.0, unit="cups", name="oats")
        )
        self.assertEqual(
            results[1], ParsedIngredient(amount=100.0, unit="grams", name="flour")
        )


if __name__ == "__main__":
    unittest.main()
