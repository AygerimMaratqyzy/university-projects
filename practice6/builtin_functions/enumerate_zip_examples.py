names = ["Aigerim","Aya","Malika"]
scores = [85,90,78]

print("Using enumerate():")
for i,n in enumerate(names,start = 1):
    print(f"{i}. {n}")

print("\nUsing zip():")
pairs = list(zip(names,scores))
print(pairs)

for name,score in zip(names,scores):
    print(f"{name} scored {score}")

val = "123"                            #type checking
print("\nType before: ",type(val))

converted_val = int(val)
print("\nType after conversion: ",type(converted_val))   #type conversion

num = 18956
print("Convert int to string:  ",str(num))
print("Convert to float: ",float(num))