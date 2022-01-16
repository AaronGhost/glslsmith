def load_file(filename):
    with open("testdata/" + filename, "r") as file:
        return file.read()
