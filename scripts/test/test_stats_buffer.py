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

import pytest

from scripts.common import Compiler, ShaderTool
from scripts.stats_buffer import report_line_nb, get_compiler_name, extract_seed_from_buffer_files, get_seed, \
    attribute_compiler_results, stats_buffers


@pytest.mark.parametrize("filename, result", [("shader_1.shadertrap", "43"), ("shader_2.shadertrap", "35"),
                                              ("missing.shadertrap", "missing file")])
def test_report_line_nb(filename, result):
    assert report_line_nb("testdata/stats_buffer/" + filename) == result


@pytest.mark.parametrize("buffer_name, compiler_name",
                         [("whatever/nvidia_0.txt", "nvidia"), ("vulkan_intel_522.txt", "vulkan_intel")])
def test_get_compiler_name(buffer_name, compiler_name):
    assert get_compiler_name(buffer_name) == compiler_name


@pytest.mark.parametrize("buffer_name, seed",
                         [("whatever/nvidia_0.txt", "0"), ("vulkan_intel_522.txt", "522")])
def test_get_compiler_name(buffer_name, seed):
    assert get_seed(buffer_name) == seed


@pytest.mark.parametrize("file_list, unique_seed",
                         [(["a_0.txt", "a_1.txt", "a_2.txt", "b_0.txt", "b_1.txt", "b_2.txt"], ["0", "1", "2"]),
                          (["a_x_0.txt", "b_0.txt", "a_x_1.txt", "b_x_1.txt", "a_0.txt", "a_1.txt", "a_150.txt",
                            "a_x_150.txt", "a_x_444.txt"]
                           , ["0", "1", "150", "444"])])
def test_extract_seed_from_buffer_files(file_list, unique_seed):
    assert extract_seed_from_buffer_files(file_list) == unique_seed


@pytest.mark.parametrize("results, group", [([["a", "b"], ["c"]], "c"),
                                            ([["a"], ["b"]], "a"),
                                            ([["a", "c"], ["b", "d"]], "angle"),
                                            ([["b", "d", "e"], ["a", "f"]], "angle"),
                                            ([["a", "b"], ["c", "d"]], "more than two"),
                                            ([["a"], ["b"], ["c"], ["d"]], "more than two")])
def test_attribute_compiler_results(results, group):
    compiler_dict = {"a": Compiler("a", "a", "angle", "", "", []),
                     "b": Compiler("b", "b", "independent", "", "", []),
                     "c": Compiler("c", "c", "angle", "", "", []),
                     "d": Compiler("d", "d", "independent", "", "", []),
                     "e": Compiler("e", "e", "independent", "", "", []),
                     "f": Compiler("f", "f", "angle", "", "", [])}
    assert attribute_compiler_results(results, compiler_dict) == group


def test_stats_buffers(capsys):
    # Prepare compilers for the scenario
    compiler_dict = {"a": Compiler("a", "a", "angle", "", "", []),
                     "b": Compiler("b", "b", "independent", "", "", []),
                     "c": Compiler("c", "c", "angle", "", "", []),
                     "d": Compiler("d", "d", "independent", "", "", []),
                     "a_x": Compiler("a_x", "a_x", "angle", "", "", [])}
    shadertools = [ShaderTool("shadertrap", "shadertrap/shadertrap", ".shadertrap")]

    # Lines that should be in the normal output
    lines = ["11 different seeds\n",
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
             "b different values: 0\n",
             "c different values: 1\n",
             "d different values: 1\n",
             "a_x different values: 1\n",
             "angle different values: 2\n",
             "more than two groups of values: 3\n"]

    # All lines from the normal output should be in, the more than two group each carry an extra line before hand
    verbose_lines = lines.copy()
    verbose_lines[4] = "[['a', 'a_x'], ['b', 'c'], ['d']]\nGroup: more than two, lines: 21, seed: 3\n"
    verbose_lines[9] = "[['a'], ['b'], ['c'], ['d'], ['a_x']]\nGroup: more than two, lines: 5, seed: 522\n"
    verbose_lines[10] = "[['a', 'b', 'a_x'], ['c', 'd']]\nGroup: more than two, lines: 2, seed: 2358\n"

    # Test for the length of the outputs and then for all "lines" contained in it
    stats_buffers("testdata/keptbuf/", "testdata/keptshad/", compiler_dict, shadertools, False)
    outputs = capsys.readouterr()
    assert len(outputs.out.splitlines()) == 20
    for line in lines:
        assert line in str(outputs.out)
    stats_buffers("testdata/keptbuf/", "testdata/keptshad/", compiler_dict, shadertools, True)
    outputs = capsys.readouterr()
    assert len(outputs.out.splitlines()) == 23
    for line in verbose_lines:
        assert line in str(outputs.out)
