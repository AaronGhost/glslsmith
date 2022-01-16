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
from subprocess import run

from common import env_setup, clean_files
from splitter_merger import split


def find_shader_main_body(glsl_text):
    glsl_reg = re.compile(r"void main\(\)\n{(.*)}", re.DOTALL)
    match_object = glsl_reg.search(glsl_text)
    return match_object.group(0)


def report_wrapper_call(main_text):
    return len(re.findall("SAFE", main_text))


def print_file_report(shader_file):
    with open(shader_file, "r") as f:
        line_count = 1
        bytes_count = 0
        for line in f:
            if line != "\n":
                line_count += 1
                bytes_count += len(line)
    print("Lines: " + str(line_count))

    # Report the number of bytes in the current code
    print("Bytes: " + str(bytes_count))

    # Report the number of wrapper calls in the current code
    with open(shader_file, "r") as g:
        wrapper_count = report_wrapper_call(find_shader_main_body(g.read()))
    print("Wrapper calls:" + str(wrapper_count))


def main():
    parser = argparse.ArgumentParser(description="Provides statistics about a selected shader")
    parser.add_argument('--shader-name', dest='shader', default='test.shadertrap',
                        help="Specify the shader name to give stats on (by default: test.shadertrap)")
    ns, exec_dirs, _, _, shader_tool = env_setup(parser)

    harness_file = r'tmp' + shader_tool.file_extension
    shader_file = r'tmp.glsl'

    # Post process the shader
    cmd = ["mvn", "-f", exec_dirs.graphicsfuzz + "pom.xml", "-pl", "glslsmith", "-q", "-e", "exec:java",
           "-Dexec.mainClass=com.graphicsfuzz.PostProcessingHandler"]
    args = r'-Dexec.args=--src ' + str(ns.shader) + r' --dest ' + harness_file
    cmd += [args]
    process_return = run(cmd, capture_output=True, text=True)
    if "SUCCESS!" not in process_return.stdout:
        print(process_return.stderr)
        print(process_return.stdout)
        print(ns.shader + " cannot be parsed for post-processing")
        exit(1)

    # Split the shader from the embedding code
    split(shader_tool, harness_file, shader_file)

    # Report the number of lines and bytes in the current code
    print_file_report(shader_file)

    # Delete the temp files and the temp shader
    clean_files("./", [harness_file, shader_file])
    exit(0)


if __name__ == "__main__":
    main()
