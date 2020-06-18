# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 07:31:27 2020

@author: Thomas
"""

''' Imports and Table Loads'''

# Filter Warnings
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

from sys import platform as _platform
if _platform == "darwin":
    root = "/Users/thomasj.king/Documents/Python_Scripts/shopping_list/"
else:
    root = "C:/Users/Thomas/Documents/MATLAB/shopping_list/"

table_path = root + "python/tables/"
recipe_path = root + "python/recipes/"

stopfoods = pd.read_csv(table_path + "stop_foods.txt")
pantry = pd.read_csv(table_path + "pantry.csv")
recipe_list = pd.read_csv(table_path + "recipe_list.csv")
default_cart = pd.read_pickle(table_path + "shopping_cart.pickle")
generic_names = pd.read_csv(table_path + "generic_names.csv")
grocery_units = pd.read_csv(table_path + "grocery_units.csv")

v2v_table = pd.read_csv(table_path + "volume_to_volume.csv")
m2m_table = pd.read_csv(table_path + "mass_to_mass.csv")
v2m_table = pd.read_csv(table_path + "volume_to_mass.csv")
m2v_table = pd.read_csv(table_path + "mass_to_volume.csv")

# verbose = True
verbose = False

dbug = True
# dbug = False

#%% Define Classes and Functions
class newCart:
    def __init__(self, newCart):
        self.list = newCart
        
    def addToCart(self,newIngredient):
        # check if already in cart
        nameIdx = self.list.Name == newIngredient.Name
        if np.sum(nameIdx) == 1: # if == 1, then we have 1 match. 
            if (self.list.Unit[nameIdx] == newIngredient.Unit).bool():
                # ^ check for matching units
                self.list.Amount[nameIdx] += newIngredient.Amount
                self.list.Recipe[nameIdx] += ", " + newIngredient.Recipe
            else: # otherwise add separate entry
                self.list = self.list.append(newIngredient)
        elif np.sum(nameIdx) > 1: # if multiple matches, then we have an ingredient
            # with multiple entries due to differing units. 
            unitIdx = self.list.Unit == newIngredient.Unit
            matchingIdx = nameIdx & unitIdx
            if np.any(matchingIdx): #Try to add together any entries with 
                # matching units
                if np.sum(matchingIdx) > 1: # we've really messed up
                    raise ValueError("unexpected value for matchingIdx")
                self.list.Amount[matchingIdx] += newIngredient.Amount
                self.list.Recipe[matchingIdx] += ", " + newIngredient.Recipe
            else: # otherwise add another entry
                self.list = self.list.append(newIngredient)
        else:
            self.list = self.list.append(newIngredient)
    
    def returnIngredientAmount(self,ingredient_name):
        this_ing = pd.DataFrame.squeeze(self.list[self.list.Name == ingredient_name])
        print(this_ing.Amount,this_ing.Unit,"of",this_ing.Name)
        
    def sortAndPrint(self):
        # sort by name and then by category, so you have items listed 
        # alphabetically within each category
        self.list = self.list.sort_values(by=["Name"]) # sort by name
        self.list = self.list.sort_values(by=['Category']) # sort by category
        self.list = self.list.reset_index(drop=True)
        self.list.to_csv("shopping_list.csv", index=False)
    def createDefaultCart(self,colList,fname):
        print("Saving new default cart as",fname)
        pd.to_pickle(pd.DataFrame(columns = colList),fname)

def convertGenericNames(ingredients,generic_names,attr):
    ing_list = ingredients[attr]
    name_list = generic_names["Name"]
    gen_list = generic_names["Generic"]

    # finding matching indices first prevents from having to loop through every
    # ingredient and check it against the generic list - O(n) vs O(n^2)
    idx = np.where(ing_list.isin(name_list))
    if np.size(idx[0]):
        for ix in idx[0]: # this also feels wrong
            gen_ix = np.where(name_list.isin([ing_list.iloc[ix]]))
            ing_list.iloc[ix] = gen_list.iloc[gen_ix[0][0]]
            # ^ this is obviously hideous, must be better way to slice and assign.
            # Doing above because np.where returns a tuple with an array inside, and if I 
            # don't pass iloc an integer index, it won't assign correctly to just
            # the variable in the series at that index

def convertUnits(ingredient,toUnit):
    # find why type of units we're converting between (mass or volume)
    fromMass = np.any(m2m_table.ToUnits == ingredient.Unit)
    fromVol = np.any(v2v_table.ToUnits == ingredient.Unit)
    toMass = np.any(m2m_table.ToUnits == toUnit)
    toVol = np.any(v2v_table.ToUnits == toUnit)
    if fromMass and toMass: # convert between masses
        conv_table = m2m_table
    elif fromVol and toVol: # convert between volumes
        conv_table = v2v_table
    elif fromVol and not toVol: # special convert from volume
        if (v2m_table[v2m_table.Name == ingredient.Name].ToUnits == toUnit).bool():
            print("Converting",ingredient.Name,"from",ingredient.Unit,"to",toUnit) if verbose else ...
            return float(v2m_table[v2m_table.Name == ingredient.Name][ingredient.Unit])*ingredient.Amount
        else:
            # we have the ingredient listed in the special conversion table,
            # but the toUnit in the table doesn't match the toUnit passed in to
            # this function. Raise our own error because there is no KeyError otherwise
            raise ValueError("unknown special unit conversion")
    else: # special convert from mass
        if (m2v_table[m2v_table.Name == ingredient.Name].ToUnits == toUnit).bool():
            print("Converting",ingredient.Name,"from",ingredient.Unit,"to",toUnit)
            return float(m2v_table[m2v_table.Name == ingredient.Name][ingredient.Unit])*ingredient.Amount
        else:
            # we have the ingredient listed in the special conversion table,
            # but the toUnit in the table doesn't match the toUnit passed in to
            # this function. Raise our own error because there is no KeyError otherwise
            raise ValueError("unknown special unit conversion")
    
    return float(conv_table[conv_table.ToUnits == toUnit][ingredient.Unit])*ingredient.Amount
    # if the toUnit is a special unit that we haven't listed for this ingredient yet,
    # then the above line will return a key error

def loadAndFilterRecipe(recipe_name):
    ''' Load'''
    fpath = recipe_path + recipe_name + ".csv"
    ingredients = pd.read_csv(fpath, dtype={'Amount':'float64'})
    # ^ pd.read_csv will auto-select datatypes unless specified - here a recipe
    # might be converted to all int64, which would truncate future arithmetic

    ''' Filter '''
    # add category column
    ingredients["Category"] = np.nan
    # force lower case for comparisons later
    ingredients.Name = ingredients.Name.str.lower()
    # remove stop foods
    ingredients.drop(ingredients[ingredients.Name.isin(stopfoods.Name)].index)
    # convert generic names
    convertGenericNames(ingredients,generic_names,"Name")
    # convert generic units
    convertGenericNames(ingredients,generic_names,"Unit")
    # convert to common units
    # ing_to_check = ingredients[ingredients.Name.isin(grocery_units.Name)]
    # for index,ing in ing_to_check.iterrows():
    for index,ing in ingredients.iterrows():
        try:
            des_unit = grocery_units.Unit[grocery_units.Name == ing.Name].reset_index(drop=True)[0] # this fe  els like a hacky workaround - having
            # trouble getting the string value for comparison, instead of a series object (we're just grabbing the 
            # first object in the series here)
            
            # assign category to ingredient
            category = grocery_units[grocery_units.Name == ing.Name]["Category"].reset_index(drop=True)[0]
            # ^ again, hacky workaround to get string from series obj
            ingredients.Category[index] = category
            if ing.Unit != des_unit:
                try:
                    ingredients.Amount[index] = convertUnits(ing,des_unit)
                    ingredients.Unit[index] = des_unit
                except:
                    print(ing.Name,"needs special conversion") if dbug else ...
        except:
            print(ing.Name,"needs assigned category ----") if dbug else ...
            
    
    #Add recipe name
    name_series = pd.Series(recipe_name).repeat(len(ingredients))
    name_series.name = "Recipe"
    return pd.DataFrame.join(ingredients,name_series.reset_index(drop=True)) 



#%% Loop through recipe list and add ingredients to cart
shopping_cart = newCart(default_cart) # initialize Cart

active_ix = np.flatnonzero(recipe_list.Select) # get active recipes
# ^ np.argwhere does not work with numpy 1.18.1. Using flatnonzero instead
active_recipes = recipe_list.iloc[active_ix.flatten()]

for index,recipe in active_recipes.iterrows():
    print("Adding " + recipe.Name + "...") if verbose else ...
    ingredients = loadAndFilterRecipe(recipe.Name)
    for index,ingredient in ingredients.iterrows():
        # do comparison with existing list, then add to cart appropriately
        shopping_cart.addToCart(ingredient)

#%% Print out list
shopping_cart.sortAndPrint()
