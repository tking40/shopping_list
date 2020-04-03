function printShoppingCart(shopping_cart)

fh = fopen('shopping_list.txt','w');
% fh = 1;

for i =  1:height(shopping_cart)
    name = shopping_cart.Name{i};
    amount = shopping_cart.Amount(i);
    unit = shopping_cart.Unit{i};
    fprintf(fh,'%g\t%s\tof %s\n',amount,unit,name);
end

fclose(fh);

end