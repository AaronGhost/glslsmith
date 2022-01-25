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

import pytest

from scripts.common import load_dir_settings, load_compilers_settings, load_reducers_settings, load_shader_tools


def pytest_addoption(parser):
    parser.addoption("--config_file", action="store")


@pytest.fixture(scope="session")
def conf(request):
    conf_path = request.config.getoption("--config_file")
    conf_dict = {"exec_dirs": load_dir_settings(conf_path),
                 "compilers": load_compilers_settings(conf_path),
                 "reducers": load_reducers_settings(conf_path),
                 "shadertools": load_shader_tools(conf_path)}
    return conf_dict
