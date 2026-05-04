file_path = r"C:\Users\Asus\pp2\work\practice6\file_handling\sample_data.txt"

with open(file_path,"a") as f:          #Append data to the file
    f.write("Charlie Brown,19,78\n")
    f.write("Diana Ross,21,92\n")

with open(file_path) as f:
    print("\n     Current File Content     ")
    print(f.read())

