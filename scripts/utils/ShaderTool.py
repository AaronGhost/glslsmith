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

from xml.dom import minidom


class ShaderTool:
    def __init__(self, name, path, file_extension):
        self.name = name
        self.path = path
        self.file_extension = file_extension

    def __str__(self):  # pragma: no cover
        return self.name

    @staticmethod
    def load_shader_tools(filename):
        xmldoc = minidom.parse(filename)
        shadertools_xml = xmldoc.getElementsByTagName("shadertool")
        shadertools = []
        for shadertool in shadertools_xml:
            name = shadertool.getElementsByTagName("name")[0].childNodes[0].data
            path = shadertool.getElementsByTagName("path")[0].childNodes[0].data
            file_extension = shadertool.getElementsByTagName("extension")[0].childNodes[0].data
            shadertools.append(ShaderTool(name, path, file_extension))
        return shadertools
