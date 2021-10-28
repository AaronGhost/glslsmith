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

import filecmp
import re
import shutil
import subprocess
import sys
from subprocess import run
from xml.dom import minidom
import os


class ShaderTool:
    def __init__(self, name, path, file_extension):
        self.name = name
        self.path = path
        self.file_extension = file_extension


def load_shader_tools(filename):
    xmldoc = minidom.parse(filename)
    shadertools_xml = xmldoc.getElementsByTagName("shadertool")
    shadertools = []
    for shadertool in shadertools_xml:
        name = shadertool.getElementsByTagName("name")[0].childNodes[0].data
        path = shadertool.getElementsByTagName("path")[0].childNodes[0].data
        file_extension = shadertool.getElementsByTagName("extension")[0].childNodes[0].data
        shadertools.append(ShaderTool(name, path, file_extension))
    return shadertools


class DirSettings:
    def __init__(self, graphcisfuzz, execdir, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir):
        self.graphicsfuzz = graphcisfuzz
        self.execdir = execdir
        self.shaderoutput = shaderoutput
        self.dumpbufferdir = dumpbufferdir
        self.keptbufferdir = keptbufferdir
        self.keptshaderdir = keptshaderdir


def load_dir_settings(filename):
    xmldoc = minidom.parse(filename)
    dirs = xmldoc.getElementsByTagName("dirsettings")[0]
    graphicsfuzz = dirs.getElementsByTagName("graphicsfuzz")[0].childNodes[0].data
    execdir = dirs.getElementsByTagName("execdir")[0].childNodes[0].data
    shaderoutput = dirs.getElementsByTagName("shaderoutput")[0].childNodes[0].data
    dumpbufferdir = dirs.getElementsByTagName("dumpbufferdir")[0].childNodes[0].data
    keptbufferdir = dirs.getElementsByTagName("keptbufferdir")[0].childNodes[0].data
    keptshaderdir = dirs.getElementsByTagName("keptshaderdir")[0].childNodes[0].data
    return DirSettings(graphicsfuzz,execdir, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir)

class Compiler:
    available_syscode = 1

    def __init__(self,name, renderer, type, ldpath, vkfilename, othervens):
        self.name = name
        self.renderer = renderer
        self.type = type
        self.ldpath = ldpath
        self.vkfilename = vkfilename
        self.otherenvs = othervens
        self.compilercode = Compiler.available_syscode
        Compiler.available_syscode += 1

    def __str__(self):
        return self.name


def load_compilers_settings(filename):
    xmldoc = minidom.parse(filename)
    compilers = []
    compilersxml = xmldoc.getElementsByTagName("compiler")
    for compiler in compilersxml:
        name = compiler.getElementsByTagName("name")[0].childNodes[0].data
        renderer = compiler.getElementsByTagName("renderer")[0].childNodes[0].data
        type = compiler.getElementsByTagName("type")[0].childNodes[0].data
        ldpath = compiler.getElementsByTagName("LD_LIBRARY_PATH")[0].childNodes[0].data
        vkfilename = compiler.getElementsByTagName("VK_ICD_FILENAMES")[0].childNodes[0].data
        otherenvs = []
        otherenvsxml = compiler.getElementsByTagName("otherenvs")
        if otherenvsxml.length != 1:
            nb_envs  = int(otherenvsxml.getElementByTagName("length")[0].childNodes[0].data)
            for i in range(nb_envs):
                otherenvs.append(otherenvsxml.getElementByTagName("env_"+str(i))[0].childNodes[0].data)
        compilers.append(Compiler(name, renderer, type, ldpath, vkfilename, otherenvs))
    return compilers


class Reducer:
    def __init__(self, reducer_name, reducer_command, interesting_test, reducer_input_name, reducer_output_name, extra_files):
        self.name = reducer_name
        self.command = reducer_command
        self.interesting_test = interesting_test
        self.input_file = reducer_input_name
        self.output_files = reducer_output_name
        self.extra_files_to_build = extra_files


def load_reducers_settings(filename):
    xmldoc = minidom.parse(filename)
    reducers = []
    reducerxml = xmldoc.getElementsByTagName("reducer")
    for reducer in reducerxml:
        name = reducer.getElementsByTagName("name")[0].childNodes[0].data
        reducer_command = reducer.getElementsByTagName("command")[0].childNodes[0].data
        interesting_test = reducer.getElementsByTagName("interesting")[0].childNodes[0].data
        input_name = reducer.getElementsByTagName("input_file")[0].childNodes[0].data
        output_name = reducer.getElementsByTagName("output_file")[0].childNodes[0].data
        extra_files = []
        extra_file_xml = reducer.getElementsByTagName("extra_files")
        if extra_file_xml.length != 1:
            nb_files = int(extra_file_xml.getElementByTagName("length")[0].childNodes[0].data)
            for i in range(nb_files):
                extra_files.append(extra_file_xml.getElementByTagName("file_"+str(i)[0]).childNodes[0].data)
        reducers.append(Reducer(name, reducer_command, interesting_test, input_name, output_name, extra_files))
    return reducers


