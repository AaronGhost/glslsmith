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
import os
import shutil
import sys

import pytest

from scripts.splitter_merger import get_glslcode_from_shadertrap, get_glslcode, split, merge, get_glslcode_from_amber, \
    main
from scripts.test.testhelper import load_file
from scripts.utils.ShaderTool import ShaderTool


def test_get_glslcode_from_shadertrap():
    assert get_glslcode_from_shadertrap(load_file("splitter_merger/shader_1.shadertrap")) == load_file(
        "splitter_merger/shader_1.glsl")


def test_get_glslscode_from_amber():
    assert get_glslcode_from_amber(load_file("splitter_merger/shader_1.amber")) == load_file(
        "splitter_merger/shader_1.glsl")


@pytest.mark.parametrize("tool", [(ShaderTool("shadertrap", "/shadertrap/bin/shadertrap", ".shadertrap")),
                                  (ShaderTool("amber", "/amber/bin/amber", ".amber"))])
def test_get_glslcode(tool):
    assert get_glslcode(tool, load_file("splitter_merger/shader_1" + tool.file_extension)) == load_file(
        "splitter_merger/shader_1.glsl")


def test_get_glslcode_non_recognized():
    with pytest.raises(SystemExit) as e:
        get_glslcode(ShaderTool("tool", "/tool/bin/tool", ".tool"), load_file("splitter_merger/shader_1.shadertrap"))
    assert e.value.code == 1


@pytest.mark.parametrize("tool", [(ShaderTool("shadertrap", "/shadertrap/bin/shadertrap", ".shadertrap")),
                                  (ShaderTool("amber", "/amber/bin/amber", ".amber"))])
def test_split(tmpdir, tool):
    split(tool, "testdata/splitter_merger/shader_1" + tool.file_extension, tmpdir.join("shader_1.glsl"))
    with open(tmpdir.join("shader_1.glsl"), "r") as f:
        assert load_file("splitter_merger/shader_1.glsl") == f.read()


@pytest.mark.parametrize("tool", [(ShaderTool("shadertrap", "/shadertrap/bin/shadertrap", ".shadertrap")),
                                  (ShaderTool("amber", "/amber/bin/amber", ".amber"))])
def test_merge(tmpdir, tool):
    shutil.copy("testdata/splitter_merger/empty" + tool.file_extension, tmpdir.join("empty" + tool.file_extension))
    with open(tmpdir.join("empty" + tool.file_extension), "r") as f:
        print(f.read())
    merge(tool, tmpdir.join("empty" + tool.file_extension), "testdata/splitter_merger/shader_1.glsl")
    with open(tmpdir.join("empty" + tool.file_extension), "r") as f:
        assert f.read() == load_file("splitter_merger/shader_1" + tool.file_extension)


def test_main(tmpdir, conf):
    scripts_path = os.getcwd()
    with pytest.raises(SystemExit) as e:
        sys.argv = ["splitter_merger.py", "--config-file", conf["conf_path"]]
        main()
    assert e.type == SystemExit
    assert e.value.code == 1
    os.chdir(scripts_path)
    with pytest.raises(SystemExit) as e:
        sys.argv = ["splitter_merger.py", "--config-file", conf["conf_path"], "--split", "x", "y", "--merge", "y", "z"]
        main()
    assert e.type == SystemExit
    assert e.value.code == 1
    os.chdir(scripts_path)
    file_extension = conf["shadertools"][0].file_extension
    shutil.copy("testdata/splitter_merger/shader_1" + file_extension, tmpdir.join("shader_orig" + file_extension))
    sys.argv = ["splitter_merger.py", "--config-file", conf["conf_path"], "--split",
                str(tmpdir.join("shader_orig" + file_extension)),
                str(tmpdir.join("shader_1.glsl"))]
    main()
    os.chdir(scripts_path)
    with open(tmpdir.join("shader_1.glsl"), "r") as f:
        assert load_file("splitter_merger/shader_1.glsl") == f.read()
    shutil.copy("testdata/splitter_merger/empty" + file_extension, tmpdir.join("empty" + file_extension))
    sys.argv = ["splitter_merger.py", "--config-file", conf["conf_path"], "--merge",
                str(tmpdir.join("empty" + file_extension)),
                str(tmpdir.join("shader_1.glsl"))]
    main()
    os.chdir(scripts_path)
    with open(tmpdir.join("empty" + file_extension), "r") as f:
        assert f.read() == load_file("splitter_merger/shader_1" + file_extension)
