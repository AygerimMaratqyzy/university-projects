total = int(input("Total price: "))
member = input("Member? (yes/no):")

if total >= 10000 or member == "yes":
    print("Discount applied")
else:
    print("No discount")