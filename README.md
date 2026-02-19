# Shopping List

WIP: Recipe parsing and shopping list management complete, integration of the two is still wip.

A Python application that intelligently manages shopping lists based on recipes you want to make. Parse recipes from URLs, extract ingredients with proper units, and generate consolidated shopping lists.

General idea is use a very cheap, long context model to parse raw dump from beautiful soup into just the recipe content, and then use a better model to do the ingredient parsing into JSON structure from there. Then the other half of the project is using an embedding store to align common ingredients and manage them in a central list.

## Features
- **Recipe Parsing**: Extract ingredients from recipe URLs using a combination of LLM providers.
- **Smart Ingredient Management**: Handle different units, amounts, and ingredient combinations
- **Embeddings Search**: Find similar ingredients using semantic search

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd shopping_list
```

2. Install dependencies:
```bash
uv sync
```

3. Set up API keys in `main/.env` for your LLM providers

## Usage

### Parse a Recipe from URL
```bash
cd main
uv run recipe_parser.py "https://example.com/recipe" --verbose
```

Outputs just the extracted ingredients.

`--verbose` Will print the extracted recipe ingredient and directions.

## Testing

Run all with `./run_tests.sh`

## Project Structure

- `main/shopping_list.py` - Core shopping list management
- `main/recipe_parser.py` - Recipe URL parsing and ingredient extraction
- `main/ingredient.py` - Ingredient data model
- `main/units.py` - Unit conversion and normalization
- `main/embeddings.py` - Semantic search for ingredients
- `main/ingredient_parser.py` - Natural language ingredient parsing

## Requirements

- Python 3.12+
- OpenAI API key (for ingredient parsing)
- Google Gemini API key (for url parsing)

