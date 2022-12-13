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
import sys

from utils.analysis_utils import comparison_helper, attribute_compiler_results
from utils.execution_utils import execute_compilation, env_setup
from utils.file_utils import clean_files, find_compiler_buffer_file


def identify_crashes(results, compilers):
    all_crashed = True
    cp_codes_timeout = 0
    cp_codes_crash = 0
    for result, compiler in zip(results, compilers):
        if result != "no_crash" and result != "timeout":
            cp_codes_crash += 1 << compiler.compilercode
        elif result == "timeout":
            cp_codes_timeout += 1 << compiler.compilercode
        else:
            all_crashed = False
    if all_crashed:
        return "1000"
    elif cp_codes_crash != 0:
        return str(1000 + cp_codes_crash)
    elif cp_codes_timeout != 0:
        return str(2000 + cp_codes_timeout)
    else:
        return str(0)


# Internal error codes are given below
# Compiler codes are defined by the order of the compiler in the config file and only the first to fail is reported
# All crash: 1000
# crash / execution error: 1000 + compiler codes (by power of two)
# timeout: 2000 + compiler code (by power of two)
# Miscompilation on one compiler: 3000 + compiler code (by power of two)
# Angle vs other Compilation: 3099
# Other differences across compilation: 4000
# Difference across specific reference and current compilation (dead code removal): 5000 + compiler code
# Compiler not recognized: 9999
def execute_reduction(compilers_dict, exec_dirs, shader_tool, shader_name, ref="", clean_dir=True, double_run=False,
                      postprocessing=True):
    # Clean the execution directory
    clean_files(exec_dirs.execdir, find_compiler_buffer_file(exec_dirs.execdir, compilers_dict))

    # Compile the shader with the different drivers with the correct run type
    if double_run:
        run_type = "add_id"
    elif not postprocessing:
        run_type = "no_postprocessing"
    else:
        run_type = "standard"
    results = execute_compilation(compilers_dict, exec_dirs.graphicsfuzz, exec_dirs.execdir, shader_tool, shader_name,
                                  run_type=run_type)

    # Check for compilation / crash / timeout errors
    error_code = identify_crashes(results, list(compilers_dict.values()))

    # Check for miscompilation / difference with a reference
    if error_code == "0":
        buffers = []
        for compiler_name in compilers_dict.keys():
            buffers.append(exec_dirs.execdir + compiler_name + ".txt")

        base_error = 3000
        # Add the reference buffer if needed
        if ref != "":
            buffers.append(ref)
            base_error = 5000
        # Compare the buffers
        comparison_result = comparison_helper(buffers)
        if len(comparison_result) >= 2:
            # Miscompilation checks (base_error - 3000) / Difference with reference (base_error - 5000)
            print(comparison_result)
            group_compiler = attribute_compiler_results(comparison_result, compilers_dict)
            if group_compiler == "angle":
                error_code = str(base_error + 99)
            elif group_compiler == "more than two":
                error_code = str(base_error + 1000) + " " + str(comparison_result)
            elif group_compiler in compilers_dict:
                error_code = str(base_error + compilers_dict[group_compiler].compilercode)
            else:
                error_code = str(9999)

    # Clean the resulting files if necessary
    if clean_dir:
        clean_files(exec_dirs.execdir, find_compiler_buffer_file(exec_dirs.execdir, compilers_dict))
        clean_files(exec_dirs.execdir, ["tmp" + shader_tool.file_extension])

    if error_code == "0":
        print("No difference between shaders")
        exit(0)
    else:
        exit(error_code)


def main():
    parser = argparse.ArgumentParser(
        description="Tool to compile and compare shader output in order to help shader reduction")
    parser.add_argument("--no-postprocessing", dest="postprocessing", action="store_false",
                        help="Deactivate post-processing")
    parser.add_argument('--shader-name', dest='shader', default='test.shadertrap',
                        help="Specify the shader name to reduce (by default: test.shadertrap)")
    parser.add_argument('--ref', dest="ref", default="",
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
