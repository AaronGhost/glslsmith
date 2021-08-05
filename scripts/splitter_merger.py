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
import sys

def split(source_file, output_file):
    f = open(source_file, "r")
    keeping_flag = False
    glsl_lines = ""
    lines = f.readlines()
    f.close()
    for line in lines:
        if "END" in line:
            keeping_flag = False
        if keeping_flag:
            glsl_lines += (line)
        if "DECLARE_SHADER shader KIND COMPUTE" in line:
            keeping_flag = True
    g = open(output_file, "w")
    g.write(glsl_lines)
    g.close()

def merge(harness_file, shader_file):
    g = open(shader_file, "r")
    code = ""
    for line in g.readlines():
        code += line
    g.close()
    shadertrap_code = ""
    f = open(harness_file, 'r')
    lines = f.readlines()
    f.close()
    keeping_flag = True
    for line in lines:
        if "END\n" in line:
            keeping_flag = True
            shadertrap_code += "\n"
        if keeping_flag:
            shadertrap_code += line
        if "DECLARE_SHADER shader KIND COMPUTE" in line:
            keeping_flag = False
            shadertrap_code += code
    f = open(harness_file, "w")
    f.write(shadertrap_code)
    f.close()

def main():
    parser = argparse.ArgumentParser(description="Extracting tool to get a glsl script from shadertrap or change the inner shader of a shadertrap code")
    parser.add_argument("--split", dest="split_file", nargs=2, help="first argument is the original shadertrap code, second is the resulting glsl code location")
    parser.add_argument("--merge", dest="merge_files", nargs=2, help="first argument is the shadertrap code, second is the glsl code")
    ns = parser.parse_args(sys.argv[1:])
    #os.chdir("../")
    if not ns.split_file and not ns.merge_files:
        print("Please precise the attempted operation, see the commandline option --help for more details")
    if ns.split_file and ns.merge_files:
        print("Please provide only one operation at a time, see --help for the available operations")
    if ns.split_file:
        split(ns.split_file[0], ns.split_file[1])
    if ns.merge_files:
        merge(ns.merge_files[0], ns.merge_files[1])


if __name__ == "__main__":
    main()
