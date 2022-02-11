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
from scripts.utils.DirSettings import DirSettings
from scripts.utils.Reducer import Reducer
from scripts.utils.ShaderTool import ShaderTool


def pytest_addoption(parser):
    parser.addoption("--config_file", action="store")


@pytest.fixture(scope="session")
def conf(request):
    conf_path = request.config.getoption("--config_file")
    conf_dict = {"exec_dirs": DirSettings.load_dir_settings(conf_path),
                 "compilers": Compiler.load_compilers_settings(conf_path),
                 "reducers": Reducer.load_reducers_settings(conf_path),
                 "shadertools": ShaderTool.load_shader_tools(conf_path)}
    return conf_dict


@pytest.fixture(scope="session")
def compilers_list():
    Compiler.available_syscode = 1
    return [Compiler("a", "a", "independent", " ", " ", []),
            Compiler("ba", "ba", "independent", "/ba/ba/", " ", []),
            Compiler("c", "c", "angle", "angle/c/data", " ", []),
            Compiler("d_x", "d", "angle", "angle/c/data", "c.json", []),
            Compiler("e", "e", "independent", "en/", "end.json", ["WHATEVER=\"indep\"", "X=\"y\""]),
            Compiler("f", "f", "angle", "en/", " ", ["WHATEVER=\"ang\"", "X=\"z\""]),
            Compiler("g", "g", "angle", " ", "ga.json", [])]


@pytest.fixture(scope="session")
def compilers_dict():
    Compiler.available_syscode = 1
    return {"a": Compiler("a", "a", "independent", " ", " ", []),
            "ba": Compiler("ba", "ba", "independent", "/ba/ba/", " ", []),
            "c": Compiler("c", "c", "angle", "angle/c/data", " ", []),
            "d_x": Compiler("d_x", "d", "angle", "angle/c/data", "c.json", []),
            "e": Compiler("e", "e", "independent", "en/", "end.json", ["WHATEVER=\"indep\"", "X=\"y\""]),
            "f": Compiler("f", "f", "angle", "en/", " ", ["WHATEVER=\"ang\"", "X=\"z\""]),
            "g": Compiler("g", "g", "angle", " ", "ga.json", [])}
