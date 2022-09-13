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
import os
import copy

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
                 "shadertools": ShaderTool.load_shader_tools(conf_path),
                 "conf_path": conf_path}
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


def load_file(filename):
    with open("testdata/" + filename, "r") as file:
        return file.read()


def compare_files(file_name, ref_name):
    file_rows = open(file_name).readlines()
    ref_rows = open(ref_name).readlines()
    row_index = 0
    for row in file_rows:
        assert row == ref_rows[row_index]
        row_index += 1
    assert len(ref_rows) == len(file_rows)


def restrict_compilers(compiler_dict, name_list):
    resulting_compilers = dict()
    for name in name_list:
        if name in compiler_dict:
            resulting_compilers[name] = compiler_dict[name]
    return resulting_compilers


def prepare_tmp_env(execdirs, tmpdir):
    tmpdir.mkdir("execdir")
    execdir = str(tmpdir.join("execdir")) + "/"
    tmpdir.mkdir("shaderoutput")
    shaderoutput = str(tmpdir.join("shaderoutput")) + "/"
    tmpdir.mkdir("keptshaders")
    keptshaderdir = str(tmpdir.join("keptshaders")) + "/"
    tmpdir.mkdir("bufferoutput")
    dumpbufferdir = str(tmpdir.join("bufferoutput")) + "/"
    tmpdir.mkdir("keptbuffers")
    keptbufferdir = str(tmpdir.join("keptbuffers")) + "/"
    settings = DirSettings(execdirs.graphicsfuzz, execdir, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir)
    return settings
