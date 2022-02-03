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

import pytest

from scripts.stats_buffer import report_line_nb, extract_seed_from_buffer_files, stats_buffers
from scripts.utils.Compiler import Compiler
from scripts.utils.ShaderTool import ShaderTool


@pytest.mark.parametrize("filename, result", [("shader_1.shadertrap", "43"), ("shader_2.shadertrap", "35"),
                                              ("missing.shadertrap", "missing file")])
def test_report_line_nb(filename, result):
    assert report_line_nb("testdata/stats_buffer/" + filename) == result


@pytest.mark.parametrize("file_list, unique_seed",
                         [(["a_0.txt", "a_1.txt", "a_2.txt", "b_0.txt", "b_1.txt", "b_2.txt"], ["0", "1", "2"]),
                          (["a_x_0.txt", "b_0.txt", "a_x_1.txt", "b_x_1.txt", "a_0.txt", "a_1.txt", "a_150.txt",
                            "a_x_150.txt", "a_x_444.txt"]
                           , ["0", "1", "150", "444"])])
def test_extract_seed_from_buffer_files(file_list, unique_seed):
    assert extract_seed_from_buffer_files(file_list) == unique_seed


def verify_outputs(capsys, lines):
    outputs = capsys.readouterr()
    assert len(outputs.out.splitlines()) == len(lines)
    for line in lines:
        assert line in str(outputs.out)


def test_stats_buffers_and_main(capsys):
    # Prepare compilers for the scenario
    compiler_dict = {"a": Compiler("a", "a", "angle", "", "", []),
                     "b": Compiler("b", "b", "independent", "", "", []),
                     "c": Compiler("c", "c", "angle", "", "", []),
                     "d": Compiler("d", "d", "independent", "", "", []),
                     "a_x": Compiler("a_x", "a_x", "angle", "", "", [])}
    shadertools = [ShaderTool("shadertrap", "shadertrap/shadertrap", ".shadertrap")]

    # Lines that should be in the normal output
    lines = ["12 different seeds\n",
             "Group: a, lines: 12, seed: 0\n",
             "Group: a, lines: 15, seed: 1\n",
             "Group: angle, lines: 18, seed: 2\n",
             "Group: more than two, lines: 21, seed: 3\n",
             "Group: c, lines: 14, seed: 4\n",
             "Group: angle, lines: 9, seed: 5\n",
             "Group: d, lines: 17, seed: 15\n",
             "Group: a, lines: 4, seed: 333\n",
             "Group: more than two, lines: 5, seed: 522\n",
             "Group: more than two, lines: 2, seed: 2358\n",
             "Group: a_x, lines: 13, seed: 9999\n",
             "========= SUMMARY ================================================================\n",
             "a different values: 3\n",
             "b different values: 1\n",
             "c different values: 1\n",
             "d different values: 1\n",
             "a_x different values: 1\n",
             "angle different values: 2\n",
             "more than two groups of values: 3\n"]

    # All lines from the normal output should be in, the more than two group each carry an extra line before hand
    verbose_lines = lines.copy()
    verbose_lines[4] = "[['a', 'a_x'], ['b', 'c'], ['d']]\nGroup: more than two, lines: 21, seed: 3\n"
    verbose_lines[9] = "[['a'], ['a_x'], ['b'], ['c'], ['d']]\nGroup: more than two, lines: 5, seed: 522\n"
    verbose_lines[10] = "[['a', 'b', 'a_x'], ['c', 'd']]\nGroup: more than two, lines: 2, seed: 2358\n"

    # Test for the length of the outputs and then for all "lines" contained in it
    # Test without verbose
    stats_buffers("testdata/keptbuf/", "testdata/keptshad/", compiler_dict, shadertools, False)
    verify_outputs(capsys, lines)

    # Test with verbose
    stats_buffers("testdata/keptbuf/", "testdata/keptshad/", compiler_dict, shadertools, True)
    verify_outputs(capsys, verbose_lines)