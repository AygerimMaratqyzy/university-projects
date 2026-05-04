fruits = ["apple", "banana", "cherry", "kiwi", "orange"]
for fruit in fruits:
    if "a" not in fruit:
        print(f"Skipping {fruit}, no 'a' in it")
        continue
    print(f"Processing {fruit}")