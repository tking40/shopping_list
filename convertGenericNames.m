function names = convertGenericNames(names)

% load generic name table
generic_names = readtable('generic_names.csv','Delimiter',',');

% loop through ingredients
for i = 1:length(names)
    name_ix = ismember(generic_names.Name,names(i));
    if any(name_ix)
        names(i) = generic_names.Generic(name_ix);
    end
end

end