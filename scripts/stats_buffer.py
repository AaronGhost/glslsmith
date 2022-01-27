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

import common


def report_line_nb(filename):
    line_count = 0
    if os.path.isfile(filename):
        with open(filename, "r") as file:
            for line in file:
                line_count += 1
        return str(line_count)
    return "missing file"


def get_compiler_name(buffer_name):
    return buffer_name.split("/")[-1].rsplit("_", 1)[0]


def get_seed(buffer_name):
    return buffer_name.split("/")[-1].rsplit("_", 1)[1].split(".")[0]


def extract_seed_from_buffer_files(files):
    res = []
    cp_name = get_compiler_name(files[0])
    for file in files:
        if get_compiler_name(file) == cp_name:
            res.append(get_seed(file))
    return res


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
        results = common.comparison_helper(correct_seed_buffers)
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

    ns, exec_dirs, compilers_dict, _, shader_tools = common.env_setup(parser)
    stats_buffers(exec_dirs.keptbufferdir, exec_dirs.keptshaderdir, compilers_dict, shader_tools, ns.verbose)


if __name__ == "__main__":
    main()
