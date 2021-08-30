import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Counts the number of time a file is called")
    parser.add_argument("--log", dest="log", default="log.txt")
    ns = parser.parse_args(sys.argv[1:])
    count_calls(ns.log)


def count_calls(log_file):
    file_call = 0
    if os.path.isfile(log_file):
        f = open(log_file, "r")
        file_call = int(f.readline())
        f.close()

    # Rewrite to the file
    g = open(log_file, "w")
    g.write(str(file_call+1))
    g.close()


if __name__ == '__main__':
    main()
