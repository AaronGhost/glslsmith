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

import common

# Internal error code on exit have been distributed as follow
# Compiler codes are defined by the order of the compiler in the config file and only the first to fail is reported
# crash / execution error: 1000 + compiler code
# timeout: 2000 + compiler code
# Miscompilation on one compiler: 3000 + compiler code
# Angle vs other Compilation: 3099
# Other differences across compilation: 4000
# Difference across specific reference and current compilation (dead code removal): 5000 + compiler code


def main():
    parser = argparse.ArgumentParser(description="Tool to compile and compare shader output in order to help shader reduction")
    parser.add_argument("--no-postprocessing", dest="postprocessing", action="store_false")
    parser.add_argument("--override-compilers", dest="restrict_compilers", default=[], nargs="+")
    parser.add_argument('--shader-name', dest='shader',default='test.shadertrap')
    parser.add_argument('--ref', type=int, dest="ref", default=-1)
    parser.add_argument('--no-cleaning', dest='clean', action="store_false")
    parser.add_argument('--config-file', dest='config', default="config.xml")
    ns = parser.parse_args(sys.argv[1:])
    # Parse directory config
    exec_dirs = common.load_dir_settings(ns.config)
    compilers = common.load_compilers_settings(ns.config)
    compilers_dict = {}
    for compiler in compilers:
        if not ns.restrict_compilers or compiler in ns.restrict_compilers:
            compilers_dict[compiler.name] = compiler
    os.chdir(exec_dirs.execdir)
    execute_reduction(compilers_dict, exec_dirs, ns.shader, ns.ref, ns.clean, ns.postprocessing)

def execute_reduction(compilers_dict,exec_dirs,shader_name, ref, clean_dir, postprocessing):
    # Execute the shadertrap file with the different drivers
    common.clean_files(os.getcwd(), common.find_buffer_file(os.getcwd()))
    compilers = list(compilers_dict.values())
    results = common.execute_compilation(compilers, exec_dirs.graphicsfuzz, exec_dirs.shadertrap, shader_name, verbose=True, postprocessing=postprocessing)
    if clean_dir:
        common.clean_files(os.getcwd(), ["tmp.shadertrap"])
    i = 0
    for result in results:
        if result != "no_crash" and result != "timeout":
            sys.exit(str(1000+compilers[i].compilercode))
        if result == "timeout":
            sys.exit(str(2000+compilers[i].compilercode))
        i += 1
    print("No crash")
    if ref != -1:
        for compiler_name in compilers_dict.keys():
            comparison_result = common.comparison_helper(["buffer_" + compiler_name + ".txt", exec_dirs.keptbufferdir + str(ref)+".txt"])
            if len(comparison_result) == 2:
                print("Buffer difference between test and reference result: " + compiler_name)
                sys.exit(str(5000+compilers[compiler_name].compilercode))
        print("No difference between tests and references")
    buffers = []
    for compiler_name in compilers_dict.keys():
        buffers.append("buffer_"+compiler_name + ".txt")
    comparison_result = common.comparison_helper(buffers)

    if len(comparison_result) == 2:
        if len(comparison_result[0]) == 1 or len(comparison_result[1]) == 1:
            if len(comparison_result[0]) == 1:
                compiler_name = comparison_result[0][0].split("_")[1].split(".")[0]
            else:
                compiler_name = comparison_result[1][0].split("_")[1].split(".")[0]
            if clean_dir:
                common.clean_files(os.getcwd(),common.find_buffer_file(os.getcwd()))
            sys.exit(str(3000+compilers_dict[compiler_name].compilercode))
        # Try if we are in the angle case
        if (all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "angle"
                for buffer_name in comparison_result[0])
            and all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "independent"
                    for buffer_name in comparison_result[1])) \
                or (all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "angle"
                        for buffer_name in comparison_result[1])
                    and all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "independent"
                            for buffer_name in comparison_result[0])):
            if clean_dir:
                common.clean_files(os.getcwd(),common.find_buffer_file(os.getcwd()))
            sys.exit(3099)
        else:
            if clean_dir:
                common.clean_files(os.getcwd(),common.find_buffer_file(os.getcwd()))
            sys.exit(str(4000)+" " + str(comparison_result))
    elif len(comparison_result) >= 3:
        text = ""
        for same_result_buffers in comparison_result:
            text += "("
            for buffer_name in same_result_buffers:
                text += buffer_name.split("_")[1].split(".")[0]
                if len(same_result_buffers) != 1 and buffer_name is not same_result_buffers[-2]:
                    text += ", "
            if same_result_buffers is not comparison_result[-2]:
                text += "), "
            else:
                text +=") and "
        text += " show different results"
        print(text)
        if clean_dir:
            common.clean_files(os.getcwd(), common.find_buffer_file(os.getcwd()))
        sys.exit(str(4000)+ " " + str(results))
    else:
        print("No differences between implementations")
        if clean_dir:
            common.clean_files(os.getcwd(), common.find_buffer_file(os.getcwd()))
        sys.stderr.write("0000")
        sys.exit(0)


if __name__ == "__main__":
    main()
