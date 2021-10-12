import argparse
import os
import shlex
import shutil
import stat
import subprocess
import sys
import time
from datetime import timedelta

import create_shell_test
import common
import splitter_merger


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
    parser.add_argument("--instrumentation", dest="instru", action="store_true",
                        help="adds an extra line in the shell script to generate a reduction log file")
    ns, exec_dirs, compilers_dict, reducer, shader_tool = common.env_setup(parser)
    if ns.batch:
        files_to_reduce = os.listdir(exec_dirs.keptshaderdir)
        # Exclude files that have been already reduced
        for file in list(files_to_reduce):
            if os.path.isfile(exec_dirs.keptshaderdir + file) and len(file.split("_")) > 1:
                files_to_reduce.remove(file)
                if os.path.isfile(exec_dirs.keptshaderdir + file.split("_")[0] + shader_tool.file_extension):
                    files_to_reduce.remove(file.split("_")[0]  + shader_tool.file_extension)

        batch_reduction(reducer, compilers_dict, exec_dirs, files_to_reduce, shader_tool, ns.ref, ns.timeout,
                        instrumentation=ns.instru)
    else:
        run_reduction(reducer, compilers_dict, exec_dirs, ns.test_file, ns.output_file, shader_tool, ns.ref, ns.timeout,
                      instrumentation=ns.instru)


def batch_reduction(reducer, compilers, exec_dirs, files_to_reduce, shader_tool, ref, reduce_timeout, override_prefix="_reduced",
                    instrumentation=False):
    for file in files_to_reduce:
        # copy file to exec_dir
        file_radix = file.split(".")[0]
        print("Reduction of " + exec_dirs.keptshaderdir + file)
        shutil.copy(exec_dirs.keptshaderdir + file, "original_test" + shader_tool.file_extension)
        # run reduction
        run_reduction(reducer, compilers, exec_dirs, "original_test" + shader_tool.file_extension, "test_reduced" + shader_tool.file_extension, shader_tool,
                      ref, reduce_timeout, log_file=reducer.name + "_" + file_radix + ".log",
                      instrumentation=instrumentation)

        # copy back
        if os.path.isfile(exec_dirs.execdir + os.sep + "test_reduced" + shader_tool.file_extension):
            shutil.copy("test_reduced" + shader_tool.file_extension,
                        exec_dirs.keptshaderdir + file_radix + override_prefix + shader_tool.file_extension)
            # clean exec_dir
            common.clean_files(os.getcwd(), ["test_reduced" + shader_tool.file_extension])


def run_reduction(reducer, compilers, exec_dirs, test_input, test_output, shader_tool, ref, reduce_timeout, log_file="",
                  instrumentation=True):
    # Builds the interestingness test
    print("Building the interesting shell script")
    # Builds a temp harness
    shutil.copy(test_input, "temp" + shader_tool.file_extension)

    # Accounts for instrumentation
    instrumentation_filename = log_file
    if instrumentation and instrumentation_filename == "":
        instrumentation_filename = reducer.name + "_" + test_input + ".log"
    error_code_str = create_shell_test.build_shell_test(compilers, exec_dirs, shader_tool, "temp" + shader_tool.file_extension,
                                                        reducer.input_file, ref, reducer.interesting_test,
                                                        instrumentation_filename)
    error_code = int(error_code_str[:4])
    # Make sure the interestingness test is executable
    interesting_test_stat = os.stat(reducer.interesting_test)
    os.chmod(reducer.interesting_test, interesting_test_stat.st_mode | stat.S_IEXEC)
    common.clean_files(exec_dirs.execdir, common.find_buffer_file(exec_dirs.execdir))
    # Copy the input file to the output (prevents to destroy the harness through execution)
    shutil.copy(test_input, test_output)
    if error_code >= 3000 or (1000 <= error_code <= 1999) or (error_code >= 2000 and reduce_timeout):
        if reducer.name == "glsl-reduce":
            json_file = open(reducer.input_file.split(".")[0] + ".json", "w")
            json_file.write("{}")
            json_file.close()
        # extract the shader code using the splitter and name it as input_file
        splitter_merger.split(shader_tool, test_input, reducer.input_file)

        # perform the reduction using the reduction launch command
        ref_timestamp = time.time()
        print("Setup finished, beginning reduction")
        cmd = shlex.split(reducer.command)
        print("Reducer command: " + " ".join(cmd))
        process = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stdout, universal_newlines=True,
                                 cwd=exec_dirs.execdir)
        # after execution concatenate back the result
        if os.path.isfile(reducer.output_files):
            splitter_merger.merge(shader_tool, test_output, reducer.output_files)
            end_timestamp = time.time()
            delta = timedelta(seconds=end_timestamp - ref_timestamp)
            print("Reduction finished in " + str(delta))
            if instrumentation:
                f = open(instrumentation_filename, "a")
                f.write("\n" + str(delta))
                f.close()
        else:
            print("Reduction failed for shader")
            common.clean_files(os.getcwd(), ["test_reduced" + shader_tool.file_extension])
    elif error_code >= 2000:
        print("Skipping test-case reduction for timeout shader")
        common.clean_files(os.getcwd(), ["test_reduced" + shader_tool.file_extension])
    else:
        print("No error on the current shader")
        common.clean_files(os.getcwd(), ["test_reduced" + shader_tool.file_extension])

    # Cleans the current repository
    common.clean_files(os.getcwd(),
                       ["temp" + shader_tool.file_extension, reducer.input_file, reducer.output_files, reducer.interesting_test])
    residues = common.find_test_file(os.getcwd())
    if test_output in residues:
        residues.remove(test_output)
    common.clean_files(os.getcwd(), residues)


if __name__ == '__main__':
    main()
