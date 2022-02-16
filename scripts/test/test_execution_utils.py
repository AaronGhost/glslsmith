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
from scripts.utils.execution_utils import select_reducer, select_shader_tool, env_setup, find_amber_buffers, \
    prepare_amber_command, prepare_shadertrap_command, collect_process_return


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


# TODO fix this with real Amber examples
@pytest.mark.parametrize("filename, result", [("shader_1.amber", [("buffer_ids", "0", "0"), ("buffer_0", "0", "1"),
                                                                  ("buffer_1", "0", "2"), ("buffer_2", "0", "3")]),
                                              ("shader_2.amber", [("buffer_0", "0", "0"), ("buffer_1", "0", "1"),
                                                                  ("buffer_2", "0", "2"), ("buffer_3", "0", "3"),
                                                                  ("buffer_4", "0", "4")])])
def test_find_amber_buffers(filename, result):
    assert find_amber_buffers("testdata/amber_shaders/" + filename) == result


@pytest.mark.parametrize("shader_name, add_id, result", [
    ("shader_1.amber", True, "./amber -d -b buffer_output.txt -B 0 testdata/amber_shaders/shader_1.amber"),
    ("shader_2.amber", False,
     "./amber -d -b buffer_output.txt -B 0 -B 1 -B 2 -B 3 -B 4 testdata/amber_shaders/shader_2.amber")])
def test_prepare_amber_command(shader_name, add_id, result):
    assert prepare_amber_command("./amber", "buffer_output.txt", "testdata/amber_shaders/" + shader_name,
                                 add_id) == result


def test_prepare_shadertrap_command():
    assert prepare_shadertrap_command("shadertrap/shadertrap", "banana",
                                      "test.shadertrap") == "shadertrap/shadertrap " \
                                                            "--require-vendor-renderer-substring banana " \
                                                            "test.shadertrap"


def test_collect_process_return():
    class Outputs(object):
        def __init__(self, stdout, stderr):
            self.stdout = stdout
            self.stderr = stderr

    process_return_1 = Outputs("Every path leads to SUCCESS!", "")
    assert collect_process_return(process_return_1, "SUCCESS!") == (True, "Every path leads to SUCCESS!")
    assert collect_process_return(process_return_1, "passed") == (False, "Every path leads to SUCCESS!")
    process_return_2 = Outputs("whatever", "1 passed")
    assert collect_process_return(process_return_2, "passed") == (True, "whatever1 passed")
