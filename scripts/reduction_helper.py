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

from scripts.utils.analysis_utils import comparison_helper
from scripts.utils.execution_utils import execute_compilation, env_setup
from scripts.utils.file_utils import clean_files, find_buffer_file


def clean_and_exit(exit_message, clean_dir):
    if clean_dir:
        clean_files(os.getcwd(), find_buffer_file(os.getcwd()))
    sys.exit(exit_message)


# Internal error code on exit have been distributed as follow
# Compiler codes are defined by the order of the compiler in the config file and only the first to fail is reported
# All crash: 1000
# crash / execution error: 1000 + compiler codes (by power of two)
# timeout: 2000 + compiler code (by power of two)
# Miscompilation on one compiler: 3000 + compiler code (by power of two)
# Angle vs other Compilation: 3099
# Other differences across compilation: 4000
# Difference across specific reference and current compilation (dead code removal): 5000 + compiler code
def execute_reduction(compilers_dict, exec_dirs, shader_tool, shader_name, ref, clean_dir, double_run, postprocessing):
    # Execute the host file with the different drivers
    clean_files(os.getcwd(), find_buffer_file(os.getcwd()))
    compilers = list(compilers_dict.values())
    results = execute_compilation(compilers_dict, exec_dirs.graphicsfuzz, shader_tool, shader_name,
                                  verbose=True, double_run=double_run, postprocessing=postprocessing)
    if clean_dir:
        clean_files(os.getcwd(), ["tmp" + shader_tool.file_extension])
    crash_flag = False
    all_crashed = True
    timeout_flag = False
    cp_codes_timeout = 0
    cp_codes_crash = 0
    i = 0
    for result in results:
        if result != "no_crash" and result != "timeout":
            cp_codes_crash += 1 << compilers[i].compilercode
            crash_flag = True
        elif result == "timeout":
            cp_codes_timeout += 1 << compilers[i].compilercode
            timeout_flag = True
        else:
            all_crashed = False
        i += 1
    if all_crashed:
        clean_and_exit(str(1000), clean_dir)
    elif crash_flag:
        clean_and_exit(str(1000 + cp_codes_crash), clean_dir)
    elif timeout_flag:
        clean_and_exit(str(2000 + cp_codes_timeout), clean_dir)
    print("No crash")
    if ref != -1:
        for compiler_name in compilers_dict.keys():
            comparison_result = comparison_helper(
                ["buffer_" + compiler_name + ".txt", exec_dirs.keptbufferdir + str(ref) + ".txt"])
            if len(comparison_result) == 2:
                print("Buffer difference between test and reference result: " + compiler_name)
                sys.exit(str(5000 + compilers[compiler_name].compilercode))
        print("No difference between tests and references")
    buffers = []
    for compiler_name in compilers_dict.keys():
        buffers.append("buffer_" + compiler_name + ".txt")
    comparison_result = comparison_helper(buffers)
    # TODO reuse the code built for stats_shader.py
    # This will probably require to move the code base to the common file
    if len(comparison_result) == 2:
        if len(comparison_result[0]) == 1 or len(comparison_result[1]) == 1:
            if len(comparison_result[0]) == 1:
                compiler_name = comparison_result[0][0].split("_")[1].split(".")[0]
            else:
                compiler_name = comparison_result[1][0].split("_")[1].split(".")[0]
            clean_and_exit(str(3000 + (1 << compilers_dict[compiler_name].compilercode)), clean_dir)
        # Try if we are in the angle case
        if (all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "angle"
                for buffer_name in comparison_result[0])
            and all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "independent"
                    for buffer_name in comparison_result[1])) \
                or (all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "angle"
                        for buffer_name in comparison_result[1])
                    and all(compilers_dict[buffer_name.split("_")[1].split(".")[0]].type == "independent"
                            for buffer_name in comparison_result[0])):
            clean_and_exit(str(3099), clean_dir)
        else:
            clean_and_exit(str(4000) + " " + str(comparison_result), clean_dir)
    elif len(comparison_result) >= 3:
        clean_and_exit(str(4000) + " " + str(comparison_result), clean_dir)
    else:
        if clean_dir:
            clean_files(os.getcwd(), find_buffer_file(os.getcwd()))
        print("No differences between implementations")
        sys.stderr.write("0000")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Tool to compile and compare shader output in order to help shader reduction")
    parser.add_argument("--no-postprocessing", dest="postprocessing", action="store_false",
                        help="Deactivate post-processing")
    parser.add_argument("--override-compilers", dest="restrict_compilers", default=[], nargs="+",
                        help="Override the list of compilers which will be used")
    parser.add_argument('--shader-name', dest='shader', default='test.shadertrap',
                        help="Specify the shader name to reduce (by default: test.shadertrap)")
    parser.add_argument('--ref', type=int, dest="ref", default=-1,
                        help="Compare the combined buffer outputs to a reference file")
    parser.add_argument('--no-cleaning', dest='clean', action="store_false",
                        help="Do not clean buffers and post-processed shaders after execution")
    parser.add_argument('--double-run', dest="double_run", action="store_true",
                        help="Run the program twice eliminating useless wrappers on the second run")
    ns, exec_dirs, compilers_dict, reducer, shader_tool = env_setup(parser)

    execute_reduction(compilers_dict, exec_dirs, shader_tool, ns.shader, ns.ref, ns.clean, ns.double_run,
                      ns.postprocessing)


if __name__ == "__main__":
    main()
