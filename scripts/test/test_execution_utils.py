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
import os
import shutil
import sys

import pytest

from scripts.utils import execution_utils
from scripts.utils.Reducer import Reducer
from scripts.utils.ShaderTool import ShaderTool
from scripts.utils.execution_utils import select_reducer, select_shader_tool, env_setup, find_amber_buffers, \
    prepare_amber_command, prepare_shadertrap_command, collect_process_return, single_compile


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
@pytest.mark.parametrize("filename, result", [("shader_1.amber", [("buffer_0", "0", "0")]),
                                              ("shader_2.amber", [("buffer_ids", "0", "0"), ("buffer_0", "0", "1"),
                                                                  ("buffer_1", "0", "2"), ("buffer_2", "0", "3"),
                                                                  ("buffer_3", "0", "4")])])
def test_find_amber_buffers(filename, result):
    assert find_amber_buffers("testdata/amber_shaders/" + filename) == result


@pytest.mark.parametrize("shader_name, add_id, result", [
    ("shader_1.amber", False, "./amber -d -b buffer_output.txt -B 0 testdata/amber_shaders/shader_1.amber"),
    ("shader_2.amber", True, "./amber -d -b buffer_output.txt -B 0 testdata/amber_shaders/shader_2.amber"),
    ("shader_2.amber", False,
     "./amber -d -b buffer_output.txt -B 0 -B 1 -B 2 -B 3 -B 4 testdata/amber_shaders/shader_2.amber")])
def test_prepare_amber_command(shader_name, add_id, result):
    assert prepare_amber_command("./amber", "buffer_output.txt", "testdata/amber_shaders/" + shader_name,
                                 add_id) == result


def test_prepare_shadertrap_command():
    assert prepare_shadertrap_command("shadertrap/shadertrap", "banana caramel",
                                      "test.shadertrap") == "shadertrap/shadertrap test.shadertrap " \
                                                            "--require-vendor-renderer-substring \"banana caramel\""


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


@pytest.fixture()
def return_to_script():
    script_location = os.getcwd()
    yield
    os.chdir(script_location)


def test_single_compile(tmpdir, conf, return_to_script, capsys):
    script_location = os.getcwd()
    tmpdir_counter = 0
    for shader_tool in conf["shadertools"]:
        for compiler in conf["compilers"]:
            for run_type in ["normal", "add_id"]:
                # Test normal
                buffer_path = tmpdir.join("d" + str(tmpdir_counter))
                tmpdir_counter += 1
                buffer_path.mkdir()
                normal_file = str(buffer_path) + "/shader_1" + shader_tool.file_extension
                shutil.copy(
                    script_location + "/testdata/" + shader_tool.name + "_shaders/shader_1" + shader_tool.file_extension,
                    normal_file)
                os.chdir(buffer_path)
                crash, timeout, message = single_compile(compiler, normal_file, shader_tool, 5, run_type, False)
                assert crash is False, "wrong value for " + compiler.name + " with " + shader_tool.name
                assert timeout is False, "wrong value for " + compiler.name + " with " + shader_tool.name
                assert message == "no_crash", "wrong value for " + compiler.name + " with " + shader_tool.name
                if run_type == "add_id":
                    assert os.path.isfile(
                        buffer_path.join("ids.txt")), "wrong value for " + compiler.name + " with " + shader_tool.name
                else:
                    assert os.path.isfile(buffer_path.join(
                        "buffer_result.txt")), "wrong value for " + compiler.name + " with " + shader_tool.name
                    with open("buffer_result.txt", "r") as f:
                        if shader_tool.name == "shadertrap":
                            assert f.readlines() == [
                                "1 1 1 1 1 1"], "wrong value for " + compiler.name + " with " + shader_tool.name
                        else:
                            assert f.readlines() == ['0\n', ' 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00\n',
                                                     ' 01 00 00 00 01 00 00 00\n'], \
                                "wrong value for " + compiler.name + " with " + shader_tool.name

                # Test crash
                crash_path = tmpdir.join("d" + str(tmpdir_counter))
                tmpdir_counter += 1
                crash_path.mkdir()
                crash_file = str(crash_path) + "/crash" + shader_tool.file_extension
                shutil.copy(
                    script_location + "/testdata/" + shader_tool.name + "_shaders/crash" + shader_tool.file_extension,
                    crash_file)
                os.chdir(crash_path)
                crash, timeout, message = single_compile(compiler, crash_file, shader_tool, 3, run_type, True)
                assert crash is True, "wrong value for " + compiler.name + " with " + shader_tool.name
                assert timeout is False, "wrong value for " + compiler.name + " with " + shader_tool.name
                assert message != "no_crash", "wrong value for " + compiler.name + " with " + shader_tool.name
                if run_type == "add_id":
                    assert os.path.isfile(
                        crash_path.join("ids.txt")), "wrong value for " + compiler.name + " with " + shader_tool.name

                # Test  timeout (Mesa compilers do not seem to timeout)
                if compiler.name != "llvmpipe" and compiler.name != "vulkan-intel" and compiler.name != "lavapipe":
                    timeout_path = tmpdir.join("d" + str(tmpdir_counter))
                    tmpdir_counter += 1
                    timeout_path.mkdir()
                    timeout_file = str(timeout_path) + "/timeout" + shader_tool.file_extension
                    shutil.copy(
                        script_location + "/testdata/" + shader_tool.name + "_shaders/timeout"
                        + shader_tool.file_extension,
                        timeout_file)
                    os.chdir(timeout_path)
                    crash, timeout, message = single_compile(compiler, timeout_file, shader_tool, 3, run_type, True)
                    assert crash is False, "wrong value for " + compiler.name + " with " + shader_tool.name
                    assert timeout is True, "wrong value for " + compiler.name + " with " + shader_tool.name
                    assert message == "timeout", "wrong value for " + compiler.name + " with " + shader_tool.name
                    if run_type == "add_id":
                        assert os.path.isfile(timeout_path.join(
                            "ids.txt")), "wrong value for " + compiler.name + " with " + shader_tool.name
        capsys.readouterr()
