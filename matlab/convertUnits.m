function ingredients = convertUnits(ingredients)

% load units table
groceryUnits = readtable('grocery_units.csv','Delimiter',',');
% load conversion table
dryTable = readtable('dry_conversion.csv','Delimiter',',');
wetTable = readtable('wet_conversion.csv','Delimiter',',');
% load dry to wet
dryToWet = readtable('dry_to_wet.csv','Delimiter',',');
% load wet to dry
wetToDry = readtable('wet_to_dry.csv','Delimiter',',');

% loop through ingredients
for i = 1:height(ingredients)
    % check if we have preferred units for this ingredient
    units_ix = ismember(groceryUnits.Name,ingredients.Name{i});
    % if we do, convert units
    if any(units_ix)
        % get units
        ing_unit = ingredients.Unit{i};
        des_unit = groceryUnits.Unit{units_ix};
        % replace label
        ingredients.Unit{i} = des_unit;
        
        % check if we are converting like to like (wet vs dry)
        dry_ing_ix = find(ismember(dryTable.RowUnits,ing_unit));
        dry_des_ix = find(ismember(dryTable.RowUnits,des_unit));
        wet_ing_ix = find(ismember(wetTable.RowUnits,ing_unit));
        wet_des_ix = find(ismember(wetTable.RowUnits,des_unit));
        both_dry = dry_ing_ix & dry_des_ix;
        both_wet = wet_ing_ix & wet_des_ix;
        % convert based on type
        if both_dry
            convFactor = dryTable.(des_unit)(dry_ing_ix);
            ingredients.Amount(i) = ingredients.Amount(i) * convFactor;
        elseif both_wet
            convFactor = wetTable.(des_unit)(wet_ing_ix);
            ingredients.Amount(i) = ingredients.Amount(i) * convFactor;
        elseif dry_ing_ix
            try
                ing_ix = ismember(dryToWet.Name,ingredients.Name{i});
                convFactor = dryToWet.(ing_unit)(ing_ix);
                ingredients.Amount(i) = ingredients.Amount(i) * convFactor;
            catch exception
                warning('%s needs special conversion\n',ingredients.Name{i})
            end   
        elseif wet_ing_ix
            try
                ing_ix = ismember(wetToDry.Name,ingredients.Name{i});
                convFactor = wetToDry.(ing_unit)(ing_ix);
                ingredients.Amount(i) = ingredients.Amount(i) * convFactor;
            catch exception
                warning('%s needs special conversion\n',ingredients.Name{i})
            end
        else % no m
%             convFactor = 1;
            warning('%s fell through the cracks\n',ingredients.Name{i})
        end
    else
        warning('%s has no preferred unit\n',ingredients.Name{i})
    end
end