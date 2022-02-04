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
from scripts.utils.DirSettings import DirSettings


def test_load_dir_settings():
    dir_settings = DirSettings.load_dir_settings("testdata/xml_files/dirsettings.xml")
    assert dir_settings.graphicsfuzz == "/graphicsfuzz/python/drivers/"
    assert dir_settings.execdir == "./"
    assert dir_settings.shaderoutput == "./glslsmithoutput/shaders/"
    assert dir_settings.dumpbufferdir == "./glslsmithoutput/buffers/"
    assert dir_settings.keptbufferdir == "./glslsmithoutput/keptbuffers/"
    assert dir_settings.keptshaderdir == "./glslsmithoutput/keptshaders/"

