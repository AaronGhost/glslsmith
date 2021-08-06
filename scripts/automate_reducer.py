import argparse
import os
import shlex
import shutil
import subprocess
import sys

import create_shell_test
import common
import splitter_merger

def main():
    parser = argparse.ArgumentParser(description="Automates the reduction of a shadertrap file")
    parser.add_argument('--config-file', dest='config', default="config.xml")
    parser.add_argument("--test-file-name", dest="test_file", default="test_original.shadertrap")
    parser.add_argument("--reducer", dest="reducer",default="perses")
    parser.add_argument('--ref', type=int, dest="ref", default=-1)
    parser.add_argument("--output-file", dest="output_file", default="test_reduced.shadertrap")
    parser.add_argument("--batch-reduction", dest="batch", action="store_true")
    parser.add_argument("--reduce-timeout", dest="timeout", action="store_true")
    ns = parser.parse_args(sys.argv[1:])

    reducers = common.load_reducers_settings(ns.config)
    compilers = common.load_compilers_settings(ns.config)
    exec_dirs = common.load_dir_settings(ns.config)
    os.chdir(exec_dirs.execdir)
    if len(reducers) == 0:
        exit("No reducer has been declared at installation, please rerun installation or edit the configuration file")
    reducer = reducers[0]
    if ns.reducer != "":
        reducer_found = False
        for existing_reducer in reducers:
            if existing_reducer.name == ns.reducer:
                reducer = existing_reducer
                reducer_found = True
        if not reducer_found:
            exit("No reducer named "+ str(ns.reducer) + " configured")
    compilers_dict = {}
    for compiler in compilers:
        compilers_dict[compiler.name] = compiler
    if ns.batch:
        files_to_reduce = os.listdir(exec_dirs.keptshaderdir)
        # Exclude files that have been already reduced
        for file in list(files_to_reduce):
            if os.path.isfile(exec_dirs.keptshaderdir+file) and len(file.split("_")) > 1:
                files_to_reduce.remove(file)
                if os.path.isfile(exec_dirs.keptshaderdir+file.split("_")[0]+".shadertrap"):
                    files_to_reduce.remove(file.split("_")[0]+".shadertrap")

        batch_reduction(reducer, compilers_dict, exec_dirs, files_to_reduce, ns.ref, ns.timeout)
    else:
        run_reduction(reducer, compilers_dict, exec_dirs, ns.test_file, ns.output_file, ns.ref, ns.timeout)


def batch_reduction(reducer, compilers, exec_dirs, files_to_reduce, ref, reduce_timeout, override_prefix="_reduced"):
    for file in files_to_reduce:
        # copy file to exec_dir
        file_radix = file.split(".")[0]
        print("Reduction of " + exec_dirs.keptshaderdir+file)
        shutil.copy(exec_dirs.keptshaderdir+file, "original_test.shadertrap")
        # run reduction
        run_reduction(reducer, compilers, exec_dirs, "original_test.shadertrap", "test_reduced.shadertrap", ref,
                      reduce_timeout)
        # copy back
        shutil.copy("test_reduced.shadertrap", exec_dirs.keptshaderdir + file_radix+override_prefix+".shadertrap")
        # clean exec_dir
        common.clean_files(os.getcwd(),["test_reduced.shadertrap"])


def run_reduction(reducer, compilers, exec_dirs, test_input, test_output, ref, reduce_timeout):
    # Builds the interestingness test
    print("Building the interesting shell script")
    # Builds a temp harness
    shutil.copy(test_input, "temp.shadertrap")
    error_code_str = create_shell_test.build_shell_test(compilers, exec_dirs, "temp.shadertrap", reducer.input_file, ref,
                                                    reducer.interesting_test)
    error_code = int(error_code_str[:4])
    # Copy the input file to the output (prevents to destroy the harness through execution)
    shutil.copy(test_input, test_output)
    if error_code >= 3000 or (1000 <= error_code <= 1999) or (error_code >= 2000 and reduce_timeout):
        if reducer.name == "glsl-reduce":
            json_file = open(reducer.input_file.split(".")[0]+".json", "w")
            json_file.write("{}")
            json_file.close()
        # extract the shader code using the splitter and name it as input_file
        splitter_merger.split(test_input, reducer.input_file)
        # perform the reduction using the reduction launch command
        print("Setup finished, beginning reduction")
        cmd = shlex.split(reducer.command)
        process = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stdout, universal_newlines=True, cwd=exec_dirs.execdir)
        print("reduction finished")
        # after execution concatenate back the result
        splitter_merger.merge(test_output, reducer.output_files)
    elif error_code >= 2000:
        print("Skipping test-case reduction for timeout shader")
    else:
        print("No error on the current shader")
    # Cleans the current repository
    common.clean_files(os.getcwd(),["temp.shadertrap",reducer.input_file, reducer.output_files, reducer.interesting_test])
    residues = common.find_test_file(os.getcwd())
    residues.remove(test_output)
    common.clean_files(os.getcwd(),residues)

if __name__ == '__main__':
    main()
