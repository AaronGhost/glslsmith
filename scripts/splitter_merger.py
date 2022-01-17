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
import re
import sys

import common


def get_glslcode_from_shadertrap(shadertrap_text):
    shadertrap_reg = re.compile(r".*DECLARE_SHADER shader KIND COMPUTE\n(.*)END\n.*", re.DOTALL)
    match_object = shadertrap_reg.match(shadertrap_text)
    return match_object.group(1)


def get_glslcode_from_amber(amber_text):
    amber_reg = re.compile(r"SHADER compute computeShader GLSL\n(.*?)END\n", re.DOTALL)
    match_object = amber_reg.search(amber_text)
    return match_object.group(1)


def get_glslcode(shader_tool, text):
    if shader_tool.name == "shadertrap":
        glsl_lines = get_glslcode_from_shadertrap(text)
        return glsl_lines
    elif shader_tool.name == "amber":
        glsl_lines = get_glslcode_from_amber(text)
        return glsl_lines
    else:
        print("Host format not recognized")
        exit(1)


def split(shader_tool, source_file, output_file):
    f = open(source_file, "r")
    lines = f.read()
    f.close()
    g = open(output_file, "w")
    g.write(get_glslcode(shader_tool, lines))
    g.close()


def merge(shader_tool, harness_file, shader_file):
    g = open(shader_file, "r")
    lines = g.read()
    g.close()
    f = open(harness_file, 'r')
    output_lines = f.read()
    f.close()
    f = open(harness_file, "w")
    f.write(output_lines.replace(get_glslcode(shader_tool, output_lines), lines))
    f.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extracting tool to get a glsl script from shadertrap or change the inner shader of a shadertrap "
                    "code")
    parser.add_argument("--split", dest="split_file", nargs=2,
                        help="first argument is the original shadertrap code, second is the resulting glsl code "
                             "location")
    parser.add_argument("--merge", dest="merge_files", nargs=2,
                        help="first argument is the shadertrap code, second is the glsl code")
    ns, _, _, _, shader_tool = common.env_setup(parser)
    ns = parser.parse_args(sys.argv[1:])

    if not ns.split_file and not ns.merge_files:
        print("Please precise the attempted operation, see the commandline option --help for more details")
    if ns.split_file and ns.merge_files:
        print("Please provide only one operation at a time, see --help for the available operations")
    if ns.split_file:
        split(shader_tool, ns.split_file[0], ns.split_file[1])
    if ns.merge_files:
        merge(shader_tool, ns.merge_files[0], ns.merge_files[1])


if __name__ == "__main__":
    main()
