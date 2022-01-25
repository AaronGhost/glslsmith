# Copyright 2021 The glslsmith Project Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Counts the number of time a file is called")
    parser.add_argument("--log", dest="log", default="log.txt", help="specify the log file")
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
    g.write(str(file_call + 1))
    g.close()


if __name__ == '__main__':
    main()
