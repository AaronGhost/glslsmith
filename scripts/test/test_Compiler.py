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

from scripts.utils.Compiler import Compiler


@pytest.fixture
def compilers_data():
    Compiler.available_syscode = 1
    yield {"a": Compiler("a", "a", "independent", " ", " ", []),
           "ba": Compiler("ba", "ba", "independent", "/ba/ba/", " ", []),
           "c": Compiler("c", "c", "angle", "angle/c/data", " ", []),
           "d_x": Compiler("d_x", "d", "angle", "angle/c/data", "c.json", []),
           "e": Compiler("e", "e", "independent", "en/", "end.json", ["WHATEVER=\"indep\"", "X=\"y\""]),
           "f": Compiler("f", "f", "angle", "en/", " ", ["WHATEVER=\"ang\"", "X=\"z\""]),
           "g": Compiler("g", "g", "angle", " ", "ga.json", [])}


@pytest.mark.parametrize("name, code", [("a", 1), ("ba", 2), ("c", 3), ("d_x", 4), ("e", 5), ("f", 6), ("g", 7)])
def test_unique_sys_code(compilers_data, name, code):
    assert compilers_data[name].compilercode == code


@pytest.mark.parametrize("name, env",
                         [("a", []),
                          ("ba", ["env", "LD_LIBRARY_PATH=/ba/ba/"]),
                          ("c", ["env", "LD_LIBRARY_PATH=angle/c/data", "ANGLE_DEFAULT_PLATFORM=vulkan"]),
                          ("d_x", ["env", "LD_LIBRARY_PATH=angle/c/data", "ANGLE_DEFAULT_PLATFORM=vulkan",
                                   "VK_ICD_FILENAMES=c.json"]),
                          ("e",
                           ["env", "LD_LIBRARY_PATH=en/", "VK_ICD_FILENAMES=end.json", "WHATEVER=\"indep\"",
                            "X=\"y\""]),
                          ("f",
                           ["env", "LD_LIBRARY_PATH=en/", "ANGLE_DEFAULT_PLATFORM=vulkan", "WHATEVER=\"ang\"",
                            "X=\"z\""]),
                          ("g", ["env", "ANGLE_DEFAULT_PLATFORM=vulkan", "VK_ICD_FILENAMES=ga.json"])])
def test_build_exec_env(compilers_data, name, env):
    exec_res = compilers_data[name].build_exec_env()
    assert exec_res == env


def test_load_compilers_settings():
    compilers = Compiler.load_compilers_settings("testdata/xml_files/compilers.xml")
    # Test first compiler
    compiler_1 = compilers[0]
    assert compiler_1.name == "aba"
    assert compiler_1.renderer == "ababa"
    assert compiler_1.type == "angle"
    assert compiler_1.ldpath == "/aba/build/lib/x86_64-linux-gnu"
    assert compiler_1.vkfilename == "/aba/build/lib/vk_aba.json"
    assert compiler_1.otherenvs == ["X=\"y\""]

    # Test second compiler
    compiler_2 = compilers[1]
    assert compiler_2.name == "aba_cus"
    assert compiler_2.renderer == "aba_ta"
    assert compiler_2.type == "independent"
    assert compiler_2.ldpath == "/abacus/build/lib/x86_64-linux-gnu"
    assert compiler_2.vkfilename == " "
    assert compiler_2.otherenvs == []