def concatenate_files(outputname, files):
    out = b''
    for fileadd in files:
        if 'buffer' in fileadd:
            with open(fileadd, 'rb') as f:
                out += f.read()
    with open(outputname, 'wb') as dumpfile:
        dumpfile.write(out)


def clean_files(current_dir, files_list):
    ref = os.getcwd()
    os.chdir(current_dir)
    for file in files_list:
        if os.path.isfile(file):
            os.remove(file)
    os.chdir(ref)


def build_env_from_compiler(compiler):
    cmd_env = []
    if compiler.ldpath != " " or compiler.otherenvs != [] or compiler.type == "angle":
        cmd_env.append("env")
        if compiler.ldpath != " ":
            cmd_env.append("LD_LIBRARY_PATH="+compiler.ldpath)
        if compiler.type == "angle":
            cmd_env.append("ANGLE_DEFAULT_PLATFORM=vulkan")
        if compiler.vkfilename != " ":
            cmd_env.append("VK_ICD_FILENAMES="+compiler.vkfilename)
        for otherenv in compiler.otherenvs:
            cmd_env.append(otherenv)
    return cmd_env


def find_file(current_dir, prefix):
    file_list = os.listdir(current_dir)
    buffer_files = []
    if current_dir[-1] != "/":
        current_dir += "/"
    for file in file_list:
        if os.path.isfile(current_dir + file):
            if prefix in file:
                buffer_files.append(file)
    return buffer_files


def find_buffer_file(current_dir):
    return find_file(current_dir, "buffer_")


def find_test_file(current_dir):
    return find_file(current_dir, "test")


def comparison_helper(files):
    comparison_values = []
    for file in files:
        comparison_values.append([file])

    i = 0
    while i < len(comparison_values) - 1:
        reference = comparison_values[i]
        for next_files in comparison_values[i+1:]:
            if next_files != reference[0]:
                if filecmp.cmp(reference[0],next_files[0],False):
                    reference += next_files
                    comparison_values.remove(next_files)
        i += 1

    return comparison_values


def env_setup(parser):
    # Add the configuration file and the host parameters to all scripts
    parser.add_argument('--config-file', dest='config', default="config.xml",
                        help="specify a different configuration file from the default")
    parser.add_argument('--host', dest='host', default="shadertrap",
                        help="Specify the host language in which to embed the shader code")
    ns = parser.parse_args(sys.argv[1:])

    # Parse directory config
    exec_dirs = load_dir_settings(ns.config)

    # Parse the compiler config to a compiler dictionary
    compilers = load_compilers_settings(ns.config)
    compilers_dict = {}
    for compiler in compilers:
        if not hasattr(ns, "restrict_compilers") or not ns.restrict_compilers or compiler in ns.restrict_compilers:
            compilers_dict[compiler.name] = compiler

    # Parse available reducers
    reducers = load_reducers_settings(ns.config)
    if len(reducers) == 0:
        exit("No reducer has been declared at installation, please rerun installation or edit the configuration file")
    reducer = reducers[0]
    if hasattr(ns, "reducer") and ns.reducer != "":
        reducer_found = False
        for existing_reducer in reducers:
            if existing_reducer.name == ns.reducer:
                reducer = existing_reducer
                reducer_found = True
        if not reducer_found:
            exit("No reducer named " + str(ns.reducer) + " configured")

    # Parse host language configuration
    shader_tools = load_shader_tools(ns.config)
    shader_tool = shader_tools[0]
    shader_tool_found = False
    for possible_tool in shader_tools:
        if possible_tool.name == ns.host:
            shader_tool_found = True
            shader_tool = possible_tool
    if not shader_tool_found:
        print("Host tool not configured / recognized defaulting to: " + shader_tool.name)

    # Ensure that values are taken from the root
    os.chdir(exec_dirs.execdir)

    return ns, exec_dirs, compilers_dict, reducer, shader_tool


def find_amber_buffers(shader_to_compile):
    with open(shader_to_compile) as f:
        return re.findall(r"BUFFER (.+) AS storage DESCRIPTOR_SET (.*) BINDING (.*)", f.read())


