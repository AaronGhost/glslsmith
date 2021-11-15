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

import sys
from subprocess import run
import os
import shutil
import argparse
import common
import automate_reducer


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Execute GLSLsmith framework and sort results")
    parser.add_argument('--seed', dest='seed', default=-1, help="Seed the random generator of GLSLsmith")
    parser.add_argument('--shader-count', dest='shadercount', default=50, type=int,
                        help="Specify the number of test per batch")
    parser.add_argument('--syntax-only', dest='syntaxonly', action='store_true',
                        help="Compile only the first compiler of the provided list to verify the syntax through "
                             "ShaderTrap")
    parser.add_argument('--generate-only', dest='generateonly', action='store_true',
                        help="Only generate shaders without doing differential testing")
    parser.add_argument('--no-generation', dest='nogeneration', action='store_true',
                        help="Performs execution and differential testing on already provided files")
    parser.add_argument('--diff-files-only', dest='diffonly', action='store_true',
                        help="Only compare already written buffer outputs")
    parser.add_argument('--no-compiler-validation', dest='validatecompilers', action='store_false',
                        help="Deactivate the compiler validation at beginning of the batch execution")
    parser.add_argument('--continuous', dest='continuous', action='store_true',
                        help="Launch the bug finding in never ending mode")
    parser.add_argument('--reduce', dest="reduce", action="store_true",
                        help="Reduce interesting shaders at the end of a batch")
    parser.add_argument("--reducer", dest="reducer", default="glsl-reduce",
                        help="Enforce the reducer if reduction is applied, see --reduce")
    parser.add_argument('--reduce-timeout', dest="timeout", action="store_true",
                        help="Force the reducer to consider reduction of shaders that time out (DISCOURAGED)")
    parser.add_argument('--reduce-wrappers', dest='double_run', action='store_true',
                        help="Run the reconditioning step twice, reducing the number of wrappers on the second run")
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help="Provide more logging information about the executed command")

    ns, exec_dirs, compilers_dict, reducer, shader_tool = common.env_setup(parser)

    # temp value for compiler validation (not revalidating on loops)
    validate_compilers = ns.validatecompilers

    batch_nb = 1
    # go to generation location
    seed = 0
    if ns.seed != -1:
        seed = ns.seed

    while batch_nb == 1 or ns.continuous:
        if not ns.diffonly:
            if not ns.nogeneration:
                # generate programs and seed reporting
                cmd = ["mvn", "-f", exec_dirs.graphicsfuzz + "pom.xml", "-pl", "glslsmith", "-q", "-e"
                    , "exec:java", "-Dexec.mainClass=com.graphicsfuzz.GeneratorHandler"]

                args = r'-Dexec.args=--shader-count ' + str(
                    ns.shadercount) + r' --output-directory ' + exec_dirs.shaderoutput
                if ns.seed != -1:
                    args += r' --seed ' + str(ns.seed)
                if ns.host != "shadertrap":
                    args += r' --printer ' + str(ns.host)
                cmd += [args]

                process_return = run(cmd, capture_output=True, text=True)
                if "ERROR" in process_return.stdout:
                    print("error with glslsmith generator, please fix them before running the script again")
                    print(process_return.stdout)
                    return
                for line in process_return.stdout.split("\n"):
                    if "Seed:" in line:
                        print(line)
                        seed = int(line.split(':')[1])

                print("Generation of " + str(ns.shadercount) + " shaders done")
                if ns.generateonly:
                    return

            # execute actions on generated shaders
            if ns.syntaxonly:
                # Execute the program with the default implementation
                for i in range(ns.shadercount):
                    result = common.execute_compilation(
                        [compilers_dict.values()[0]], exec_dirs.graphicsfuzz, shader_tool,
                        exec_dirs.shaderoutput + "test_" + str(i) + shader_tool.file_extension, verbose=True)
                    if result[0] != "no_crash":
                        print("Error on shader " + str(i))
                    else:
                        print("Shader " + str(i) + " validated")
                # Clean the directory after usage and exit
                buffers = common.find_buffer_file(os.getcwd())
                common.clean_files(os.getcwd(), buffers)
                print("Compilation of all programs done")
                return

            # Validate compilers on an empty program instance
            if validate_compilers:
                if shader_tool.name != "shadertrap":
                    print("Impossible to validate the compilers if the host language is not shadertrap")
                else:
                    for compiler in compilers_dict.values():
                        if compiler.type == "android":
                            run(["adb", "push", "scripts/empty.shadertrap", "/data/local/tmp/test.shadertrap"],
                                capture_output=True, text=True)
                            # The Android ShaderTrap binary is assumed to be present at /data/local/tmp

                            process_return = run(["adb", "shell", "/data/local/tmp/shadertrap", "--show-gl-info",
                                                  "--require-vendor-renderer-substring",
                                                  compiler.renderer, "/data/local/tmp/test.shadertrap"],
                                                 capture_output=True, text=True)
                            run(["adb", "shell", "rm", "/data/local/tmp/test.shadertrap"])
                        else:
                            cmd_ending = [shader_tool.path, "--show-gl-info", "--require-vendor-renderer-substring",
                                          compiler.renderer, "scripts/empty.shadertrap"]
                            cmd = common.build_env_from_compiler(compiler) + cmd_ending
                            process_return = run(cmd, capture_output=True, text=True)
                            buffers = common.find_buffer_file(os.getcwd())
                            common.clean_files(os.getcwd(), buffers)
                        if compiler.renderer not in process_return.stdout:
                            print("compiler not found or not working: " + compiler.name)
                            print(process_return.stdout)
                            print(process_return.stderr)
                            return
                    print("compilers validated")
                    validate_compilers = False

            buffers = common.find_buffer_file(exec_dirs.dumpbufferdir)
            common.clean_files(exec_dirs.dumpbufferdir, buffers)
            # Execute program compilation on each compiler and save the results for the batch
            for i in range(ns.shadercount):
                common.execute_compilation(compilers_dict, exec_dirs.graphicsfuzz, shader_tool,
                                           exec_dirs.shaderoutput + "test_" + str(i) + shader_tool.file_extension,
                                           str(i), exec_dirs.dumpbufferdir, verbose=ns.verbose,
                                           double_run=ns.double_run, postprocessing=True)
        # Compare outputs and save buffers
        # Check that we can compare outputs across multiple compilers
        if len(compilers_dict) == 1:
            print("Impossible to compare outputs for only one compiler")
            return
        identified_shaders = []
        for i in range(ns.shadercount):
            # Reference buffers for a given shader instance
            buffers_files = []
            for compiler_name in compilers_dict:
                buffers_files.append(exec_dirs.dumpbufferdir + "buffer_" + compiler_name + "_" + str(i) + ".txt")
            # Compare and check back the results
            values = common.comparison_helper(buffers_files)
            if len(values) != 1:
                print("Different results across implementations for shader " + str(seed + i))
                # Move shader
                identified_shaders.append(str(seed + i) + shader_tool.file_extension)
                shutil.move(exec_dirs.shaderoutput + "test_" + str(i) + shader_tool.file_extension,
                            exec_dirs.keptshaderdir + str(seed + i) + shader_tool.file_extension)
                # Move buffers
                for compiler_name in compilers_dict:
                    shutil.move(exec_dirs.dumpbufferdir + "buffer_" + compiler_name + "_" + str(i) + ".txt",
                                exec_dirs.keptbufferdir + compiler_name + "_" + str(seed + i) + ".txt")

        # reduce with the default reducer if specified
        if ns.reduce:
            automate_reducer.batch_reduction(reducer, compilers_dict, exec_dirs, identified_shaders, shader_tool, -1,
                                             ns.timeout)
        # Set flag for while loop and print the number of batch
        print("Batch " + str(batch_nb) + " processed")
        batch_nb += 1


if __name__ == "__main__":
    main()
