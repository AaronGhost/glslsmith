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
import shutil
import time
import automate_reducer
import splitter_merger
from utils.analysis_utils import comparison_helper, attribute_compiler_results
from utils.execution_utils import execute_compilation, call_glslsmith_generator, env_setup, \
    call_glslsmith_reconditioner, single_compile
from utils.file_utils import find_compiler_buffer_file, clean_files


def validate_compiler(exec_dir, compiler, shader_tool):
    shutil.copy(os.path.dirname(os.path.realpath(__file__)) + "/empty.shadertrap", exec_dir)
    crash, timeout, message = single_compile(exec_dir, compiler, exec_dir + "/empty.shadertrap",
                                             shader_tool)
    clean_files(exec_dir, ["empty.shadertrap"])
    if message != "no_crash":
        print("Error with compiler " + compiler.name)
        print(message)
        exit(1)

    return message


def glsl_output(exec_dir, graphicsfuzz, shaderoutput, shader_tool, current_seed):
    # Give the files their seed name
    reconditioned_path = shaderoutput + "test_" + str(
        current_seed) + "_re" + shader_tool.file_extension
    glsl_path = shaderoutput + "test_" + current_seed + "_re" + ".comp"
    # Recondition the shader
    check, message = call_glslsmith_reconditioner(graphicsfuzz, exec_dir, shaderoutput + "test_" + str(
        current_seed) + shader_tool.file_extension, reconditioned_path)
    if not check:
        print(message)
        print("Shader " + current_seed + " cannot be parsed for post-processing")
        exit(1)
    splitter_merger.split(shader_tool, reconditioned_path, glsl_path)


def syntax_check(compiler, exec_dir, graphicsfuzz, shaderoutput, shader_tool, current_seed):
    result = execute_compilation(
        compiler, graphicsfuzz, exec_dir, shader_tool,
        shaderoutput + "test_" + current_seed + shader_tool.file_extension)
    if result[0] != "no_crash":
        print("Error on shader " + current_seed)
    else:
        print("Shader " + current_seed + " validated")


def write_output_to_file(text, location):
    with open(location, "r") as f:
        lines = f.readlines()
        lines.insert(1, text)
    with open(location, "w") as f:
        f.writelines(lines)


def save_test_case(kept_shader_dir, dump_buffer_dir, kept_buffer_dir, compilers_dict, shader_location, current_seed,
                   shader_tool):
    # Move test
    shutil.move(shader_location,
                kept_shader_dir + current_seed + shader_tool.file_extension)

    # Move buffers
    for compiler_name in compilers_dict:
        shutil.move(dump_buffer_dir + compiler_name + "_" + current_seed + ".txt",
                    kept_buffer_dir + compiler_name + "_" + current_seed + ".txt")


