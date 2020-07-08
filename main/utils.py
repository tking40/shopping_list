#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 18:58:54 2020

@author: thomasj.king
"""


""" Recipe Utilities"""

import pandas as pd
import numpy as np
import re
from fractions import Fraction
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import inflection as inf

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
        # self.list = self.list.sort_values(by=['Category']) # sort by category
        self.list = self.list.reset_index(drop=True)
        self.list.to_csv("shopping_list.csv", index=False)
    def createDefaultCart(self,colList,fname):
        print("Saving new default cart as",fname)
        pd.to_pickle(pd.DataFrame(columns = colList),fname)


            

def convertGenericNames(ingredients,generic_names,attr):
    r'''
    Convert known ingredient names to generic equivalents.
    
    This function converts known names to generic names by finding entries in 
    ingredients.atrr that match exactly to the names in the generic_names.Name 
    series. Conversion is done by locating index of the name in the series, and 
    then replacing ingredient name with the value of generic_names.Generic at 
    that index. This function is solely used when parsing recipes from
    [root]/python/recipes/. 

    Parameters
    ----------
    ingredients : pandas.core.frame.DataFrame (n,3)
        DF of n ingredients to convert. Columns = {"Name","Amount","Unit"}
    generic_names : pandas.core.frame.DataFrame (m,2)
        Lookup table matching m possible names to m generic names.
    attr : str
        Attribute to match (either "Name" or "Unit").

    Returns
    -------
    None.
    
    Examples
    --------
    >>> import pandas as pd
    >>> table_path = root + "python/tables/"
    >>> ingredients_lookup = pd.read_csv(table_path + "ingredients_lookup.csv")
    >>> units_lookup = pd.read_csv(table_path + "units_lookup.csv")
    >>> ingList,dirList = loadURL(recipe.Address)
    >>> ingredients = parseIngredients(ingList,ingredients_lookup,units_lookup)
    >>> ingredients_generic = convertGenericNames(ingredients, ingredients_lookup, "Name")

    '''
    ing_list = ingredients[attr]
    name_list = generic_names["Name"]
    gen_list = generic_names["Generic"]
    
    # finding matching indices first prevents from having to loop through every
    # ingredient and check it against the generic list - O(n) vs O(n^2)
    idx = np.where(ing_list.isin(name_list))
    if np.size(idx[0]): # if not empty (we have any matches)
        for ix in idx[0]:
            gen_ix = np.where(name_list.isin([ing_list.iloc[ix]]))
            ing_list.iloc[ix] = gen_list.iloc[gen_ix[0][0]]
            # ^ this is obviously hideous, must be better way to slice and assign.
            # Doing above because np.where returns a tuple with an array inside, and if I 
            # don't pass iloc an integer index, it won't assign correctly to just
            # the variable in the series at that index

def convertUnits(ingredient,toUnit,conv_tables,verbose=False):
    r'''
    Convert between units of different types.
    
    This function takes in an ingredient, the desired unit, and converts 
    between the current and desired unit using conv_tables. 

    Parameters
    ----------
    ingredient : pandas.core.series.Series, (1,)
        Single-element series which contains ingredient name, amount, unit, 
        category, and recipe.
    toUnit : str
        Desired unit for conversion.
    conv_tables : list (4,)
        List containing tables for 4 different types of unit conversions:
            v2v_table: pandas.core.frame.DataFrame
                volume to volume conversions
            m2m_table: pandas.core.frame.DataFrame
                mass to mass conversions
            v2m_table:pandas.core.frame.DataFrame
                volume to mass conversions
            m2v_table: pandas.core.frame.DataFrame
                mass to volume conversions   
    verbose : bool {True, False} , optional
        Flag for informational print statements.

    Raises
    ------
    KeyError
        Raised if we have an ingredient listed in the special conversion table,
        but the toUnit in the table doesn't match the toUnit passed into this
        function. Does not raise KeyError otherwise.

    Returns
    -------
    float
        Converted ingredient amount.
    
    Example
    -------
    >>> import pandas as pd
    >>> ingredient = pd.Series(["heavy whipping cream",0.5,"cups","dairy",
                "Tikka Masala"],["Name","Amount","Unit","Category","Recipe"])
    >>> toUnit = "fluid_oz"
    >>> v2v_table = pd.read_csv(table_path + "volume_to_volume.csv")
    >>> m2m_table = pd.read_csv(table_path + "mass_to_mass.csv")
    >>> v2m_table = pd.read_csv(table_path + "volume_to_mass.csv")
    >>> m2v_table = pd.read_csv(table_path + "mass_to_volume.csv")
    >>> conv_tables = [v2v_table,m2m_table,v2m_table,m2v_table]
    >>> new_amount = convertUnits(ingredient, toUnit, conv_tables)

    '''
    # find what type of units we're converting between (mass or volume)
    v2v_table,m2m_table,v2m_table,m2v_table = conv_tables # extract tables
    
    fromMass = np.any(m2m_table.ToUnits == ingredient.Unit)
    fromVol = np.any(v2v_table.ToUnits == ingredient.Unit)
    toMass = np.any(m2m_table.ToUnits == toUnit)
    toVol = np.any(v2v_table.ToUnits == toUnit)
    if fromMass and toMass: # convert between masses
        conv_table = m2m_table
    elif fromVol and toVol: # convert between volumes
        conv_table = v2v_table
    elif fromVol and toMass: # special convert from volume
        if (v2m_table[v2m_table.Name == ingredient.Name].ToUnits == toUnit).bool():
            print("Converting",ingredient.Name,"from",ingredient.Unit,"to",toUnit) if verbose else ...
            return float(v2m_table[v2m_table.Name == ingredient.Name][ingredient.Unit])*ingredient.Amount
        else:
            # we have the ingredient listed in the special conversion table,
            # but the toUnit in the table doesn't match the toUnit passed in to
            # this function. Raise our own error because there is no KeyError otherwise
            raise KeyError("unknown special unit conversion")
    else: # special convert from mass
        if (m2v_table[m2v_table.Name == ingredient.Name].ToUnits == toUnit).bool():
            print("Converting",ingredient.Name,"from",ingredient.Unit,"to",toUnit) if verbose else ...
            return float(m2v_table[m2v_table.Name == ingredient.Name][ingredient.Unit])*ingredient.Amount
        else:
            # we have the ingredient listed in the special conversion table,
            # but the toUnit in the table doesn't match the toUnit passed in to
            # this function. Raise our own error because there is no KeyError otherwise
            raise KeyError("unknown special unit conversion")
    
    return float(conv_table[conv_table.ToUnits == toUnit][ingredient.Unit])*ingredient.Amount
    # if the toUnit is a special unit that we haven't listed for this ingredient yet,
    # then the above line will return a key error


def loadAndFilterRecipe(recipe,recipe_path,name_tables,conv_tables,verbose=False,dbug=True):
    r'''
    Load and filter ingredients for given recipe.
    
    This function takes in recipe descriptor and either loads from URL or text
    file, and then parses accordingly. Then assigns category and recipe to each
    ingredient before returning filtered ingredients list.

    Parameters
    ----------
    recipe : pandas.core.series.Series, (1,)
        Single-element series containing recipe descriptors.
    recipe_path : str
        Location of recipe files.
    name_tables : list(4,)
        List containing lookup tables for name removal and conversion.
    conv_tables : list (4,)
        List containing tables for 4 different types of unit conversions.
    verbose : bool {True, False} , optional
        Flag for informational print statements. The default is False.
    dbug : bool {True, False} , optional
        Flag for print statements related to debugging. The default is True.

    Returns
    -------
    pandas.core.frame.DataFrame (n,5)
        Dataframe containing n ingredients with 5 Columns: {"Name","Unit",
        "Amount","Category","Recipe"}
    
    Example
    --------
    >>> import pandas as pd
    >>> table_path = root + "python/tables/"
    >>> url_list = pd.read_csv(table_path + "url_list.txt")
    >>> recipe = url_list.iloc[0]
    >>> recipe_path = root + "python/recipes/"
    >>> stopfoods = pd.read_csv(table_path + "stop_foods.txt")
    >>> ingredients_lookup = pd.read_csv(table_path + "ingredients_lookup.csv")
    >>> units_lookup = pd.read_csv(table_path + "units_lookup.csv")
    >>> grocery_units = pd.read_csv(table_path + "grocery_units.csv")
    >>> name_tables = [stopfoods,ingredients_lookup,units_lookup,grocery_units]
    >>> v2v_table = pd.read_csv(table_path + "volume_to_volume.csv")
    >>> m2m_table = pd.read_csv(table_path + "mass_to_mass.csv")
    >>> v2m_table = pd.read_csv(table_path + "volume_to_mass.csv")
    >>> m2v_table = pd.read_csv(table_path + "mass_to_volume.csv")
    >>> conv_tables = [v2v_table,m2m_table,v2m_table,m2v_table]
    >>> ingredients = loadAndFilterRecipe(recipe,recip_path,name_tables,conv_tables)

    '''
    
    
    # extract tables
    stopfoods,ingredients_lookup,units_lookup,grocery_units = name_tables
    
    isURL = "Address" in recipe # boolean check on recipe type
    
    # load recipes
    if isURL:
        ingList,dirList = loadURL(recipe.Address)
        print(ingList) if dbug else ...
        ingredients = parseIngredients(ingList,ingredients_lookup,units_lookup)
    else:
        fpath = recipe_path + recipe.Name + ".csv"
        ingredients = pd.read_csv(fpath, dtype={'Amount':'float64'})
        # ^ pd.read_csv will auto-select datatypes unless specified - here a recipe
        # might be converted to all int64, which would truncate future arithmetic
        # force lower case for comparisons later
        ingredients.Name = ingredients.Name.str.lower()
        # convert generic names
        convertGenericNames(ingredients,ingredients_lookup,"Name")
        # convert generic units
        convertGenericNames(ingredients,units_lookup,"Unit")
        

    ''' Filter '''
    
    # add category column
    ingredients["Category"] = np.nan 
    # remove stop foods
    ingredients = ingredients.drop(ingredients[ingredients.Name.isin(stopfoods.Name)].index)
    
    for index,ing in ingredients.iterrows():
        try:
            # match ingredient to table
            match = grocery_units[grocery_units.Name == ing.Name]
            
            # get desired unit
            des_unit = match["Unit"].values[0]
            
            # assign category to ingredient
            category = match["Category"].values[0]
            ingredients.Category[index] = category
            
            if ing.Unit != des_unit:
                try:
                    ingredients.Amount[index] = convertUnits(ing,des_unit,conv_tables,verbose)
                    ingredients.Unit[index] = des_unit
                except:
                    print(ing.Name,"needs special conversion") if dbug else ...
        except:
            print(ing.Name,"needs assigned category ----") if dbug else ...
            
    
    #Add recipe name
    name_series = pd.Series(recipe.Name).repeat(len(ingredients))
    name_series.name = "Recipe"
    return pd.DataFrame.join(ingredients.reset_index(drop=True),name_series.reset_index(drop=True)) 

def myIsNumber(x):
    r'''
    Check if number, return float if so.
    
    This function checks if input string is a number. Trys to convert to float,
    or convert to fraction and then float. If unsuccessful, returns False.

    Parameters
    ----------
    x : str
        String for number checking.

    Returns
    -------
    float OR bool
        Returns float if number is found. Otherwise, returns False.

    '''
    # this is a goddamn mess and I don't care
    try:
        return float(x)
    except:
        try:
            return float(Fraction(x))
        except:
            try:
                return float(Fraction(x.replace(chr(8260),"/")))
            except:
                return False

def matchIngredient(ingName,genNames,dbug=True):
    r'''
    Find matching ingredient name and return generic name.
    
    This function uses the genName lookup table to find the matching ingredient
    name in the genNames.Name series. Then returns the matching generic name. 
    Finds matching ingredient by scoring names in series - 1 point for every
    matching word. Then matching name is the one with the most points. If
    multiple matches found, will return match name with shortest length (flour
    matches equally to flour and flour tortillas, but the former is correct).

    Parameters
    ----------
    ingName : str
        Ingredient name.
    genNames : pandas.core.frame.DataFrame (n,2)
        Lookup table of n names and n corresponding generic names.
    dbug : bool {True,False}, optional
        Flag for print statements related to debugging. The default is True.

    Returns
    -------
    str
        Matching generic ingredient name.

    '''
    
    # get words from ingredient phrase
    ingWords = TextBlob(ingName).words.lower()
    # singularize using inflection (textblob is bad at this)
    ingWords = [inf.singularize(word) for word in ingWords]
    singGenNames = [inf.singularize(word) for word in genNames.Name]
    # score each ingredient based on matching words with generic names
    # here we're comparing whole words after we've singularized them
    score = [len([None for ingWord in ingWords if ingWord in genName.split()]) for genName in singGenNames]
    # get max score
    maxval = max(score)
    # if we have multiple maxima, we need to do some more calculations
    # example: 'flour' matches 'flour' and 'flour tortilla' equally
    if maxval == 0:
        print(ingName,"has no matches") if dbug else ...
        return ingName
    elif score.count(maxval) > 1: 
        # find indices of maxima
        ix = [i for i,s in enumerate(score) if s == maxval]
        # get character length of matching generic names
        counts = [len(singGenNames[i]) for i in ix]
        # if we have multiple matching names with equal length, then we need
        # to refine our generic names list
        matchingNames = [singGenNames[i] for i in ix]
        print(ingName,"matches",matchingNames,"equally") if dbug else ...
        if counts.count(min(counts)) > 1:
            print("could not find best match") if dbug else ...
            return ingName
        # otherwise, assume that smallest matching name is the one we want
        else:
            matchedIng = genNames.Generic[ix[counts.index(min(counts))]]
            print(ingName,"matches best to",matchedIng) if dbug else ...
            return matchedIng
    # if 1 maximum, we've found the matching ingredient
    else:
        matchedIng = genNames.Generic[score.index(maxval)]
        print(ingName,"matches to",matchedIng) if dbug else ...
        return matchedIng

def matchUnit(ingName, genNames, dbug=True):
    r'''
    Find matching unit name and return generic name.
    
    This function uses the genName lookup table to find the matching unit
    name in the genNames.Name series. Then returns the matching generic name. 
    Finds matching unit by scoring names in series - 1 point for every
    matching word. Then matching name is the one with the most points. If
    multiple matches found, will return match that occurs first in input 
    ingName string.

    Parameters
    ----------
    ingName : str
        Ingredient name.
    genNames : pandas.core.frame.DataFrame (n,2)
        Lookup table of n names and n corresponding generic names.
    dbug : bool {True,False}, optional
        Flag for print statements related to debugging. The default is True.

    Returns
    -------
    str
        Matching generic unit name.
        

    '''
    # get words from ingredient phrase
    ingWords = TextBlob(ingName).words.lower()
    # score each word in ingredient name with generic units
    score = [len([None for ingWord in ingWords if ingWord in genName.split()]) for genName in genNames.Name]
    # get max score
    maxval = max(score)
    
    if maxval == 0:
        print("no units found for",ingName) if dbug else ...
        return "units"
    else:
        # if 1 maxval, we found unit. If multiple maxvals, we assume first
        # unit found is correct. Operation is the same here either way
        return genNames.Generic[score.index(maxval)]
    

def parseIngredients(ingList,ingredients_lookup,units_lookup,dbug=True):
    r'''
    Parse ingredients list into common names and units and output as DataFrame.
    
    This function parses the name string for each ingredient in ingList and
    returns a DataFrame with the name, amount, and unit for each.

    Parameters
    ----------
    ingList : list (n,)
        List of n ingredient strings.
    ingredients_lookup : pandas.core.frame.DataFrame (m,2)
        Lookup table of m ingredient names and n corresponding generic names.
    units_lookup : pandas.core.frame.DataFrame (k,2)
        Lookup table of k unit names and n corresponding generic names.
    dbug : bool {True,False}, optional
        Flag for print statements related to debugging. The default is True.

    Returns
    -------
    pandas.core.frame.DataFrame (n,3)
        Ingredients DataFrame with columns: {"Name","Amount","Unit"}

    '''
    newList = []
    for ingName in ingList:
        # remove parens
        ingName = re.sub("[\(\[].*?[\)\]]","",ingName)
        # get name
        name = matchIngredient(ingName,ingredients_lookup,dbug)
        # get amount
        numbers = [myIsNumber(word) for word in ingName.split() if myIsNumber(word)]
        amount = np.sum(numbers)
        # get units
        unit = matchUnit(ingName,units_lookup,dbug)
        
        newList.append([name,amount,unit])
    return pd.DataFrame(newList,columns=["Name","Amount","Unit"])

def loadURL(URL):
    r'''
    Loads recipe from URL.
    
    This function uses beautiful soup to read in URL content and then find 
    ingredients and directions lists based on specified format for each website.

    Parameters
    ----------
    URL : str
        Recipe URL.

    Returns
    -------
    ingredients : list (n,)
        List of n ingredient strings.
    directions : list, (m,)
        List of m directions strings.

    '''
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    isWordPress = soup.find("div", {"class": "wprm-recipe-ingredient-group"})
    if isWordPress:
        raw_ingredients = soup.find("div", {"class": "wprm-recipe-ingredient-group"})
        raw_directions = soup.find("div", {"class": "wprm-recipe-instruction-group"})
        ingTok = 'li'
        dirTok = 'li'
    if "food.com" in URL:
        raw_directions = soup.find("div", {"class": "recipe-layout__directions"})
        raw_ingredients = soup.find("div", {"class": "recipe-layout__ingredients"})
        ingTok = 'li'
        dirTok = 'li'
    elif "bonappetit" in URL:
        raw_ingredients = soup.find("div", {"class": "ingredientsGroup"})
        raw_directions = soup.find("div", {"class": "steps-wrapper"})
        ingTok = 'li'
        dirTok = 'li'
    elif "allrecipes" in URL or "marthastewart" in URL:
        raw_ingredients = soup.find("fieldset", {"class": "ingredients-section__fieldset"})
        raw_directions = soup.find("fieldset", {"class": "instructions-section__fieldset"})
        ingTok = 'li'
        dirTok = 'li'
    elif "foodnetwork" in URL:
        raw_ingredients = soup.find("section", {"class": "o-Ingredients"})
        raw_directions = soup.find("section", {"class": "o-Method"})
        ingTok = 'p'
        dirTok= 'li'
    elif "camelliabrand" in URL:
        raw_ingredients = soup.find("div", {"class": "ingredients"})
        raw_directions = soup.find("div", {"class": "e-instructions instructions"})
        ingTok = 'li'
        dirTok = 'li'
    elif "nytimes" in URL:
        raw_ingredients = soup.find("section", {"class": "recipe-ingredients-wrap"})
        raw_directions = soup.find("section", {"class": "recipe-steps-wrap"})
        ingTok = 'li'
        dirTok = 'li'
    
    ingredients = [x.get_text().strip()
               for x in raw_ingredients.find_all(ingTok)]
    directions = [x.get_text().strip()
               for x in raw_directions.find_all(dirTok)]

    return ingredients,directions

#%% Test
# root = "C:/Users/Thomas/Documents/MATLAB/shopping_list/"
# ingName = "15 oz. tomato sauce ($0.50)"
# table_path = root + "python/tables/"
# units_lookup = pd.read_csv(table_path + "units_lookup.csv")
# matchUnit(ingName,units_lookup)
URL = "https://www.camelliabrand.com/recipes/instant-pot-new-orleans-style-red-beans-and-rice/"
loadURL(URL)