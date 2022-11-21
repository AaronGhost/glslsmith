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

import os
import re
import shlex
import shutil
import subprocess
import sys

from utils.Compiler import Compiler
from utils.DirSettings import DirSettings
from utils.Reducer import Reducer
from utils.ShaderTool import ShaderTool
from utils.file_utils import find_compiler_buffer_file, clean_files, concatenate_files, find_digit_buffer_file, ensure_abs_path
from utils.analysis_utils import comparison_helper


def build_compiler_dict(compilers, restrict_compilers=None):
    if restrict_compilers:
        return {compiler.name: compiler for compiler in compilers if compiler.name in restrict_compilers}
    else:
        return {compiler.name: compiler for compiler in compilers}


def select_reducer(reducers, reducer_name):
    if len(reducers) == 0:
        exit("No reducer has been declared at installation, please edit the configuration file")
    ans = next((x for x in reducers if x.name == reducer_name), reducers[0])
    if reducer_name != "" and ans.name != reducer_name:
        exit("Reducer " + reducer_name + " not found")
    return ans


def select_shader_tool(shader_tools, tool_name):
    ans = next((x for x in shader_tools if x.name == tool_name), shader_tools[0])
    if tool_name != "" and ans.name != tool_name:
        exit(tool_name + " not found")
    return ans


def env_setup(parser):
    # Add the configuration file and the host parameters to all scripts
    parser.add_argument('--config-file', dest='config', default="config.xml",
                        help="specify a different configuration file from the default")
    parser.add_argument('--host', dest='host', default="",
                        help="Specify the host language in which to embed the shader code")
    ns = parser.parse_args(sys.argv[1:])

    # Parse directory config
    exec_dirs = DirSettings.load_dir_settings(ns.config)

    # Parse the compiler config to a compiler dictionary
    compilers = Compiler.load_compilers_settings(ns.config)
    compilers_dict = build_compiler_dict(compilers, ns.restrict_compilers if hasattr(ns, "restrict_compilers") else [])

    # Parse available reducers
    reducers = Reducer.load_reducers_settings(ns.config)
    reducer = select_reducer(reducers, ns.reducer if hasattr(ns, "reducer") else "")

    # Parse host language configuration
    shader_tools = ShaderTool.load_shader_tools(ns.config)
    shader_tool = select_shader_tool(shader_tools, ns.host)

    # Ensure that values are taken from the root
    os.chdir(exec_dirs.execdir)

    return ns, exec_dirs, compilers_dict, reducer, shader_tool


def find_amber_buffers(shader_to_compile):
    with open(shader_to_compile) as f:
        return re.findall(r"BUFFER (.+) AS storage DESCRIPTOR_SET (.*) BINDING (.*)", f.read())


def prepare_amber_command(amber_tool_path, output_file, shader_name, add_id):
    original_amber_command = amber_tool_path + " -d -b " + output_file
    amber_command = original_amber_command
    for name, descriptor_set, binding in find_amber_buffers(shader_name):
        if add_id and name == "buffer_ids":
            return original_amber_command + " -B " + binding + " " + shader_name
        if not add_id and name != "buffer_ids":
            amber_command += " -B " + binding
    return amber_command + " " + shader_name


def prepare_shadertrap_command(shader_tool_path, renderer, shader_name):
    return shader_tool_path + " " + shader_name + " --require-vendor-renderer-substring \"" + renderer + "\""


def collect_process_return(process_return, check_value):
    message = process_return.stdout + process_return.stderr
    if check_value not in message:
        print(message)
        return False, message
    return True, message


def call_glslsmith_generator(graphicsfuzz, exec_dir, shadercount, output_directory, seed=-1, host="shadertrap"):
    cmd = [graphicsfuzz + "graphicsfuzz/target/graphicsfuzz/python/drivers/glslsmith-generator", "--shader-count",
           str(shadercount), "--output-directory", ensure_abs_path(exec_dir, output_directory)]
    if seed != -1:
        cmd += ["--seed", str(seed)]
    if host != "shadertrap":
        cmd += ["--printer", str(host)]
    return collect_process_return(subprocess.run(cmd, capture_output=True, text=True), "SUCCESS!")


def call_glslsmith_reconditioner(graphicsfuzz, exec_dir, shader, harness, run_type="standard"):
    cmd = [graphicsfuzz + "graphicsfuzz/target/graphicsfuzz/python/drivers/glslsmith-recondition", "--src",
           ensure_abs_path(exec_dir, str(shader)), "--dest", ensure_abs_path(exec_dir, harness)]
    if run_type == "add_id":
        cmd += ["--id_wrappers"]
    elif run_type == "reduced":
        cmd += ["--reduce_wrappers", ensure_abs_path(exec_dir, "buffer_results.txt")]
    return collect_process_return(subprocess.run(cmd, capture_output=True, text=True), "SUCCESS!")


