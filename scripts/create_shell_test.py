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

    ns, exec_dirs, compilers_dict, reducer, shader_tool = common.env_setup(parser)

    build_shell_test(compilers_dict, exec_dirs, shader_tool, ns.harness, ns.shader, ns.ref, ns.shellname,
                     double_run=ns.double_run)


def build_shell_test(compilers_dict, exec_dirs, shader_tool, harness_name, shader_name, ref, shell_file, double_run=False,
                     instrumentation=""):
    # Collect error code from the reduction process
    try:
        reduction_helper.execute_reduction(compilers_dict, exec_dirs, shader_tool, harness_name, ref, True,
                                           double_run=double_run, postprocessing=True)
    except SystemExit as e:
        error_code = str(e)
        print("Detected error code: " + error_code)
        shell = open(shell_file, 'w')
        # Sets structure
        shell.write("#!/usr/bin/env bash\n")
        shell.write("set -o pipefail\n")
        shell.write("set -o nounset\n")
        shell.write("set -o errexit\n")
        shell.write("ROOT=\"" + os.getcwd() + "\"\n")
        shell.write("ERROR_CODE=\"" + str(error_code) + "\"\n")
        # Choose the shader name (glsl-reduce support)
        shell.write("if [ $# -eq 0 ]\n")
        shell.write("then\n")
        shell.write("SHADER=$(pwd)\"/" + shader_name + "\"\n")
        shell.write("else\n")
        shell.write("SHADER_ROOT=$(echo $1 | sed -e 's/\\.[^.]*$//')\n")
        shell.write("SHADER=\"${SHADER_ROOT}.comp\"\n")
        shell.write("fi\n")
        if instrumentation != "":
            shell.write("python3 ${ROOT}/scripts/benchmark_helper.py --log ${ROOT}/" + instrumentation + "\n")
        shell.write("echo $(pwd)\n")
        shell.write("echo \"$SHADER\"\n")
        # Check that main remains
        shell.write("cat \"$SHADER\" | grep \"main\"\n")
        # Call merger
        shell.write(
            "python3 ${ROOT}/scripts/splitter_merger.py --config-file ${ROOT}/scripts/config.xml --host " + shader_tool.name + " --merge " + "${ROOT}/"
            + harness_name + "$SHADER\"\n")
        # Call reduction script to check for error code
        # TODO use only restricted compiler set
        if double_run:
            option = " --double-run"
        else:
            option = ""
        shell.write("ERROR_CODE_IN_FILE=$( (python3 ${ROOT}/scripts/reduction_helper.py --config-file ${"
                    "ROOT}/scripts/config.xml --shader-name ${ROOT}/" + harness_name + " --host " + shader_tool.name
                    + option + " 2>&1 > /dev/null) || true)\n")
        shell.write("echo $ERROR_CODE_IN_FILE\n")
        shell.write("if [ \"$ERROR_CODE_IN_FILE\" == \"$ERROR_CODE\" ]\nthen\n    exit 0\nelse\n    exit 1\nfi\n")
        shell.close()
        return str(error_code)
    else:
        print("Execution seems to conform on all tested compilers")
        return "0000"


if __name__ == '__main__':
    main()
