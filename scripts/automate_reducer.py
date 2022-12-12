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
from utils.file_utils import clean_files, find_test_file, ensure_abs_path


def batch_reduction(reducer, compilers, exec_dirs, files_to_reduce, shader_tool, ref, reduce_timeout=False,
                    double_run=False):
    reduction_input = exec_dirs.execdir + "test_to_reduce" + shader_tool.file_extension
    reduction_output = exec_dirs.execdir + "test_reduced" + shader_tool.file_extension
    print("Reducing " + str(len(files_to_reduce)) + " shaders")
    for file in files_to_reduce:
        # copy file to exec_dir
        file_name = file.split("/")[-1].split(".")[0]
        reduced_filename = file.replace(shader_tool.file_extension, "_re" + shader_tool.file_extension)
        print("Reduction of " + file)
        shutil.copy(file, reduction_input)
        # run reduction
        run_reduction(reducer, compilers, exec_dirs, reduction_input, reduction_output, shader_tool, ref,
                      reduce_timeout, log_file=reducer.name + "_" + file_name + ".log", double_run=double_run)

        # copy back
        if os.path.isfile(reduction_output):
            shutil.copy(reduction_output,
                        reduced_filename)
            # clean exec_dir
            clean_files(exec_dirs.execdir, ["test_to_reduce" + shader_tool.file_extension,
                                            "test_reduced" + shader_tool.file_extension])


def run_reduction(reducer, compilers, exec_dirs, test_input, test_output, shader_tool, ref, reduce_timeout=False,
                  log_file="reduction.log", double_run=False):
    test_input = ensure_abs_path(exec_dirs.execdir, test_input)
    test_output = ensure_abs_path(exec_dirs.execdir, test_output)
    log_file = ensure_abs_path(exec_dirs.execdir, log_file)
    input_file = ensure_abs_path(exec_dirs.execdir, reducer.input_file)
    output_file = ensure_abs_path(exec_dirs.execdir, reducer.output_files)
    original_test_files = find_test_file(exec_dirs.execdir)
    # Provides log file location
    error_code_str = create_shell_code.build_shell_test(compilers, exec_dirs, shader_tool,
                                                        test_input,
                                                        input_file, ref,
                                                        exec_dirs.execdir + reducer.interesting_test,
                                                        double_run=double_run, log_name=log_file)

    # Ensure the interestingness test is executable
    interesting_test_stat = os.stat(exec_dirs.execdir + reducer.interesting_test)
    os.chmod(exec_dirs.execdir + reducer.interesting_test, interesting_test_stat.st_mode | stat.S_IEXEC)

    # Parse the error code from the interestingness test
    error_code = int(error_code_str[:4])

    # List temporary files for cleaning
    temp_files = [reducer.input_file, reducer.output_files, reducer.interesting_test]

    # Check if we want to perform reduction for this type of errors
    if error_code >= 3000 or (1000 <= error_code <= 1999) or (error_code >= 2000 and reduce_timeout):
        # Copy the embedded harness file to the output (avoid destroying the harness through execution)
        shutil.copy(test_input, test_output)

        # Generate extra necessary files when using glsl-reduce
        if reducer.name == "glsl-reduce":
            json_file = open(input_file.split(".")[0] + ".json", "w")
            json_file.write("{}")
            json_file.close()
            temp_files.append(input_file.split(".")[0] + ".json")

        # Extract the shader code using the splitter and name it as input_file
        splitter_merger.split(shader_tool, test_input, input_file)

        # Perform the reduction using the reduction launch command
        ref_timestamp = time.time()
        cmd = shlex.split(reducer.command)
        print("Reduction launched: " + " ".join(cmd))
        process = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stdout, universal_newlines=True,
                                 cwd=exec_dirs.execdir)

        # Add eventual temporary files
        temp_files += find_test_file(exec_dirs.execdir)
        temp_files = list(set(temp_files) - set(original_test_files))

        # Check results
        if os.path.isfile(output_file):
            # Merge the shader code with the harness
            splitter_merger.merge(shader_tool, test_output, output_file)
            temp_files.remove(test_output.split("/")[-1])
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


def get_files_to_reduce(reduce_keptshaders, test_file, keptshaderdir):
    if reduce_keptshaders:
        files_to_reduce = os.listdir(keptshaderdir)
        for file in list(files_to_reduce):
            # Exclude files that have been already reduced
            if file.find("_re") != -1:
                files_to_reduce.remove(file)
                not_reduced_file = file.replace("_re", "")
                if not_reduced_file in files_to_reduce:
                    files_to_reduce.remove(not_reduced_file)

        # Return full path names
        return map(lambda x: keptshaderdir + x, files_to_reduce)

    else:
        return [test_file]


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

    files_to_reduce = get_files_to_reduce(ns.batch, exec_dirs.execdir + ns.test_file, exec_dirs.keptshaderdir)
    batch_reduction(reducer, compilers_dict, exec_dirs, files_to_reduce, shader_tool, ns.ref, ns.timeout,
                    double_run=ns.double_run)


if __name__ == '__main__':
    main()
