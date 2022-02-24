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


class Compiler:
    available_syscode = 1

    def __init__(self, name, renderer, compiler_type, ldpath, vkfilename, othervens):
        self.name = name
        self.renderer = renderer
        self.type = compiler_type
        self.ldpath = ldpath
        self.vkfilename = vkfilename
        self.otherenvs = othervens
        self.compilercode = Compiler.available_syscode
        Compiler.available_syscode += 1

    def __str__(self):  # pragma: no cover
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def build_exec_env(self):
        cmd_env = []
        if self.ldpath != " " or self.otherenvs != [] or self.type == "angle" or self.vkfilename != " ":
            cmd_env.append("env")
            if self.ldpath != " ":
                cmd_env.append("LD_LIBRARY_PATH=" + self.ldpath + ":$LD_LIBRARY_PATH")
            if self.type == "angle":
                cmd_env.append("ANGLE_DEFAULT_PLATFORM=vulkan")
            if self.vkfilename != " ":
                cmd_env.append("VK_ICD_FILENAMES=" + self.vkfilename)
            for otherenv in self.otherenvs:
                cmd_env.append(otherenv)
        return cmd_env

    @staticmethod
    def load_compilers_settings(filename):
        xmldoc = minidom.parse(filename)
        compilers = []
        compilersxml = xmldoc.getElementsByTagName("compiler")
        for compiler in compilersxml:
            name = compiler.getElementsByTagName("name")[0].childNodes[0].data
            renderer = compiler.getElementsByTagName("renderer")[0].childNodes[0].data
            compiler_type = compiler.getElementsByTagName("type")[0].childNodes[0].data
            ldpath = compiler.getElementsByTagName("LD_LIBRARY_PATH")[0].childNodes[0].data
            vkfilename = compiler.getElementsByTagName("VK_ICD_FILENAMES")[0].childNodes[0].data
            otherenvs = []
            otherenvsxml = compiler.getElementsByTagName("otherenvs")[0]
            if len(otherenvsxml.getElementsByTagName("length")) != 0:
                nb_envs = int(otherenvsxml.getElementsByTagName("length")[0].childNodes[0].data)
                for i in range(nb_envs):
                    otherenvs.append(otherenvsxml.getElementsByTagName("env_" + str(i))[0].childNodes[0].data)
            compilers.append(Compiler(name, renderer, compiler_type, ldpath, vkfilename, otherenvs))
        return compilers
