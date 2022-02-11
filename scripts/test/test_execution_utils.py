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
# limitations under the License
import argparse
import sys

import pytest

from scripts.utils import execution_utils
from scripts.utils.Reducer import Reducer
from scripts.utils.ShaderTool import ShaderTool
from scripts.utils.execution_utils import select_reducer, select_shader_tool, env_setup


def test_build_compiler_dict(compilers_list, compilers_dict):
    assert execution_utils.build_compiler_dict(compilers_list, []) == compilers_dict
    assert execution_utils.build_compiler_dict(compilers_list, ["a", "d_x", "f"]) == {"a": compilers_dict["a"],
                                                                                      "d_x": compilers_dict["d_x"],
                                                                                      "f": compilers_dict["f"]}


def test_select_reducer():
    reducers = Reducer.load_reducers_settings("testdata/xml_files/reducers.xml")
    # Exit if no reducer is available
    with pytest.raises(SystemExit) as e:
        select_reducer([], "whatever")
    assert e.type == SystemExit
    assert isinstance(e.value.code, str)
    # Exit if a reducer is explicitly asked, and it is not available
    with pytest.raises(SystemExit) as e:
        select_reducer(reducers, "whatever")
    assert e.type == SystemExit
    assert isinstance(e.value.code, str)
    # Other cases return the correct compiler
    assert select_reducer(reducers, "glsl-reduce").name == "glsl-reduce"
    assert select_reducer(reducers, "").name == "picire"


def test_select_shader_tool():
    shader_tools = ShaderTool.load_shader_tools("testdata/xml_files/shadertools.xml")
    # Exit if no reducer is available
    with pytest.raises(SystemExit) as e:
        select_shader_tool(shader_tools, "whatever")
    assert e.type == SystemExit
    assert isinstance(e.value.code, str)
    assert select_shader_tool(shader_tools, "amber").name == "amber"
    assert select_shader_tool(shader_tools, "").name == "shadertrap"


def test_env_setup():
    parser = argparse.ArgumentParser()
    sys.argv = ["execution-utils", "--config", "testdata/xml_files/fake_config.xml"]
    ns, exec_dirs, compilers_dict, reducer, shade_tool = env_setup(parser)
    assert hasattr(ns, "host")
    assert exec_dirs.graphicsfuzz == "/graphicsfuzz/"
    assert compilers_dict["a"].renderer == "ana"
    assert compilers_dict["bas"].ldpath == "/ba_x/ba_x/"
    assert reducer.name == "picire"
    assert shade_tool.name == "shadertrap"

