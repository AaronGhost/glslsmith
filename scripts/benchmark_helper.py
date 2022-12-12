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
from datetime import datetime


def count_calls(log_file):
    if os.path.isfile(log_file):
        # Read current log file status (started reduction time and number of calls)
        with open(log_file, "r") as f:
            logs = f.readlines()
            start_timestamp = logs[0].strip("\n")
            file_calls = logs[1].strip("\n")
    else:
        # Give the current time as the reduction start time and prepare to write down the call numbers
        start_timestamp = str(int(round(datetime.timestamp(datetime.now()))))
        file_calls = 0
    # Rewrite to the file
    with open(log_file, "w") as f:
        f.write(start_timestamp + "\n")
        f.write(str(int(file_calls) + 1) + "\n")
        f.write(str(int(round(datetime.timestamp(datetime.now())))))


def main():
    parser = argparse.ArgumentParser(description="Counts the number of time a file is called")
    parser.add_argument("--log", dest="log", default="log.txt", help="specify the log file")
    ns = parser.parse_args(sys.argv[1:])
    count_calls(ns.log)


if __name__ == '__main__':
    main()
