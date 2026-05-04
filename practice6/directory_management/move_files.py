import shutil
import os

source_file = "../file_handling/sample_data.txt"

os.makedirs("data/students", exist_ok = True)
os.makedirs("data/archive", exist_ok = True)

d_copy = "data/students/students_copy.txt"
shutil.copy(source_file,d_copy)
print("File copied to data/students/")

d_move = "data/archive/students_moved.txt"
shutil.move(source_file,d_move)
print("File moved to data/archive/")

print("\n     Files in data/students     ")
print(os.listdir("data/students"))

print("\n     Files in data/archive      ")
print(os.listdir("data/archive"))