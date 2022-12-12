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
import os.path
import shutil

import pytest

from scripts.automate_reducer import get_files_to_reduce, run_reduction
from scripts.test.conftest import prepare_tmp_env


@pytest.mark.parametrize("use_kept, test_shader, keptshaders, expected, directory", [
    (False, "test.shadertrap", [], ["test.shadertrap"], "execdir"),
    (True, "test.shadertrap", ["kept.shadertrap"], ["kept.shadertrap"], "keptshaderdir"),
    (True, "test.shadertrap", ["kept.shadertrap", "kept2.shadertrap", "kept2_re.shadertrap"],
     ["kept.shadertrap"], "keptshaderdir"),
    (True, "test.shadertrap", ["kept.shadertrap" "kept2_re.shadertrap"], ["kept.shadertrap"],
     "keptshaderdir"),
    (True, "test.shadertrap", ["kept.shadertrap", "kept2.shadertrap"],
     ["kept.shadertrap", "kept2.shadertrap"], "keptshaderdir"),
])
def test_get_files_to_reduce(tmpdir, conf, use_kept, test_shader, keptshaders, expected, directory):
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)
    for shader in keptshaders:
        with open(execdirs.keptshaderdir + shader, "w") as f:
            f.write("")
    with open(execdirs.execdir + test_shader, "w") as f:
        f.write("")

    test_shader = execdirs.execdir + test_shader

    files = get_files_to_reduce(use_kept, test_shader, execdirs.keptshaderdir)
    assert all([os.path.basename(f) in expected for f in files])
    if directory == "execdir":
        assert all([execdirs.execdir in f for f in files])
    elif directory == "keptshaderdir":
        assert all([execdirs.keptshaderdir in f for f in files])


@pytest.mark.parametrize("error_code, expect_reduction, success, message",
                         [(0, False, False, "No error"),
                          (3001, True, True, "Reduction finished"),
                          (2001, False, False, "Skipping"),
                          (3001, True, False, "Reduction failed"),
                          ])
def test_run_reduction(conf, tmpdir, mocker, capsys, error_code, expect_reduction, success, message):
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)

    def fake_reduction():
        if success:
            with open(execdirs.execdir + conf["reducers"][0].output_files, "w") as f:
                f.write("")

    if conf["shadertools"][0].name == "shadertrap":
        test_input = execdirs.execdir + "test.shadertrap"
        test_output = execdirs.execdir + "test_reduced.shadertrap"
        copied_file = "testdata/shadertrap_shaders/shader_1.shadertrap"
    elif conf["shadertools"][0].name == "amber":
        test_input = execdirs.execdir + "test.amber"
        test_output = execdirs.execdir + "test_reduced.amber"
        copied_file = "testdata/amber_shaders/shader_1.amber"
    else:
        pytest.mark.skip("Unknown shader tool")
        return

    # Mock the creation of the reduction script for miscompilation
    mocker.patch("automate_reducer.create_shell_code.build_shell_test", return_value=str(error_code))
    # Mock the execution of the reduction script
    mocker.patch("automate_reducer.subprocess.run", side_effect=fake_reduction())
    # Copy the test shader to the execdir
    shutil.copy(copied_file, test_input)
    # Generate a fake interesting script
    with open(execdirs.execdir + "interesting.sh", "w") as f:
        f.write("")

    run_reduction(conf["reducers"][0], conf["compilers"], execdirs, test_input, test_output,
                  conf["shadertools"][0], -1, False, "reduction.log")

    assert os.path.isfile(test_input)
    # Normal reduction process
    if expect_reduction:
        if success:
            assert os.path.exists(test_output)
            assert "Reduction finished in" in capsys.readouterr().out
        else:
            assert "Reduction failed" in capsys.readouterr().out
    else:
        assert message in capsys.readouterr().out


def test_batch_reduction():
    pass


def test_main():
    pass
