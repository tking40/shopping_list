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
generic_names = pd.read_csv(table_path + 'generic_names.csv')
grocery_units = pd.read_csv(table_path + 'grocery_units.csv')

v2v_table = pd.read_csv(table_path + 'volume_to_volume.csv')
m2m_table = pd.read_csv(table_path + 'mass_to_mass.csv')
v2m_table = pd.read_csv(table_path + 'volume_to_mass.csv')
m2v_table = pd.read_csv(table_path + 'mass_to_volume.csv')

#%% Define Classes and Functions
class newCart:
    def __init__(self, newCart):
        self.list = newCart
        
    def addToCart(self,newIngredient):
        # check if already in cart
        idx = self.list.Name == newIngredient.Name
        if np.any(idx):
            self.list.Amount[idx] += newIngredient.Amount
            self.list.Recipe[idx] += ', ' + newIngredient.Recipe
        else:
            self.list = self.list.append(newIngredient)

def convertGenericNames(ingredients,generic_names):
    ing_list = ingredients['Name']
    name_list = generic_names['Name']
    gen_list = generic_names['Generic']

    # finding matching indices first prevents from having to loop through every
    # ingredient and check it against the generic list - O(n) vs O(n^2)
    idx = np.where(ing_list.isin(name_list))
    if np.size(idx[0]):
        for ix in idx:
            gen_ix = np.where(name_list.isin(ing_list.iloc[ix]))
            ing_list.iloc[ix[0]] = gen_list.iloc[gen_ix[0][0]]
            # ^ this is obviously hideous, must be better way to slice and assign.
            # Doing above because np.where returns a tuple with an array inside, and if I 
            # don't pass iloc an integer index, it won't assign correctly to just
            # the variable in the series at that index

def convertUnits(ingredient,toUnit):
    # check if mass or volume ingredient
    fromMass = np.any(m2m_table.RowUnits == ingredient.Unit)
    toMass = np.any(m2m_table.RowUnits == toUnit)
    if fromMass and toMass:         # mass to mass
        convTable = m2m_table
    elif fromMass and not toMass:   # mass to volume
        conv_table = m2v_table
    elif not fromMass and toMass:   # volume to mass
        conv_table = v2m_table
    else:                           # volume to volume
        conv_table = v2v_table
        
    return float(conv_table[conv_table.RowUnits == ingredient.Unit][toUnit])*ingredient.Amount

def loadAndFilterRecipe(recipe_name):
    ''' Load'''
    ingredients = pd.read_csv(recipe_path + recipe_name + '.csv')
    
    ''' Filter '''
    # force lower case for comparisons later
    ingredients.Name = ingredients.Name.str.lower()
    # remove stop foods
    ingredients.drop(ingredients[ingredients.Name.isin(stopfoods.Name)].index)
    # convert generic names
    convertGenericNames(ingredients,generic_names)
    # convert to common units
    ing_to_check = ingredients[ingredients.Name.isin(grocery_units.Name)]
    for index,ing in ing_to_check.iterrows():
        des_unit = grocery_units.Unit[grocery_units.Name == ing.Name].reset_index(drop=True)[0] # this feels like a hacky workaround - having
        # trouble getting the string value for comparison, instead of a series object (we're just grabbing the 
        # first object in the series here)
        if ing.Unit != des_unit:
            try:
                ingredients.Amount[index] = convertUnits(ing,des_unit)
                ingredients.Unit[index] = des_unit
            except:
                print(ing.Name + " needs special conversion")
            
    
    #Add recipe name
    name_series = pd.Series(recipe_name).repeat(len(ingredients))
    name_series.name = "Recipe"
    return pd.DataFrame.join(ingredients,name_series.reset_index(drop=True)) 



#%% Loop through recipe list and add ingredients to cart
shopping_cart = newCart(default_cart) # initialize Cart

active_ix = np.argwhere(recipe_list.Select) # get active recipes
active_recipes = recipe_list.iloc[active_ix.flatten()]

for index,recipe in active_recipes.iterrows():
    print("Adding " + recipe.Name + "...")
    ingredients = loadAndFilterRecipe(recipe.Name)
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

# Sort and reindex shopping list
shopping_list = shopping_cart.list.sort_values(by=["Name"])
shopping_list = shopping_list.reset_index(drop=True)

print(shopping_list)