def exec_glslsmith(exec_dirs, compilers_dict, reducer, shader_tool, seed, shader_count, syntax_only=False, reduce=False,
                   run_type="standard", glsl_only=False):
    # go to generation location
    if seed != -1:
        seed = seed
    else:
        seed = int(time.time())

    # generate programs and seed reporting
    check, message = call_glslsmith_generator(exec_dirs.graphicsfuzz, exec_dirs.execdir, shader_count,
                                              exec_dirs.shaderoutput, seed, shader_tool)
    if not check:
        print(message)
        exit(1)
    print("Generation of " + str(shader_count) + " shaders with seed:" + str(seed) + " done")
    if glsl_only:
        for i in range(shader_count):
            glsl_output(exec_dirs.execdir, exec_dirs.graphicsfuzz, exec_dirs.shaderoutput, shader_tool, str(seed + i))
        print("Shaders successfully reconditioned and formatted as glsl")
        exit(0)

    # Check the syntax of the generated shader with the first available compiler
    if syntax_only:
        # Execute the program with the default implementation
        first_compiler = list(compilers_dict.values())[0]
        for i in range(shader_count):
            syntax_check({first_compiler.name: first_compiler}, exec_dirs.execdir, exec_dirs.graphicsfuzz,
                         exec_dirs.shaderoutput, shader_tool, str(seed + i))
        # Clean the directory after usage and exit
        clean_files(exec_dirs.execdir, find_compiler_buffer_file(exec_dirs.execdir, compilers_dict))
        clean_files(exec_dirs.execdir, ["tmp" + shader_tool.file_extension])

        print("Compilation of all programs done")
        exit(0)

    # Execute program compilation on each compiler and save the results for the batch
    identified_shaders = []
    for i in range(shader_count):
        current_seed = str(seed + i)
        # Clean the execution platform and execute compilation
        clean_files(exec_dirs.execdir, find_compiler_buffer_file(exec_dirs.execdir, compilers_dict))
        clean_files(exec_dirs.execdir, ["tmp" + shader_tool.file_extension])
        shader_location = exec_dirs.shaderoutput + "test_" + current_seed + shader_tool.file_extension
        _ = execute_compilation(compilers_dict, exec_dirs.graphicsfuzz, exec_dirs.execdir, shader_tool,
                                shader_location,
                                current_seed, exec_dirs.dumpbufferdir, run_type)

        # Compare outputs and save buffers
        # Reference buffers for a given shader instance
        buffers_files = []
        for compiler_name in compilers_dict:
            buffers_files.append(exec_dirs.dumpbufferdir + compiler_name + "_" + current_seed + ".txt")
        # Compare and check back the results from the buffers
        values = comparison_helper(buffers_files)
        if len(values) != 1:
            print("Differences on shader: " + current_seed)
            # Register the shader for eventual reduction
            identified_shaders.append(exec_dirs.keptshaderdir + current_seed + shader_tool.file_extension)
            # Add a name comment in the shader to identify easily the responsible compiler(s)
            write_output_to_file("# " + attribute_compiler_results(values, compilers_dict) + "\n", shader_location)
            # Save the relevant buffers and shaders
            save_test_case(exec_dirs.keptshaderdir, exec_dirs.dumpbufferdir, exec_dirs.keptbufferdir, compilers_dict,
                           shader_location, current_seed, shader_tool)

    clean_files(exec_dirs.execdir, find_compiler_buffer_file(exec_dirs.execdir, compilers_dict))
    clean_files(exec_dirs.execdir, ["tmp" + shader_tool.file_extension])

    # reduce with the default reducer if specified
    if reduce:
        automate_reducer.batch_reduction(reducer, compilers_dict, exec_dirs, identified_shaders, shader_tool)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Execute GLSLsmith framework and sort results")
    parser.add_argument('--seed', dest='seed', default=-1, type=int, help="Seed the random generator of GLSLsmith")
    parser.add_argument('--shader-count', dest='shadercount', default=50, type=int,
                        help="Specify the number of test per batch")
    parser.add_argument('--syntax-only', dest='syntaxonly', action='store_true',
                        help="Compile only the first compiler of the provided list to verify the syntax through "
                             "ShaderTrap")
    parser.add_argument('--continuous', dest='continuous', action='store_true',
                        help="Launch the bug finding in never ending mode")
    parser.add_argument('--reduce', dest="reduce", action="store_true",
                        help="Reduce interesting shaders at the end of a batch")
    parser.add_argument("--reducer", dest="reducer", default="glsl-reduce",
                        help="Enforce the reducer if reduction is applied, see --reduce")
    parser.add_argument('--double_run', dest='double_run', action='store_true',
                        help="Run the reconditioning step twice, reducing the number of wrappers on the second run")
    parser.add_argument('--glsl-only', dest="glsl_only", action="store_true",
                        help="Generate the files, recondition them on the go and split out the glsl shader out of the "
                             "harness")

    ns, exec_dirs, compilers_dict, reducer, shader_tool = env_setup(parser)
    batch_nb = 1

    # Validate compilers on an empty program instance
    if shader_tool.name != "shadertrap":
        print("Impossible to validate the compilers if the host language is not shadertrap")
    else:
        for compiler in compilers_dict.values():
            validate_compiler(exec_dirs.execdir, compiler, shader_tool)
        print("Compilers validated")

    while batch_nb == 1 or ns.continuous:
        print("Batch " + str(batch_nb))
        batch_nb += 1
        exec_glslsmith(exec_dirs, compilers_dict, reducer, shader_tool, ns.seed, ns.shadercount, ns.syntaxonly,
                       ns.reduce, ns.double_run, ns.glsl_only)


if __name__ == "__main__":
    main()
