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
from scripts.utils.Reducer import Reducer


def test_eq():
    first_reducer = Reducer("reducer", "reducer --input x", "interesting.sh", "shader.glsl", "shader2.glsl", [])
    second_reducer = Reducer("reducer", "reducer --input x", "interesting.sh", "shader.glsl", "shader2.glsl", [])
    assert (first_reducer == second_reducer) is True
    second_reducer.name = "new"
    assert (first_reducer == second_reducer) is False
    assert (first_reducer == "reducer") is False


def test_load_reducers_settings():
    reducers = Reducer.load_reducers_settings("testdata/xml_files/reducers.xml")
    # First reducer (picire)
    assert reducers[0].name == "picire"
    assert reducers[0].command == "picire --input test.comp --test interesting.sh"
    assert reducers[0].interesting_test == "interesting.sh"
    assert reducers[0].input_file == "test.comp"
    assert reducers[0].output_files == "test.comp"
    assert reducers[0].extra_files_to_build == []

    # Second reducer (glsl-reduce)
    assert reducers[1].name == "glsl-reduce"
    assert reducers[1].command == "com.graphicsfuzz.reducer.tool.GlslReduce"
    assert reducers[1].interesting_test == "interesting.sh"
    assert reducers[1].input_file == "test.comp"
    assert reducers[1].output_files == "test_reduced_final.comp"
    assert reducers[1].extra_files_to_build == ["test.json"]
