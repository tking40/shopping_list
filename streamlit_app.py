import streamlit as st
import pandas as pd
import logging

from main.recipe_parser import parse_recipe, llm_parse_ingredients, parse_ingredients

# Configure logging to show only in the terminal / backend, not Streamlit UI
logging.basicConfig(level=logging.INFO)

st.title("📝 Recipe Ingredient Parser")

st.markdown(
    """
This small web-app lets you extract structured ingredients from any recipe.

1. Either **paste a recipe URL** or **paste the raw recipe text** below.
2. Click **Parse** and wait a few seconds (the model needs to think!).
3. View the ingredients in a table and copy them for your shopping-list.
"""
)

# --- User inputs -----------------------------------------------------------------
url_input = st.text_input("Recipe URL (leave blank if pasting recipe text)")

# --- Parse button -----------------------------------------------------------------
if st.button("Parse"):
    if not url_input:
        st.warning("Please supply either a recipe URL.")
        st.stop()

    # -------------------------------------------------------------------------
    try:
        # Use a dynamic status box so the user sees which step is running ------
        with st.status("Starting …", expanded=False) as status:
            # -- Step 1 ---------------------------------------------------------
            status.update(label="Fetching recipe …", state="running")

            raw_content = parse_recipe(url_input)
            if "cloudflare" in raw_content.lower():
                st.toast("Cloudflare protection detected - may be unable to parse recipe", icon="🚨")

            # -- Step 2 ---------------------------------------------------------
            status.update(label="Calling LLM to extract ingredients …", state="running")
            ingredients_json_str = llm_parse_ingredients(raw_content)

            # -- Step 3 ---------------------------------------------------------
            status.update(label="Parsing ingredients JSON …", state="running")
            parsed_ingredients = parse_ingredients(ingredients_json_str)

            # -- Done -----------------------------------------------------------
            status.update(label="✅ Done!", state="complete")

        # 4. Display --------------------------------------------------------------
        if parsed_ingredients:
            df = pd.DataFrame([
                {
                    "Amount": ing.amount,
                    "Unit": ing.unit,
                    "Name": ing.name,
                }
                for ing in parsed_ingredients
            ])
            st.success("Parsed ingredients:")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No ingredients found.")

        # -- Raw content -----------------------------------------------------------
        with st.expander("Show raw recipe text"):
            st.text_area("Recipe content", raw_content, height=300)

    except Exception as e:
        st.error(f"Error while parsing recipe: {e}") 