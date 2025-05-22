import requests
from bs4 import BeautifulSoup
import litellm
import json
import re
import argparse
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()

# DEFAULT_MODEL = "openai/gpt-4.1-nano-2025-04-14"
DEFAULT_MODEL = "gemini/gemini-2.0-flash-lite"
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

ex_recipe = """

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

ex_output = """
```json
[
  {
    "amount": 3.0,
    "unit": "tbsp.",
    "name": "extra-virgin olive oil"
  },
  {
    "amount": 2.0,
    "unit": "lb.",
    "name": "chicken thighs"
  },
  {
    "amount": 1.0,
    "unit": "lb.",
    "name": "baby red potatoes"
  },
  {
    "amount": 2.0,
    "unit": "tbsp.",
    "name": "butter"
  },
  {
    "amount": 5.0,
    "unit": "item",
    "name": "cloves garlic"
  },
  {
    "amount": 2.0,
    "unit": "tbsp.",
    "name": "fresh thyme"
  },
  {
    "amount": 1.0,
    "unit": "item",
    "name": "Freshly chopped parsley"
  },
  {
    "amount": 2.0,
    "unit": "tbsp.",
    "name": "freshly grated Parmesan"
  }
]
```
"""


@dataclass
class ParsedIngredient:
    amount: float
    unit: str
    name: str


def parse_recipe(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup.prettify())

    prompt = f"Extract the ingredients and instructions from the following recipe: {soup.prettify()}"
    messages = [
        {"role": "user", "content": prompt},
    ]
    response = litellm.completion(
        model=DEFAULT_MODEL,
        messages=messages,
    )
    response_content = response.choices[0].message.content
    print("\nDEBUG parse_recipe:\n\n", response_content)
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
    print("\nDEBUG parse_ingredients:\n\n", response_content)
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
    parser = argparse.ArgumentParser(description='Parse recipe ingredients from a URL')
    parser.add_argument('url', help='URL of the recipe to parse')
    args = parser.parse_args()
    
    content = parse_recipe(args.url)

    ingredients_content = llm_parse_ingredients(content)
    ingredients = parse_ingredients(ingredients_content)

    for ingredient in ingredients:
        print(f"{ingredient.amount} {ingredient.unit} {ingredient.name}")


if __name__ == "__main__":
    main()
