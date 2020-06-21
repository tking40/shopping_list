# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 07:31:27 2020

@author: Thomas
"""

# Standard Library Imports
import warnings
from sys import platform as _platform


# Third Party Imports
import pandas as pd
import numpy as np

# Local application imports
import utils
# for some reason, 'from . import utils' doesn't work

#%% Initialization
# Filter Warnings
warnings.filterwarnings("ignore")
# ^ Doing this because the way I'm currently assigning values to dataframes
# triggers a warning that I'm writing to an object reference, not a copy, which
# is what I want to do

# Platform dependent path
if _platform == "darwin": # Mac
    root = "/Users/thomasj.king/Documents/Python_Scripts/shopping_list/"
else: # Windows
    root = "C:/Users/Thomas/Documents/MATLAB/shopping_list/"

# Table Loads
table_path = root + "python/tables/"
recipe_path = root + "python/recipes/"

pantry = pd.read_csv(table_path + "pantry.csv")
recipe_list = pd.read_csv(table_path + "recipe_list.csv")
url_list = pd.read_csv(table_path + "url_list.csv")

stopfoods = pd.read_csv(table_path + "stop_foods.txt")
generic_names = pd.read_csv(table_path + "generic_names.csv")
grocery_units = pd.read_csv(table_path + "grocery_units.csv")
name_tables = [stopfoods,generic_names,grocery_units]

default_cart = pd.read_pickle(table_path + "shopping_cart.pickle")

v2v_table = pd.read_csv(table_path + "volume_to_volume.csv")
m2m_table = pd.read_csv(table_path + "mass_to_mass.csv")
v2m_table = pd.read_csv(table_path + "volume_to_mass.csv")
m2v_table = pd.read_csv(table_path + "mass_to_volume.csv")
conv_tables = [v2v_table,m2m_table,v2m_table,m2v_table]

# Flags
verbose = False
dbug = True


#%% Add stored recipes from csv files
shopping_cart = utils.newCart(default_cart) # initialize Cart

active_ix = np.flatnonzero(recipe_list.Select) # get active recipes
# ^ np.argwhere does not work with numpy 1.18.1. Using flatnonzero instead

# active_recipes = recipe_list.iloc[active_ix.flatten()] # this is needed for np.argwhere
active_recipes = recipe_list.iloc[active_ix]

for index,recipe in active_recipes.iterrows():
    print("Adding " + recipe.Name + "...") if verbose else ...
    ingredients = utils.loadAndFilterRecipe(recipe.Name,recipe_path,name_tables,
                                            conv_tables,verbose,dbug)
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

#%% Add new recipes from URLs


#%% Print out list
shopping_cart.sortAndPrint()

#%% Soup It!

URL = 'https://www.food.com/recipe/shrimp-and-grits-518698'
URL = 'https://www.food.com/recipe/slow-cooker-chicken-pozole-345614'
URL = 'https://www.food.com/recipe/quick-and-easy-pizza-dough-117532'
URL = 'https://www.budgetbytes.com/slow-cooker-chicken-tikka-masala/'
"""
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
# results = soup.find(id='__layout')

recipe_directions = soup.find("div", {"class": "recipe-layout__directions"})
recipe_ingredients = soup.find("div", {"class": "recipe-layout__ingredients"})


ingredients = [x.get_text().strip()
               for x in recipe_ingredients.find_all('li')]
directions = [x.get_text().strip()
               for x in recipe_directions.find_all('li')]
"""
possibleUnits = ["cup","cups","lbs","pounds","tsp","teaspoons","teaspoon","tbsp","tablespoons","tablespoon"]
for index,recipe in url_list.iterrows():
    print("Adding " + recipe.Name + "...") if verbose else ...
    ingList,dirList = utils.loadURL(recipe.Address)
    ingredients = utils.parseIngredients(ingList,possibleUnits)
    
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

# ix = 0
# for y in ingredients:
#     ix+=1
#     print(ix,y)

# print("Ingredients")
# ingDF = utils.parseIngredients(ingredients,possibleUnits)
# print(ingDF)
# print('')

print("Directions")
for i,j in enumerate(dirList): print(i+1,j)