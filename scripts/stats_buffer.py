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
import argparse
from subprocess import run
import common


def report_line_nb(seed, dir):
    if os.path.isfile(dir + str(seed) + ".shadertrap"):
        cmd = ["wc", "-l", dir + str(seed) + r".shadertrap"]
        process_return = run(cmd, capture_output=True, text=True)
        return process_return.stdout.split()[0]
    else:
        return "missing"


def get_compiler_name_from_buffer(buffer_name):
    return buffer_name.split("/")[-1].split("_")[0]


def main():
    parser = argparse.ArgumentParser(description="Print stats and info about difference showing buffers")
    parser.add_argument('--report-seed', dest='compilers', default=[], nargs="+",
                        help="Provide the compilers for which the seed number and the shader length will be reported, "
                             "pass all to get the values for all compilers, and more_than_two for non-trivial case")
    parser.add_argument('--verbose', dest="verbose", action="store_true", help="Gives the detail of agreeing compiler "
                                                                               "for non-trivial case")

    ns, exec_dirs, compilers_dict, _, shader_tool = common.env_setup(parser)

    # Store names for the difference calculation
    compiler_differences = {}
    for compiler_name in compilers_dict:
        compiler_differences[compiler_name] = 0
    compiler_differences["angle"] = 0
    compiler_differences["more_than_two"] = 0
    # Get a list of the files in the directory
    file_list = os.listdir(exec_dirs.keptbufferdir)
    seeds = []
    any_name = next(iter(compilers_dict))
    for file in file_list:
        termination = file.split("_")[-1]
        compiler_radix = file.replace("_" + termination, "")
        if any_name == compiler_radix:
            seeds.append(termination.split(".")[0])

    print(str(len(seeds)) + " different seeds")
    for seed in seeds:
        correct_seed_buffers = []
        for compiler_name in compilers_dict:
            correct_seed_buffers.append(exec_dirs.keptbufferdir + compiler_name + "_" + seed + ".txt")
        results = common.comparison_helper(correct_seed_buffers)
        # Read back results from the comparison
        if len(results) == 2:
            if len(results[0]) == 1 or len(results[1]) == 1:
                if len(results[0]) == 1:
                    compiler_name = get_compiler_name_from_buffer(results[0][0])
                else:
                    compiler_name = get_compiler_name_from_buffer(results[1][0])
                if compiler_name in ns.compilers or "all" in ns.compilers:
                    print(compiler_name + ", lines: " + report_line_nb(seed,
                                                                       exec_dirs.keptshaderdir) + ", seed: " + seed)
                compiler_differences[compiler_name] += 1
                continue

            # Try if we are in the angle case
            if (all(compilers_dict[get_compiler_name_from_buffer(buffer_name)].type == "angle"
                    for buffer_name in results[0])
                and all(compilers_dict[get_compiler_name_from_buffer(buffer_name)].type == "independent"
                        for buffer_name in results[1])) \
                    or (all(compilers_dict[get_compiler_name_from_buffer(buffer_name)].type == "angle"
                            for buffer_name in results[1])
                        and all(compilers_dict[get_compiler_name_from_buffer(buffer_name)].type == "independent"
                                for buffer_name in results[0])):
                if "angle" in ns.compilers or "all" in ns.compilers:
                    print("angle" + ", lines: " + report_line_nb(seed, exec_dirs.keptshaderdir) + ", seed: " + seed)
                compiler_differences["angle"] += 1
                continue

        # Everything else where a cause is difficult to identify
        compiler_differences["more_than_two"] += 1
        if "more_than_two" in ns.compilers or "all" in ns.compilers:
            print("More than two different values, lines: " + report_line_nb(seed, exec_dirs.keptshaderdir)
                  + ", seed: " + seed)
        if ns.verbose:
            if len(results) == len(compilers_dict):
                print("all compilers disagree\n")
            else:
                compilers_text = ""
                for agreeing_compilers in results:
                    for buffer_name in agreeing_compilers:
                        compilers_text += get_compiler_name_from_buffer(buffer_name) + ", "
                    compilers_text = compilers_text[:-2]
                    compilers_text += " compilers agree, "
                compilers_text = compilers_text[:-2]
                print(compilers_text + "\n")

    for compiler_name in compilers_dict:
        print(compiler_name + " different values: " + str(compiler_differences[compiler_name]))
    print("angle different values: " + str(compiler_differences["angle"]))
    print("more than two groups of values: " + str(compiler_differences["more_than_two"]))


if __name__ == "__main__":
    main()