def execute_compilation(compilers_dict, graphicsfuzz, shader_tool, shadername, output_seed="", move_dir="./", verbose=False,
                        timeout=10, postprocessing=True):
    no_compile_errors = []
    # Verify that the file exists
    if not os.path.isfile(shadername):
        print(shadername + " not found")
        return [False for _ in compilers_dict]
    resulting_buffers = []
    # Call postprocessing using java
    shader_to_compile = shadername
    if postprocessing:
        cmd = ["mvn", "-f", graphicsfuzz+"pom.xml", "-pl", "glslsmith", "-q", "-e", "exec:java",
               "-Dexec.mainClass=com.graphicsfuzz.PostProcessingHandler" ]
        args = r'-Dexec.args=--src ' + str(shadername) + r' --dest tmp' + shader_tool.file_extension
        cmd += [args]
        process_return = run(cmd, capture_output=True, text=True)
        #print(process_return.stderr)
        #print(process_return.stdout)
        if "SUCCESS!" not in process_return.stdout:
            print(process_return.stderr)
            print(process_return.stdout)
            print(shadername + " cannot be parsed for post-processing")
            return [False for _ in compilers_dict]
        shader_to_compile = "tmp" + shader_tool.file_extension

    # Call the compilation for each available compiler
    for compiler_name in compilers_dict:
        # Specify the buffers output name (if a seed is given it is added in the name)
        if output_seed != "":
            file_result = "buffer_"+ compiler_name + "_" + str(output_seed) + ".txt"
        else:
            file_result = "buffer_"+ compiler_name + ".txt"
        # Register the resulting buffer as a result instead of a temporary buffer (ie: buffer_1 etc...)
        resulting_buffers.append(file_result)

        try:
            compiler = compilers_dict[compiler_name]
            if compiler.type == "android":
                run(["adb", "push", shader_to_compile, "/data/local/tmp/test" + shader_tool.file_extension],
                    capture_output=True, text=True)
                # The Android ShaderTrap and Amber binaries are assumed to be present at /data/local/tmp
                if shader_tool.name == "amber":
                    amber_command = "./amber -d"
                    for buffer_name, descriptor_set, binding in find_amber_buffers(shader_to_compile):
                        amber_command += " -b " + buffer_name + " -B " + binding
                    amber_command += " test.amber"
                    process_return = run(["adb", "shell", "cd /data/local/tmp && " + amber_command], capture_output=True, text=True,
                                         timeout=timeout)
                else:
                    process_return = run(["adb", "shell",
                                          "cd /data/local/tmp && ./shadertrap --require-vendor-renderer-substring "
                                          + compiler.renderer + " test.shadertrap"], capture_output=True, text=True,
                                         timeout=timeout)
                ls_return = run(["adb", "shell", "ls", "/data/local/tmp/buffer_*"], capture_output=True, text=True)
                for buffer_file in ls_return.stdout.split():
                    run(["adb", "pull", buffer_file], capture_output=True, text=True)
                run(["adb", "shell", "rm", "/data/local/tmp/buffer_*"], capture_output=True, text=True)
                run(["adb", "shell", "rm", "/data/local/tmp/test" + shader_tool.file_extension], capture_output=True,
                    text=True)
            else:
                # Execute the correct cmd command
                if shader_tool.name == "amber":
                    buffers = find_amber_buffers(shader_to_compile)
                    cmd_ending = [shader_tool.path, "-d"]
                    for buffer_name, descriptor_set, binding in buffers:
                        cmd_ending += ["-b",buffer_name,"-B",binding]
                    cmd_ending.append(shader_to_compile)
                else:
                    cmd_ending = [shader_tool.path, "--require-vendor-renderer-substring",compiler.renderer,
                                  shader_to_compile]
                cmd = build_env_from_compiler(compiler) + cmd_ending
                process_return = run(cmd, capture_output=True, text=True, timeout=timeout)
        # Catch timeouts (post-processed shaders should not contain any)
        except subprocess.TimeoutExpired:
            print("Timeout reached on shader " + shadername + " with " + compiler_name)
            no_compile_errors.append("timeout")
            # Write timeout as buffer value to permit direct buffer comparison in reduction for example etc...
            file = open(file_result, 'w')
            file.write("timeout")
            # Perform the copy of the file if the final buffer is saved somewhere else
            if move_dir != './':
                shutil.move(file_result, move_dir)
                clean_files(os.getcwd(),file_result)
            continue
        # Detect error at compilation time
        if (shader_tool.name == "shadertrap" and 'SUCCESS!' not in process_return.stderr) or \
                (shader_tool.name == "amber" and "1 pass" not in process_return.stdout):
            if verbose:
                print("Execution error on shader " + shadername + " with " + compiler.name)
            message = ""
            # Output compilation error messages
            if process_return.stdout != "":
                print(process_return.stdout)
                message += process_return.stdout
            if process_return.stderr != "":
                print(process_return.stderr)
                message += process_return.stderr
            no_compile_errors.append(message)
        else:
            no_compile_errors.append("no_crash")
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
    return no_compile_errors
