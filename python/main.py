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
url_list = pd.read_csv(table_path + "url_list.txt")

stopfoods = pd.read_csv(table_path + "stop_foods.txt")
ingredients_lookup = pd.read_csv(table_path + "ingredients_lookup.csv")
units_lookup = pd.read_csv(table_path + "units_lookup.csv")
grocery_units = pd.read_csv(table_path + "grocery_units.csv")

name_tables = [stopfoods,ingredients_lookup,units_lookup,grocery_units]

default_cart = pd.read_pickle(table_path + "shopping_cart.pickle")

v2v_table = pd.read_csv(table_path + "volume_to_volume.csv")
m2m_table = pd.read_csv(table_path + "mass_to_mass.csv")
v2m_table = pd.read_csv(table_path + "volume_to_mass.csv")
m2v_table = pd.read_csv(table_path + "mass_to_volume.csv")
conv_tables = [v2v_table,m2m_table,v2m_table,m2v_table]

# Flags
verbose = True
dbug = True


#%% Add stored recipes from csv files
shopping_cart = utils.newCart(default_cart) # initialize Cart

active_ix = np.flatnonzero(recipe_list.Select) # get active recipes
# ^ np.argwhere does not work with numpy 1.18.1. Using flatnonzero instead

# active_recipes = recipe_list.iloc[active_ix.flatten()] # this is needed for np.argwhere
active_recipes = recipe_list.iloc[active_ix]

for index,recipe in active_recipes.iterrows():
    print("Adding " + recipe.Name + "...") if verbose else ...
    ingredients = utils.loadAndFilterRecipe(recipe,recipe_path,name_tables,
                                            conv_tables,verbose,dbug)
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

#%% Add new recipes from URLs
for index,recipe in url_list.iterrows():
    print("Adding " + recipe.Name + "...") if verbose else ...
    ingredients = utils.loadAndFilterRecipe(recipe,recipe_path,name_tables,
                                            conv_tables,verbose,dbug)
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

#%% Print out list
shopping_cart.sortAndPrint()

# print("Directions")
# for i,j in enumerate(dirList): print(i+1,j)