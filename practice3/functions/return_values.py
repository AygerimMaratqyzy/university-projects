def total(*prices,**options):
    total = sum(prices)

    if "discount" in options:        #apply discount
        total -=options["discount"]
    
    if "tax" in options:                #apply tax
        total += total * options["tax"]

    return total

r = total(100,50,25,discount = 20,tax = 0.2)
print(r)