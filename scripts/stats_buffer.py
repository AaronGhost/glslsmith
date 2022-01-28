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

from scripts.utils.analysis_utils import attribute_compiler_results, comparison_helper
from scripts.utils.execution_utils import env_setup
from scripts.utils.file_utils import get_compiler_name, get_seed


def report_line_nb(filename):
    line_count = 0
    if os.path.isfile(filename):
        with open(filename, "r") as file:
            for line in file:
                line_count += 1
        return str(line_count)
    return "missing file"


def extract_seed_from_buffer_files(files):
    res = []
    cp_name = get_compiler_name(files[0])
    for file in files:
        if get_compiler_name(file) == cp_name:
            res.append(get_seed(file))
    return res


def stats_buffers(buffer_dir, shader_dir, compilers_dict, shader_tools, verbose):
    compiler_differences = {}
    for compiler_name in compilers_dict:
        compiler_differences[compiler_name] = 0
    compiler_differences["angle"] = 0
    compiler_differences["more than two"] = 0
    # Get a list of the files in the directory
    seeds = extract_seed_from_buffer_files(os.listdir(buffer_dir))

    print(str(len(seeds)) + " different seeds")
    for seed in seeds:
        correct_seed_buffers = []
        for compiler_name in compilers_dict:
            correct_seed_buffers.append(buffer_dir + compiler_name + "_" + seed + ".txt")
        results = comparison_helper(correct_seed_buffers)
        # Read back results from the comparison and attribute the defect to a group
        group_name = attribute_compiler_results(results, compilers_dict)
        compiler_differences[group_name] += 1

        if verbose and group_name == "more than two":
            print(list(map(lambda x: list(map(lambda y: get_compiler_name(y), x)), results)))
        # Report the number of lines for each shader
        for tool in shader_tools:
            if os.path.isfile(shader_dir + seed + tool.file_extension):

                print("Group: " + group_name + ", lines: " + report_line_nb(
                    shader_dir + seed + tool.file_extension) + ", seed: " + seed)
                break

    # Print a summary
    print("========= SUMMARY ================================================================")
    for compiler_name in compilers_dict:
        print(compiler_name + " different values: " + str(compiler_differences[compiler_name]))
    print("angle different values: " + str(compiler_differences["angle"]))
    print("more than two groups of values: " + str(compiler_differences["more than two"]))


def main():
    parser = argparse.ArgumentParser(description="Print stats and info about difference showing buffers")
    parser.add_argument('--verbose', dest="verbose", action="store_true", help="Gives the detail of agreeing compiler "
                                                                               "for non-trivial case")

    ns, exec_dirs, compilers_dict, _, shader_tools = env_setup(parser)
    stats_buffers(exec_dirs.keptbufferdir, exec_dirs.keptshaderdir, compilers_dict, shader_tools, ns.verbose)


if __name__ == "__main__":
    main()
