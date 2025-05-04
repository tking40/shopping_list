from typing import Dict, Optional
import litellm
import json
from dataclasses import dataclass
from dotenv import load_dotenv
import re

load_dotenv()

DEFAULT_MODEL = "gemini/gemini-2.0-flash-lite"

SYSTEM_PROMPT = """
"You are a helpful assistant that parses ingredient strings into structured data.

Given an ingredient string, return a JSON object with these fields:
- amount: float (the numeric amount)
- unit: string (the unit of measurement)
- name: string (the ingredient name)

Example response for "2 cups oats":
{{
    "amount": 2.0,
    "unit": "cups",
    "name": "oats"
}}

Example response for "100g of flour":
{{
    "amount": 100.0,
    "unit": "grams",
    "name": "flour"
}}

If the units are not specified, use "unit": "item"
If the amount is not specified, use "amount": 1.0
For the names, correct any obvious typos or misspellings.
"""


@dataclass
class ParsedIngredient:
    amount: float
    unit: str
    name: str


class IngredientParser:
    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize the ingredient parser.

        Args:
            api_key: API key for the LLM provider
            model: Model to use for parsing (default: gpt-3.5-turbo)
        """
        self.model = model

    def parse_ingredient(self, ingredient_str: str) -> ParsedIngredient:
        """Parse an ingredient string into structured data.

        Args:
            ingredient_str: String like "2 cups oats" or "1/2 tbsp olive oil"

        Returns:
            ParsedIngredient object containing amount, unit, and name
        """

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {"role": "user", "content": ingredient_str},
        ]

        response = litellm.completion(
            model=self.model, messages=messages, temperature=0
        )
        response_content = response.choices[0].message.content
        print(response_content)

        # Extract JSON from code fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_content)
        if match:
            json_str = match.group(1)
        else:
            json_str = response_content.strip()

        if not json_str.strip():
            raise ValueError(
                f"No JSON found in response. Raw response: {response_content}"
            )

        try:
            parsed = json.loads(json_str)
            return ParsedIngredient(
                amount=float(parsed["amount"]), unit=parsed["unit"], name=parsed["name"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(
                f"Failed to parse ingredient string: {ingredient_str}. JSON string: {json_str}"
            ) from e

    def batch_parse_ingredients(
        self, ingredient_strings: list[str]
    ) -> list[ParsedIngredient]:
        """Parse multiple ingredient strings.

        Args:
            ingredient_strings: List of ingredient strings

        Returns:
            List of ParsedIngredient objects
        """
        return [self.parse_ingredient(ing) for ing in ingredient_strings]
