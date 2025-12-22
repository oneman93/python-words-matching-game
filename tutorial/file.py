import os

txt_filepath = "demofile.txt"

print()
with open(txt_filepath, "a") as f:
    f.writelines("Now the file has more content!")

print("\n")
with open(txt_filepath, "r") as f:
    print(f.read(5))

print("\n")
with open(txt_filepath, "r") as f:
    print(f.read())

if os.path.exists(txt_filepath):
    os.remove(txt_filepath)
    print(txt_filepath + " is not removed")
else:
    print("the file does not exist")
