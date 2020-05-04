# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 07:31:27 2020

@author: Thomas
"""

''' Imports and Table Loads'''

import pandas as pd
import numpy as np

table_path = 'C:/Users/Thomas/Documents/MATLAB/shopping_list/python/tables/'
recipe_path = 'C:/Users/Thomas/Documents/MATLAB/shopping_list/python/recipes/'

stopfoods = pd.read_csv(table_path + 'stop_foods.txt')
pantry = pd.read_csv(table_path + 'pantry.csv')
recipe_list = pd.read_csv(table_path + 'recipe_list.csv')
default_cart = pd.read_pickle(table_path + 'shopping_cart.pickle')

#%% Define Classes and Functions
class newCart:
    def __init__(self, newCart):
        self.list = newCart
        
    def addToCart(self,newIngredient):
#        self.list = pd.([self.list,newIngredient])
        self.list = self.list.append(newIngredient)

def loadAndFilterRecipe(recipe_name):
    ''' Load'''
    ingredients = pd.read_csv(recipe_path + recipe_name + '.csv')
    
    ''' Filter '''
    # force lower case for comparisons later
    ingredients.Name = ingredients.Name.str.lower() 
    # convert generic names
    # convert to common units
    
    #Add recipe name
    name_series = pd.Series(recipe_name).repeat(len(ingredients))
    name_series.name = "Recipe"
    return pd.DataFrame.join(ingredients,name_series.reset_index(drop=True))


#%% Initialize Cart
shopping_cart = newCart(default_cart)
#%% Loop through recipe list and add ingredients to cart

active_ix = np.argwhere(recipe_list.Select)
active_recipes = recipe_list.iloc[active_ix.flatten()]
for index,recipe in active_recipes.iterrows():
    print("Adding " + recipe.Name + "...")
    ingredients = loadAndFilterRecipe(recipe.Name)
    for index,ingredient in ingredients.iterrows():
        shopping_cart.addToCart(ingredient)



