function shopping_cart = addToCart(shopping_cart,ingredient)

% if shopping cart empty
if isempty(shopping_cart)
    % create new list item
    shopping_cart = vertcat(shopping_cart,ingredient);
else
    % get ix of ingredient in shopping cart, if it exists
    cart_ix = ismember(shopping_cart.Name,ingredient.Name{1});

    % if it does exist in cart
    if any(cart_ix)
        % check if ingredient units match
        cart_unit = shopping_cart.Unit{cart_ix};
        ing_unit = ingredient.Unit{1};
        if strcmp(cart_unit,ing_unit) && sum(cart_ix)  == 1
            % merge the amounts & update cart
            shopping_cart.Amount(cart_ix) = shopping_cart.Amount(cart_ix) ...
                + ingredient.Amount;
            try
            shopping_cart.Recipe{cart_ix} = [shopping_cart.Recipe{cart_ix},...
                ',',ingredient.Recipe{1}];
            catch exception
                
            end
        else
            % add separate line to highlight difference in expected units
            shopping_cart = vertcat(shopping_cart,ingredient);
        end
    else
        % create new list item
        shopping_cart = vertcat(shopping_cart,ingredient);
    end
end

end