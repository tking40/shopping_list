import requests
from bs4 import BeautifulSoup
import litellm
import json
import re
import argparse
from dataclasses import dataclass
import logging

from dotenv import load_dotenv

load_dotenv()

# DEFAULT_MODEL = "openai/gpt-4.1-nano-2025-04-14"
DEFAULT_MODEL = "gemini/gemini-2.5-flash-lite"
INGREDIENTS_MODEL = "openai/gpt-4.1-2025-04-14"

SYSTEM_PROMPT = """
"You are a helpful assistant that parses recipes into structured data.

Given a recipe, parse the ingredients into a structured format:
For each ingredient string, return a JSON object with these fields:
- amount: float (the numeric amount)
- unit: string (the unit of measurement)
- name: string (the ingredient name)

Example response for "2 cups oats":
{{
    "amount": 2.0,
    "unit": "cups",
    "name": "oats"
}}

Canned items should be specified with correct volume/weight, and name should reflected "canned".
Example response for "1 14oz can of tomatoes:
{{
    "amount": 14.0,
    "unit": "ounces",
    "name": "canned tomatoes"
}}

Example response for "freshly chopped parsley":
{{
    "amount": 1.0,
    "unit": "item",
    "name": "Freshly chopped parsley"
}}


If the units are not specified, use "unit": "item"
NEVER use amount 0.0. If the amount is not specified, use "amount": 1.0
For the names, correct any obvious typos or misspellings.
If the ingredient is optional, prepend (optional) to the name.
Ignore staple ingredients like salt, pepper, oil, etc.

Return the ingredients in a JSON array of objects.

"""

log = logging.getLogger(__name__)


@dataclass
class ParsedIngredient:
    amount: float
    unit: str
    name: str


def parse_recipe(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    prompt = f"Extract the ingredients and instructions from the following recipe: {soup.prettify()}"
    messages = [
        {"role": "user", "content": prompt},
    ]
    response = litellm.completion(
        model=DEFAULT_MODEL,
        messages=messages,
    )
    response_content = response.choices[0].message.content
    log.info(f"\nparse_recipe:\n\n{response_content}")
    if "cloudflare" in response_content.lower():
        log.warning("Cloudflare protection detected - may be unable to parse recipe")
    return response_content


def llm_parse_ingredients(input_content):
    # assert that the returned content is less than 10000 characters
    assert len(input_content) < 10000, "Response content is too long"

    # prompt = f"Extract the ingredients from the following recipe: {response_content}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": input_content},
    ]
    response = litellm.completion(
        model=INGREDIENTS_MODEL, messages=messages, temperature=0.0
    )
    response_content = response.choices[0].message.content
    log.info(f"\nparse_ingredients:\n\n{response_content}")
    return response_content


def parse_ingredients(response_content):
    # Extract JSON from code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_content)
    if match:
        json_str = match.group(1)
    else:
        # If no code fences, try to extract just the JSON array before any instructions
        json_match = re.search(r"\[[\s\S]*?\]", response_content)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_content.strip()

    if not json_str.strip():
        raise ValueError(f"No JSON found in response. Raw response: {response_content}")

    try:
        parsed = json.loads(json_str)
        if not parsed:
            raise ValueError(f"No ingredients found! Raw response: {response_content}")
        return [
            ParsedIngredient(
                amount=float(ingredient["amount"]),
                unit=ingredient["unit"],
                name=ingredient["name"],
            )
            for ingredient in parsed
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse ingredients. JSON string: {json_str}") from e


def main():
    parser = argparse.ArgumentParser(description="Parse recipe ingredients from a URL")
    parser.add_argument("url", help="URL of the recipe to parse")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    content = parse_recipe(args.url)
    print(f"\nRecipe Content:\n{content}\n")

    ingredients_content = llm_parse_ingredients(content)
    ingredients = parse_ingredients(ingredients_content)

    for ingredient in ingredients:
        print(f"{ingredient.amount} {ingredient.unit} {ingredient.name}")


if __name__ == "__main__":
    main()
