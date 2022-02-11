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
from scripts.utils.ShaderTool import ShaderTool


def test_eq():
    first_shadertool = ShaderTool("shadertool", "shadertool/shadertool", ".shader")
    second_shadertool = ShaderTool("shadertool", "shadertool/shadertool", ".shader")
    assert (first_shadertool == second_shadertool) is True
    second_shadertool.name = "tool"
    assert (first_shadertool == second_shadertool) is False
    assert (first_shadertool == "shadertool") is False


def test_load_shader_tools():
    shader_tools = ShaderTool.load_shader_tools("testdata/xml_files/shadertools.xml")
    # Test first shader tool (Shadertrap)
    assert shader_tools[0].name == "shadertrap"
    assert shader_tools[0].path == "/shadertrap/build/src/shadertrap/shadertrap"
    assert shader_tools[0].file_extension == ".shadertrap"

    # Test second shader tool (amber)
    assert shader_tools[1].name == "amber"
    assert shader_tools[1].path == "/amber/out/Debug/amber"
    assert shader_tools[1].file_extension == ".amber"
