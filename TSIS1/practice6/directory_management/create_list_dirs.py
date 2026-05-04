import os

os.makedirs("data/students/archive",exist_ok = True) #Creates nested directories
print("Nested directories created")

print("\n     Current Directory Content     ")       #Lists all files inside 'data' folder
for i in  os.listdir("data"):
    print(i)

print("\n     .txt Files     ") 
files = [f for f in os.listdir("../file_handling") if f.endswith(".txt")]
for f in files:
    print(f)
