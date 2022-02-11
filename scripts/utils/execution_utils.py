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
import shutil
import subprocess
import sys
from subprocess import run

from utils.Compiler import Compiler
from utils.DirSettings import DirSettings
from utils.Reducer import Reducer
from utils.ShaderTool import ShaderTool
from utils.file_utils import find_buffer_file, clean_files, concatenate_files


def build_compiler_dict(compilers, restrict_compilers):
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
    parser.add_argument('--host', dest='host', default="shadertrap",
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


def single_compile(compiler, shader_to_compile, shader_tool, timeout, run_type, verbose=False):
    try:
        if compiler.type == "android":
            run(["adb", "push", shader_to_compile, "/data/local/tmp/test" + shader_tool.file_extension],
                capture_output=True, text=True)
            # The Android ShaderTrap binary is assumed to be present at /data/local/tmp
            if shader_tool.name == "amber":
                amber_command = "./amber -d"
                for buffer_name, descriptor_set, binding in find_amber_buffers(shader_to_compile):
                    amber_command += " -b " + buffer_name + " -B " + binding
                amber_command += " test.amber"
                process_return = run(["adb", "shell", "cd /data/local/tmp && " + amber_command], capture_output=True,
                                     text=True,
                                     timeout=timeout)
            else:
                process_return = run(["adb", "shell",
                                      "cd /data/local/tmp && ./shadertrap --require-vendor-renderer-substring "
                                      + compiler.renderer + " test.shadertrap"], capture_output=True, text=True,
                                     timeout=timeout)
            if run_type == "add_id":
                run(["adb", "pull", "ids.txt"], capture_output=True, text=True)
                run(["adb", "shell", "rm", "/data/local/tmp/buffer_*"], capture_output=True, text=True)
            else:
                ls_return = run(["adb", "shell", "ls", "/data/local/tmp/buffer_*"], capture_output=True, text=True)
                for buffer_file in ls_return.stdout.split():
                    run(["adb", "pull", buffer_file], capture_output=True, text=True)
                run(["adb", "shell", "rm", "/data/local/tmp/buffer_*"], capture_output=True, text=True)
                run(["adb", "shell", "rm", "/data/local/tmp/test" + shader_tool.file_extension], capture_output=True,
                    text=True)
        else:
            # Execute the correct cmd command
            if shader_tool.name == "amber":
                # TODO only the last buffer_name is effectively dumped (contain multiple binding) => b token useless
                cmd_ending = [shader_tool.path, "-d"]

                if run_type == "add_id":
                    buffer, descriptor_set, binding = find_amber_buffers(shader_to_compile)[0]
                    cmd_ending += ["-b", "buffer_ids.txt", "-B", binding]
                else:
                    for buffer_name, descriptor_set, binding in find_amber_buffers(shader_to_compile):
                        cmd_ending += ["-b", buffer_name, "-B", binding]
                cmd_ending.append(shader_to_compile)

            else:
                cmd_ending = [shader_tool.path, "--require-vendor-renderer-substring", compiler.renderer,
                              shader_to_compile]
            cmd = compiler.build_exec_env() + cmd_ending
            if verbose:
                print("Shadertrap command: " + " ".join(cmd))
            process_return = run(cmd, capture_output=True, text=True, timeout=timeout)
            if run_type == "add_id":
                if os.path.isfile("buffer_ids.txt"):
                    shutil.move("buffer_ids.txt", "ids.txt")
                    buffer_files = find_buffer_file(os.getcwd())
                    clean_files(os.getcwd(), buffer_files)
                else:
                    open("ids.txt", 'a').close()

    # Catch timeouts (post-processed shaders should not contain any)
    except subprocess.TimeoutExpired:
        return False, True, "timeout"
    # Detect error at compilation time
    if (shader_tool.name == "shadertrap" and 'SUCCESS!' not in process_return.stderr) or \
            (shader_tool.name == "amber" and "1 pass" not in process_return.stdout):
        message = ""
        # Output compilation error messages
        if process_return.stdout != "":
            print(process_return.stdout)
            message += process_return.stdout
        if process_return.stderr != "":
            print(process_return.stderr)
            message += process_return.stderr
        return True, False, message

    return False, False, "no_crash"


def execute_compilation(compilers_dict, graphicsfuzz, shader_tool, shadername, output_seed="", move_dir="./",
                        verbose=False,
                        timeout=10, double_run=False, postprocessing=True):
    no_compile_errors = []
    # Verify that the file exists
    if not os.path.isfile(shadername):
        print(shadername + " not found")
        return [False for _ in compilers_dict]
    resulting_buffers = []
    # Call postprocessing using java
    shader_to_compile = shadername
    run_type = "standard"
    if postprocessing:
        cmd = ["mvn", "-f", graphicsfuzz + "pom.xml", "-pl", "glslsmith", "-q", "-e", "exec:java",
               "-Dexec.mainClass=com.graphicsfuzz.PostProcessingHandler"]
        args = r'-Dexec.args=--src ' + str(shadername) + r' --dest tmp' + shader_tool.file_extension
        if double_run:
            args += r' --id_wrappers'
        cmd += [args]
        if verbose:
            print("Reconditioning command: " + " ".join(cmd))
        process_return = run(cmd, capture_output=True, text=True)
        # print(process_return.stderr)
        # print(process_return.stdout)
        if "SUCCESS!" not in process_return.stdout:
            print(process_return.stderr)
            print(process_return.stdout)
            print(shadername + " cannot be parsed for post-processing")
            return [False for _ in compilers_dict]
        shader_to_compile = "tmp" + shader_tool.file_extension

        # Call the compilation for a single compiler in dual mode
        if double_run:
            # Produce the ids file for the second run
            compiler_name = next(iter(compilers_dict))
            compiler = compilers_dict[compiler_name]
            crash_result, timeout_result, message = single_compile(compiler, shader_to_compile, shader_tool,
                                                                   timeout, "add_id")
            run_type = "reduced"

            # Verify that no execution error occurred and fallback if necessary
            if crash_result or timeout_result:
                print("Execution error on shader " + shadername + " with " + compiler.name
                      + " and added ids, falling back on standard run")
                # print(message)
                run_type = "standard"
            else:
                # Post-process in without useless wrappers
                cmd = ["mvn", "-f", graphicsfuzz + "pom.xml", "-pl", "glslsmith", "-q", "-e", "exec:java",
                       "-Dexec.mainClass=com.graphicsfuzz.PostProcessingHandler"]
                args = r'-Dexec.args=--src ' + str(shadername) + r' --dest tmp' + str(
                    shader_tool.file_extension) + r' --reduce_wrappers ids.txt'
                cmd += [args]
                if verbose:
                    print("Reconditioning command: " + " ".join(cmd))
                process_return = run(cmd, capture_output=True, text=True)
                # print(process_return.stderr)
                # print(process_return.stdout)
                if "SUCCESS!" not in process_return.stdout:
                    # print(process_return.stderr)
                    # print(process_return.stdout)
                    print(shadername + " cannot be parsed with the second run, error")
                    return [False for _ in compilers_dict]
        else:
            run_type = "standard"

    # Call the compilation for each available compiler in single mode or dual mode
    for compiler_name in compilers_dict:
        # Specify the buffers output name (if a seed is given it is added in the name)
        if output_seed != "":
            file_result = "buffer_" + compiler_name + "_" + str(output_seed) + ".txt"
        else:
            file_result = "buffer_" + compiler_name + ".txt"
        # Register the resulting buffer as a result instead of a temporary buffer (ie: buffer_1 etc...)
        resulting_buffers.append(file_result)

        compiler = compilers_dict[compiler_name]

        crash_result, timeout_result, message = single_compile(compiler, shader_to_compile, shader_tool, timeout,
                                                               run_type)
        no_compile_errors.append(message)
        if timeout_result:
            print("Timeout reached on shader " + shadername + " with " + compiler.name)
            # Write timeout as buffer value to permit direct buffer comparison in reduction for example etc...
            file = open(file_result, 'w')
            file.write("timeout")
            # Perform the copy of the file if the final buffer is saved somewhere else
            if move_dir != './':
                shutil.move(file_result, move_dir)
                clean_files(os.getcwd(), file_result)
            continue

        if crash_result:
            if verbose:
                print("Execution error on shader " + shadername + " with " + compiler.name)
                print(message)

        # Concatenate files to a single output per test
        buffer_files = find_buffer_file(os.getcwd())
        # Exclude combined files from concatenation and removal
        buffer_files = [file for file in buffer_files if file not in resulting_buffers]
        concatenate_files(file_result, buffer_files)
        # Move the results to the dumpbuffer
        if move_dir != './':
            shutil.move(file_result, move_dir)
            buffer_files.append(file_result)
        clean_files(os.getcwd(), buffer_files)
        if double_run:
            clean_files(os.getcwd(), ["ids.txt"])
    return no_compile_errors
