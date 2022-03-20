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

import os
import re


def concatenate_files(outputname, files):
    out = b''
    for fileadd in files:
        if 'buffer' in fileadd:
            with open(fileadd, 'rb') as f:
                out += f.read()
    with open(outputname, 'wb') as dumpfile:
        dumpfile.write(out)


def clean_files(current_dir, files_list):
    ref = os.getcwd()
    os.chdir(current_dir)
    for file in files_list:
        if os.path.isfile(file):
            os.remove(file)
    os.chdir(ref)


def find_file(current_dir, regex_pattern=""):
    regex = re.compile(regex_pattern)
    file_list = os.listdir(current_dir)
    buffer_files = []
    if current_dir[-1] != "/":
        current_dir += "/"
    for file in file_list:
        if os.path.isfile(current_dir + file) and regex.match(file):
            buffer_files.append(file)
    return buffer_files


def find_digit_buffer_file(current_dir):  # pragma: no cover
    return find_file(current_dir, "buffer_[0-9]+")


def find_buffer_file(current_dir):  # pragma: no cover
    return find_file(current_dir, "buffer_")


def find_test_file(current_dir):  # pragma: no cover
    return find_file(current_dir, "test")


def get_compiler_name(buffer_name):
    return buffer_name.split("/")[-1].rsplit("_", 1)[0]


def get_seed(buffer_name):
    return buffer_name.split("/")[-1].rsplit("_", 1)[1].split(".")[0]


def ensure_abs_path(root_dir, test_dir):
    # Return test_dir if absolute or an absolute path using the root_dir
    if os.path.isabs(test_dir):
        return test_dir
    else:
        return os.path.normpath(os.path.join(root_dir, test_dir)) + "/"