def single_compile(exec_dir, compiler, shader_to_compile, shader_tool, timeout=10, run_type="standard", verbose=False):
    previous_location = os.getcwd()
    os.chdir(exec_dir)
    try:
        # Push the shader file to android
        if compiler.type == "android":
            subprocess.run(["adb", "push", shader_to_compile, "/data/local/tmp/" + shader_to_compile],
                           capture_output=True, text=True)
            # Construct the tool path
            tool_path = "./" + shader_tool.path.split("/")[-1]
        else:
            tool_path = shader_tool.path

        # Prepare the command depending on the tool path
        if shader_tool.name == "amber":
            cmd_ending = prepare_amber_command(tool_path, "buffer_results.txt", shader_to_compile, run_type == "add_id")
        else:
            cmd_ending = prepare_shadertrap_command(tool_path, compiler.renderer, shader_to_compile)

        # Execute the command
        if compiler.type == "android":
            process_return = subprocess.run(["adb", "shell", "cd /data/local/tmp && " + cmd_ending],
                                            capture_output=True, text=True, timeout=timeout)
            if verbose:
                print("adb shell cd /data/local/tmp && " + cmd_ending)
        else:
            process_return = subprocess.run(compiler.build_exec_env() + shlex.split(cmd_ending), capture_output=True,
                                            text=True, timeout=timeout)
            if verbose:
                print(" ".join(compiler.build_exec_env()) + cmd_ending)

        # Collect the result
        if compiler.type == "android":
            # Pull all buffers from android
            ls_return = subprocess.run(["adb", "shell", "ls", "/data/local/tmp/buffer_*"], capture_output=True,
                                       text=True)
            for buffer_file in ls_return.stdout.split():
                subprocess.run(["adb", "pull", buffer_file], capture_output=True, text=True)

            # Clean in the case of android
            subprocess.run(["adb", "shell", "rm", "/data/local/tmp/buffer_*", "/data/local/tmp/" + shader_to_compile],
                           capture_output=True, text=True)

    # Timeout case
    except subprocess.TimeoutExpired:
        with open("buffer_results.txt", 'w') as file:
            file.write("timeout")
            file.close()
        os.chdir(previous_location)
        return False, True, "timeout"

    # Detect error at compilation time
    if shader_tool.name == "amber":
        check_passed, message = collect_process_return(process_return, "1 pass")
    else:
        check_passed, message = collect_process_return(process_return, "SUCCESS!")
        if check_passed:
            if run_type == "add_id":
                shutil.move("buffer_ids.txt", "buffer_results.txt")
            else:
                buffer_files = find_digit_buffer_file(os.getcwd())
                # Exclude combined files from concatenation and removal
                concatenate_files("buffer_results.txt", buffer_files)
                clean_files(exec_dir, buffer_files)
    if not check_passed:
        with open("buffer_results.txt", 'w') as file:
            file.write("crash")
            file.close()

    # Return to location
    os.chdir(previous_location)
    return not check_passed, False, message if not check_passed else "no_crash"


def execute_compilation(compilers_dict, graphicsfuzz, exec_dir, shader_tool, shader_name, output_seed="", move_dir="./",
                        run_type="standard", timeout=10):
    no_compile_errors = []
    # Verify that the file exists
    if not os.path.isfile(ensure_abs_path(exec_dir, shader_name)):
        print(shader_name + " not found")
        return ["missing"] * len(compilers_dict)
    resulting_buffers = []
    shader_to_compile = ensure_abs_path(exec_dir, shader_name)
    # Call postprocessing using java if requested
    if run_type != "no_postprocessing":
        shader_to_compile = ensure_abs_path(exec_dir, "tmp" + shader_tool.file_extension)
        reconditioned, error = call_glslsmith_reconditioner(graphicsfuzz, exec_dir, str(shader_name),
                                                            shader_to_compile,
                                                            run_type)
        if not reconditioned:
            print(error)
            return ["failed_reconditioning"] * len(compilers_dict)

    file_result = ""
    # Call the compilation with a subset of compilers in add_id mode
    for compiler_name in compilers_dict:
        # Specify the buffers output name (if a seed is given it is added in the name)
        if output_seed != "":
            file_result = compiler_name + "_" + str(output_seed) + ".txt"
        else:
            file_result = compiler_name + ".txt"
        file_result = ensure_abs_path(exec_dir, file_result)
        # Register the resulting buffer as a result instead of a temporary buffer (ie: buffer_1 etc...)
        resulting_buffers.append(file_result)
        compiler = compilers_dict[compiler_name]
        crash_result, timeout_result, message = single_compile(exec_dir, compiler, shader_to_compile, shader_tool,
                                                               timeout, run_type)
        no_compile_errors.append(message)
        shutil.move(ensure_abs_path(exec_dir, "buffer_results.txt"), file_result)

    # Compare the different buffers obtained from the compilation if we need to rerun
    if run_type == "add_id":
        compiler_results = comparison_helper(resulting_buffers)

        # If the results are identical we can try the reduced wrappers version
        if len(compiler_results) == 1:
            shutil.move(file_result, ensure_abs_path(exec_dir, "buffer_results.txt"))
            # Recursive call with the reduced number of wrappers
            return execute_compilation(compilers_dict, graphicsfuzz, exec_dir, shader_tool, shader_name, output_seed,
                                       move_dir, "reduced", timeout)

    # Copy back the results
    if move_dir != "./":
        for buffer in resulting_buffers:
            shutil.move(buffer, move_dir)
    return no_compile_errors
