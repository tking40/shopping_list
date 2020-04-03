% Recipe List
clear
cd '/Users/thomasj.king/Documents/MATLAB/shopping_list'
addpath('recipes/')
addpath('tables/')
%% Set up tables
% Load pantry
if ~exist('pantry','var')
    pantry = readtable('pantry.xlsx','Sheet',1);
end
names = string(pantry.Name);
amounts = pantry.Amount;
units = string(pantry.Unit);

% Load Recipe Table
recipe_list = readtable('pantry.xlsx','Sheet',2);

% Load stopfoods
stopfoods = readtable('stop_foods.txt','Delimiter',',');

%% Add Ingredients to Cart
% Initialize Shopping Cart
shopping_cart = readtable('shopping_cart.csv','Delimiter',',');

% Loop through recipe list and add ingredients to list
for i = 1:height(recipe_list)
    if recipe_list.Select(i) % if active recipe
        fprintf('Adding %s...\n',recipe_list.Name{i})
        % load ingredients table
        fpath = [recipe_list.Name{i},'.csv'];
        ingredients = readtable(fpath,'Delimiter',',');
        % force lower case for comparisons
        ingredients.Name = lower(ingredients.Name);
        % convert generic foodnames
        ingredients.Name = convertGenericNames(ingredients.Name);
        % convert units to grocery store units
        ingredients = convertUnits(ingredients);
        % add recipe tag to ingredients
        ingredients.Recipe(:) = recipe_list.Name(i);
        
        % Loop through ingredients to add to shopping cart
        for ing_ix = 1:height(ingredients)
            % check if ingredient is a stopfood
            if ~ismember(ingredients.Name{ing_ix},stopfoods.Name)
                shopping_cart = addToCart(shopping_cart,ingredients(ing_ix,:));
            end
        end
        
    end
end

% Print cart to file
disp('Saving to shopping_list.txt')
printShoppingCart(shopping_cart)
[sorted,sortix] = sort(shopping_cart.Name);
shopping_cart(sortix,:)

