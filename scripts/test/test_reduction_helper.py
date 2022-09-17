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

from scripts.reduction_helper import attribute_compilation_results


@pytest.mark.parametrize("results, expected",
                         [(["no_crash", "no_crash", "no_crash", "no_crash"], "0"),
                          (["no_crash", "no_crash", "no_crash", "timeout"], "2016"),
                          (["no_crash", "no_crash", "no_crash", "crash"], "1016"),
                          (["no_crash", "no_crash", "timeout", "crash"], "1016"),
                          (["no_crash", "no_crash", "timeout", "timeout"], "2024"),
                          (["no_crash", "no_crash", "crash", "crash"], "1024"),
                          (["crash", "crash", "crash", "crash"], "1000")])
def test_attribute_compilation_results(results, compilers_list, expected):
    assert attribute_compilation_results(results, compilers_list[0:4]) == expected
