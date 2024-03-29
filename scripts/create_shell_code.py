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

import reduction_helper
from utils.file_utils import ensure_abs_path
from utils.execution_utils import env_setup


# TODO rewrite this to make a double dispatch to a python script from the shell (testing will be easier)
def main():
    parser = argparse.ArgumentParser(description="Build an interestingness test shell script for the given shader")
    parser.add_argument("--override-compilers", dest="restrict_compilers", default=[], nargs="+", help="TODO")
    parser.add_argument('--harness-name', dest='harness', default='test.shadertrap',
                        help="Configure the name  of the shadetrap file in the shell code")
    parser.add_argument('--shader-name', dest='shader', default='test.comp.glsl',
                        help="Configure the name of the shader (glsl) in the shell code")
    parser.add_argument('--no-post-processing', dest='postprocess', action='store_false', help="TODO")
    parser.add_argument('--no-validation', dest='shadervalidation', action='store_false', help="TODO")
    parser.add_argument('--shell-name', dest='shellname', default='interesting.sh',
                        help="Configure the name of the interestingness test to dump the code to")
    parser.add_argument('--double_run', dest="double_run", action="store_true",
                        help="Run the program twice eliminating useless wrappers on the second run")
    parser.add_argument('--ref', type=int, dest="ref", default=-1, help="TODO")

    ns, exec_dirs, compilers_dict, reducer, shader_tool = env_setup(parser)

    build_shell_test(compilers_dict, exec_dirs, shader_tool, ns.harness, ns.shader, ns.ref, ns.shellname,
                     double_run=ns.double_run)


def build_shell_test(compilers_dict, exec_dirs, shader_tool, harness_name, shader_name, ref, shell_file,
                     double_run=False,
                     log_name="reduction.log"):
    # Collect error code from the reduction process
    shell_file = ensure_abs_path(exec_dirs.execdir, shell_file)
    try:
        reduction_helper.execute_reduction(compilers_dict, exec_dirs, shader_tool, harness_name, ref, True,
                                           double_run=double_run, postprocessing=True)
    except SystemExit as e:
        error_code = str(e)
        print(error_code)

        # We can use relative path everywhere except for the shell script
        log_name = os.path.basename(log_name)
        harness_name = os.path.basename(harness_name)
        shader_name = os.path.basename(shader_name)

        # Write the shell script
        if error_code != "0":
            print("Detected error code: " + error_code)

            shell = open(shell_file, 'w')
            # Sets execution conditions
            shell.write("#!/usr/bin/env bash\n" +
                        "set -o pipefail\n" +
                        "set -o nounset\n" +
                        "set -o errexit\n")
            # Sets specific locations for the script
            shell.write("ROOT=\"" + exec_dirs.execdir + "\"\n" +
                        "ERROR_CODE=\"" + str(error_code) + "\"\n")
            # Choose the shader name (glsl-reduce support without arguments) + other reducers with argument name
            shell.write("if [ $# -eq 0 ]\n" +
                        "then\n" +
                        "SHADER=$(pwd)\"/" + shader_name + "\"\n" +
                        "else\n" +
                        "SHADER_ROOT=$(echo $1 | sed -e 's/\\.[^.]*$//')\n" +
                        "SHADER=\"${SHADER_ROOT}.comp\"\n" +
                        "fi\n")
            # Logging
            shell.write("python3 ${ROOT}/scripts/benchmark_helper.py --log ${ROOT}/" + log_name + "\n")

            # Sanity checks
            shell.write("echo $(pwd)\n")
            shell.write("echo \"$SHADER\"\n")
            # Check that main remains
            shell.write("cat \"$SHADER\" | grep \"main\"\n")
            # Merge the shader with the (fixed) harness
            shell.write(
                "python3 ${ROOT}/scripts/splitter_merger.py --config-file ${ROOT}/scripts/config.xml --host "
                + shader_tool.name + " --merge " + "${ROOT}/"
                + harness_name + " $SHADER\n")

            # Call reduction script to check for error code (eventually with double-run)
            # TODO use only restricted compiler set
            if double_run:
                option = " --double-run"
            else:
                option = ""
            shell.write("ERROR_CODE_IN_FILE=$( (python3 ${ROOT}/scripts/reduction_helper.py --config-file ${"
                        "ROOT}/scripts/config.xml --shader-name ${ROOT}/" + harness_name + " --host " + shader_tool.name
                        + option + " 2>&1 > /dev/null) || true)\n")

            # Check returned code
            shell.write("echo $ERROR_CODE_IN_FILE\n" +
                        "if [ \"$ERROR_CODE_IN_FILE\" == \"$ERROR_CODE\" ]\n" +
                        "then\n" +
                        "    exit 0\n" +
                        "else\n" +
                        "    exit 1\n" +
                        "fi\n")
            shell.close()
            return str(error_code)
        else:
            print("Execution seems to conform on all tested compilers")
            return "0000"


if __name__ == '__main__':
    main()
