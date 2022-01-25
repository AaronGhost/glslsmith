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

from scripts.stats_buffer import report_line_nb, get_compiler_name_from_buffer


@pytest.mark.parametrize("filename, result", [("shader_1.shadertrap", "44"), ("shader_2.shadertrap", "36"),
                                              ("missing.shadertrap", "missing file")])
def test_report_line_nb(filename, result):
    assert report_line_nb("testdata/stats_buffer/" + filename) == result


@pytest.mark.parametrize("buffer_name, compiler_name",
                         [("whatever/nvidia_0.txt", "nvidia"), ("vulkan_intel_522.txt", "vulkan_intel")])
def test_get_compiler_name_from_buffer(buffer_name, compiler_name):
    assert get_compiler_name_from_buffer(buffer_name) == compiler_name
