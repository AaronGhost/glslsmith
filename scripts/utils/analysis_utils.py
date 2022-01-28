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

import filecmp

from scripts.utils.file_utils import get_compiler_name


def comparison_helper(files):
    comparison_values = []
    for file in files:
        comparison_values.append([file])
    i = 0
    while i < len(comparison_values) - 1:
        reference = comparison_values[i]
        for next_files in comparison_values[i + 1:]:
            if next_files != reference[0]:
                if filecmp.cmp(reference[0], next_files[0], False):
                    reference += next_files
                    comparison_values.remove(next_files)
        i += 1

    return comparison_values


def attribute_compiler_results(results, compilers_dict):
    # A single compiler disagrees with the others (can be attributed to one compiler)
    if len(results) == 2:
        if len(results[0]) == 1 or len(results[1]) == 1:
            if len(results[0]) == 1:
                return get_compiler_name(results[0][0])
            else:
                return get_compiler_name(results[1][0])
        # A family of compilers disagrees (Angle)
        if (all(compilers_dict[get_compiler_name(buffer_name)].type == "angle"
                for buffer_name in results[0])
            and all(compilers_dict[get_compiler_name(buffer_name)].type == "independent"
                    for buffer_name in results[1])) \
                or (all(compilers_dict[get_compiler_name(buffer_name)].type == "angle"
                        for buffer_name in results[1])
                    and all(compilers_dict[get_compiler_name(buffer_name)].type == "independent"
                            for buffer_name in results[0])):
            return "angle"
    # Something else is happening
    return "more than two"