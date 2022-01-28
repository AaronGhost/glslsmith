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


class DirSettings:
    def __init__(self, graphcisfuzz, execdir, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir):
        self.graphicsfuzz = graphcisfuzz
        self.execdir = execdir
        self.shaderoutput = shaderoutput
        self.dumpbufferdir = dumpbufferdir
        self.keptbufferdir = keptbufferdir
        self.keptshaderdir = keptshaderdir

    @staticmethod
    def load_dir_settings(filename):
        xmldoc = minidom.parse(filename)
        dirs = xmldoc.getElementsByTagName("dirsettings")[0]
        graphicsfuzz = dirs.getElementsByTagName("graphicsfuzz")[0].childNodes[0].data
        execdir = dirs.getElementsByTagName("execdir")[0].childNodes[0].data
        shaderoutput = dirs.getElementsByTagName("shaderoutput")[0].childNodes[0].data
        dumpbufferdir = dirs.getElementsByTagName("dumpbufferdir")[0].childNodes[0].data
        keptbufferdir = dirs.getElementsByTagName("keptbufferdir")[0].childNodes[0].data
        keptshaderdir = dirs.getElementsByTagName("keptshaderdir")[0].childNodes[0].data
        return DirSettings(graphicsfuzz, execdir, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir)
