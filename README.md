# Shopping List

A Python application that parses recipes from URLs and extracts structured ingredients for shopping lists.

## Project Structure

### Active Code (Current Focus)
The active codebase focuses on simple recipe URL parsing:

- **`main/recipe_parser.py`** - Recipe URL parsing and ingredient extraction using LLMs
- **`streamlit_app.py`** - Web UI for parsing recipes

Flow: URL → fetch HTML → LLM extracts recipe → LLM parses ingredients → display results

### Inactive Code (Future Vision)
These modules represent a more ambitious vision for combining multiple recipes via semantic similarity into a unified shopping list. They are **not currently integrated** into the active app:

- **`main/shopping_list.py`** - Shopping list management with recipe grouping
- **`main/ingredient.py`** - Ingredient data model with unit-aware quantities
- **`main/units.py`** - Unit conversion (volume, mass, count)
- **`main/embeddings.py`** - Semantic search for similar ingredients
- **`main/embeddings_db_store.py`** - SQLite storage for ingredient embeddings
- **`main/ingredient_parser.py`** - Standalone ingredient string parser (similar to recipe_parser)

The intended flow for this subsystem: Multiple recipes → extract ingredients → use embeddings to match similar items (e.g., "tomatoes" + "cherry tomatoes") → combine into unified shopping list

## Features
- **Recipe Parsing**: Extract ingredients from recipe URLs using LLMs
- **Smart Ingredient Extraction**: Handles amounts, units, and ingredient names
- **(Planned) Smart Ingredient Management**: Combine ingredients across recipes using semantic similarity

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

