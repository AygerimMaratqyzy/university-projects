f = open("sample_data.txt")
print("      Full Data       ")
print(f.read())

f = open(r"C:\Users\Asus\pp2\work\practice6\file_handling\sample_data.txt")
print("      Full Data       ")
print(f.read())

with open("sample_data.txt") as f:
    print("\n     Line by Line     ")
    print(f.readline())

with open("sample_data.txt") as f:
    print("\n     First 15 characters     ")
    print(f.read(15))
