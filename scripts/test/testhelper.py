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

def load_file(filename):
    with open("testdata/" + filename, "r") as file:
        return file.read()


def compare_files(file_name, ref_name):
    file_rows = open(file_name).readlines()
    ref_rows = open(ref_name).readlines()
    row_index = 0
    for row in file_rows:
        assert row == ref_rows[row_index]
        row_index += 1
    assert len(ref_rows) == len(file_rows)


def restrict_compilers(compiler_dict, name_list):
    resulting_compilers = dict()
    for name in name_list:
        if name in compiler_dict:
            resulting_compilers[name] = compiler_dict[name]
    return resulting_compilers
