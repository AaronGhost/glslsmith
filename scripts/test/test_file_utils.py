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

from scripts.utils.file_utils import get_compiler_name, get_seed


@pytest.mark.parametrize("buffer_name, compiler_name",
                         [("whatever/nvidia_0.txt", "nvidia"), ("vulkan_intel_522.txt", "vulkan_intel")])
def test_get_compiler_name(buffer_name, compiler_name):
    assert get_compiler_name(buffer_name) == compiler_name


@pytest.mark.parametrize("buffer_name, seed",
                         [("whatever/nvidia_0.txt", "0"), ("vulkan_intel_522.txt", "522")])
def test_get_compiler_name(buffer_name, seed):
    assert get_seed(buffer_name) == seed
