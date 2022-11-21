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
import shlex
import shutil
import stat
import subprocess
import sys
import time
from datetime import timedelta

import create_shell_code
import splitter_merger
from utils.execution_utils import env_setup
from utils.file_utils import find_compiler_buffer_file, clean_files, find_test_file


def main():
    parser = argparse.ArgumentParser(description="Automates the reduction of a shadertrap file")
    parser.add_argument("--test-file-name", dest="test_file", default="test_original.shadertrap",
                        help="specify a test file to reduce (by default: test_original.shadertrap)")
    parser.add_argument("--reducer", dest="reducer", default="glsl-reduce",
                        help="Specify a reducer to call by its name (by default:glsl-reduce)")
    parser.add_argument('--ref', type=int, dest="ref", default=-1)
    parser.add_argument("--output-file", dest="output_file", default="test_reduced.shadertrap",
                        help="specify the name of the expected output file")
    parser.add_argument("--batch-reduction", dest="batch", action="store_true",
                        help="launch batch reduction on all shaders stored in keptshaders (only attempt to reduce "
                             "shaders which are not already reduced)")
    parser.add_argument("--reduce-timeout", dest="timeout", action="store_true",
                        help="forces the reducer to attempt to reduce shaders which time out")
    parser.add_argument('--double-run', dest="double_run", action="store_true",
                        help="Run the program twice eliminating useless wrappers on the second run")
    ns, exec_dirs, compilers_dict, reducer, shader_tool = env_setup(parser)
    if ns.batch:
        files_to_reduce = os.listdir(exec_dirs.keptshaderdir)
        # Exclude files that have been already reduced
        for file in list(files_to_reduce):
            if os.path.isfile(exec_dirs.keptshaderdir + file) and len(file.split("_")) > 1:
                files_to_reduce.remove(file)
                if os.path.isfile(exec_dirs.keptshaderdir + file.split("_")[0] + shader_tool.file_extension):
                    files_to_reduce.remove(file.split("_")[0] + shader_tool.file_extension)

        batch_reduction(reducer, compilers_dict, exec_dirs, files_to_reduce, shader_tool, ns.ref, ns.timeout,
                        double_run=ns.double_run)
    else:
        run_reduction(reducer, compilers_dict, exec_dirs, ns.test_file, ns.output_file, shader_tool, ns.ref, ns.timeout,
                      double_run=ns.double_run)


def batch_reduction(reducer, compilers, exec_dirs, files_to_reduce, shader_tool, ref, reduce_timeout=False,
                    double_run=False, override_prefix="_reduced"):
    for file in files_to_reduce:
        # copy file to exec_dir
        file_name = file.split(".")[0]
        print("Reduction of " + exec_dirs.keptshaderdir + file)
        shutil.copy(exec_dirs.keptshaderdir + file, exec_dirs.execdir + file)
        # run reduction
        run_reduction(reducer, compilers, exec_dirs, exec_dirs.execdir + file,
                      exec_dirs.exec_dir + "test_reduced" + shader_tool.file_extension, shader_tool,
                      ref, reduce_timeout, log_file=reducer.name + "_" + file_name + ".log", double_run=double_run)

        # copy back
        if os.path.isfile(exec_dirs.execdir + "test_reduced" + shader_tool.file_extension):
            shutil.copy("test_reduced" + shader_tool.file_extension,
                        exec_dirs.keptshaderdir + file_name + override_prefix + shader_tool.file_extension)
            # clean exec_dir
            clean_files(os.getcwd(), ["test_reduced" + shader_tool.file_extension])


def run_reduction(reducer, compilers, exec_dirs, test_input, test_output, shader_tool, ref, reduce_timeout=False,
                  log_file="reduction.log", double_run=False):
    print("Building the interesting shell script")
    # Builds a temp harness to construct the interestingness test
    shutil.copy(test_input, exec_dirs.execdir + "temp" + shader_tool.file_extension)

    # Provides log file location
    error_code_str = create_shell_code.build_shell_test(compilers, exec_dirs, shader_tool,
                                                        exec_dirs.execdir + "temp" + shader_tool.file_extension,
                                                        reducer.input_file, ref, reducer.interesting_test,
                                                        double_run=double_run, log_name=log_file)

    # Ensure the interestingness test is executable
    interesting_test_stat = os.stat(reducer.interesting_test)
    os.chmod(reducer.interesting_test, interesting_test_stat.st_mode | stat.S_IEXEC)

    # Parse the error code from the interestingness test
    error_code = int(error_code_str[:4])

    # List temporary files for cleaning
    temp_files = [reducer.input_file, reducer.output_files, reducer.interesting_test, "temp" + shader_tool.file_extension]

    # Check if we want to perform reduction for this type of errors
    if error_code >= 3000 or (1000 <= error_code <= 1999) or (error_code >= 2000 and reduce_timeout):
        # Copy the embedded harness file to the output (avoid destroying the harness through execution)
        shutil.copy(test_input, test_output)

        # Generate extra necessary files when using glsl-reduce
        if reducer.name == "glsl-reduce":
            json_file = open(reducer.input_file.split(".")[0] + ".json", "w")
            json_file.write("{}")
            json_file.close()
            temp_files.append(reducer.input_file.split(".")[0] + ".json")

        # Extract the shader code using the splitter and name it as input_file
        splitter_merger.split(shader_tool, test_input, reducer.input_file)

        # Perform the reduction using the reduction launch command
        ref_timestamp = time.time()
        print("Setup finished, beginning reduction")
        cmd = shlex.split(reducer.command)
        print("Reducer command: " + " ".join(cmd))
        process = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stdout, universal_newlines=True,
                                 cwd=exec_dirs.execdir)

        # Add eventual temporary files
        temp_files += find_test_file(exec_dirs.execdir)

        # Check results
        if os.path.isfile(reducer.output_files):
            # Merge the shader code with the harness
            splitter_merger.merge(shader_tool, test_output, reducer.output_files)
            temp_files.remove(test_output)
            end_timestamp = time.time()
            delta = timedelta(seconds=end_timestamp - ref_timestamp)
            print("Reduction finished in " + str(delta))
        else:
            print("Reduction failed for shader")
    elif error_code >= 2000:
        print("Skipping test-case reduction for timeout shader")
    else:
        print("No error on the current shader")

    clean_files(exec_dirs.execdir, temp_files)


if __name__ == '__main__':
    main()
