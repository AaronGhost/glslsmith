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

from scripts.utils.file_utils import get_compiler_name, get_seed, concatenate_files, find_file


def test_concatenate_files(tmpdir):
    buffer_1 = tmpdir.join("buffer_1.txt")
    buffer_1.write("buffer_1")
    buffer_2 = tmpdir.join("buffer_2.txt")
    buffer_2.write("buffer_2")
    buffer_n = tmpdir.join("buffer_n.txt")
    buffer_n.write("buffer_n")
    not_buf = tmpdir.join("not_buf.txt")
    not_buf.write("not_buf")
    res = tmpdir.join("result.txt")
    concatenate_files(str(res), [str(buffer_1), str(buffer_2), str(buffer_n), str(not_buf)])
    assert res.read() == "buffer_1buffer_2buffer_n"


def test_find_file(tmpdir):
    tmpdir.join("buffer_1.txt").write("1")
    tmpdir.join("buffer_2.txt").write("2")
    tmpdir.join("result.txt").write("3")
    files = find_file(str(tmpdir), "buffer")
    assert len(files) == 2
    assert "buffer_1.txt" in files
    assert "buffer_2.txt" in files


@pytest.mark.parametrize("buffer_name, compiler_name",
                         [("whatever/nvidia_0.txt", "nvidia"), ("vulkan_intel_522.txt", "vulkan_intel")])
def test_get_compiler_name(buffer_name, compiler_name):
    assert get_compiler_name(buffer_name) == compiler_name


@pytest.mark.parametrize("buffer_name, seed",
                         [("whatever/nvidia_0.txt", "0"), ("vulkan_intel_522.txt", "522")])
def test_get_seed(buffer_name, seed):
    assert get_seed(buffer_name) == seed
