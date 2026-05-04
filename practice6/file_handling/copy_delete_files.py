import shutil 
import os

src_file = "sample_data.txt"
bckp_file = "sample_data_backup.txt"

shutil.copy(src_file,bckp_file)
print("Backup created")

delete_file = "temp.txt"              

with open(delete_file,"w") as f:
    f.write("Temporary file")

if os.path.exists(delete_file):        #check if the file exists
    os.remove(delete_file)
    print("File deleted successfully.")
else:
    print("File does not exist.")