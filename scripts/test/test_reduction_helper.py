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
import os
import shutil
import sys

import pytest

from scripts.reduction_helper import identify_crashes, execute_reduction, main
from scripts.test.conftest import prepare_tmp_env
from scripts.utils.file_utils import clean_files


@pytest.mark.parametrize("results, expected",
                         [(["no_crash", "no_crash", "no_crash", "no_crash"], "0"),
                          (["no_crash", "no_crash", "no_crash", "timeout"], "2016"),
                          (["no_crash", "no_crash", "no_crash", "crash"], "1016"),
                          (["no_crash", "no_crash", "timeout", "crash"], "1016"),
                          (["no_crash", "no_crash", "timeout", "timeout"], "2024"),
                          (["no_crash", "no_crash", "crash", "crash"], "1024"),
                          (["crash", "crash", "crash", "crash"], "1000")])
def test_identify_crashes(results, compilers_list, expected):
    assert identify_crashes(results, compilers_list[0:4]) == expected


@pytest.mark.parametrize("results, buffers_content, expected, ref, add_id, postprocess",
                         [(["no_crash", "no_crash", "no_crash", "no_crash"], ["0 0", "0 0", "0 0", "0 0"], 0, "",
                           False, False),
                          (["no_crash", "no_crash", "no_crash", "timeout"], ["0 0", "0 0", "0 0", "0 0"], 2016, "",
                           False, False),
                          (["no_crash", "no_crash", "crash", "crash"], ["0 0", "0 0", "0 0", "0 0"], 1024, "",
                           True, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 1", "0 0", "0 0", "0 0"], 3001, "",
                           False, True),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 0", "0 1", "0 0", "0 0"], 3002, "",
                           False, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 0", "0 0", "0 1", "0 0"], 3003, "",
                           False, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 0", "0 0", "0 0", "0 1"], 3004, "",
                           True, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 1", "0 1", "0 0", "0 0"], 3099, "",
                           False, True),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 1", "0 0", "1 1", "0 0"],
                           "4000 [['a'], ['ba', 'd_x'], ['c']]", "", False, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 1", "0 0", "0 0", "0 1"], 9999, "",
                           False, False),
                          (["no_crash", "no_crash", "no_crash", "no_crash"], ["0 1", "0 0", "0 0", "0 0"], 5001,
                           "0 0", False, False)])
def test_execute_reduction(tmpdir, conf, mocker, compilers_dict, results, buffers_content, expected, ref, add_id,
                           postprocess):
    # Use only the first 4 compilers
    compiler_names = ["a", "ba", "c", "d_x"]
    compilers = {k: compilers_dict[k] for k in compiler_names}

    # Prepare the environment
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)

    # Side-effecting function to mock the compilation process
    def generate_buffers(*args, **kwargs):
        for i, compiler in enumerate(compiler_names):
            with open(execdirs.execdir + compiler + ".txt", "w") as fid:
                fid.write(buffers_content[i])
        # Add the reference buffer if needed
        if ref != "":
            with open(execdirs.execdir + "ref.txt", "w") as fid:
                fid.write(str(ref))
        return results

    # Mock the function that executes the compilation
    mocker.patch("scripts.reduction_helper.execute_compilation", side_effect=generate_buffers)

    # Set the path for the reference buffer if used
    if ref != "":
        ref_file = execdirs.execdir + "ref.txt"
    else:
        ref_file = ""

    # Execute the reduction and check that the result is identical to the expected one
    with pytest.raises(SystemExit) as e:
        execute_reduction(compilers, execdirs, conf["shadertools"][0], "test.shadertrap", ref_file, False, add_id,
                          postprocess)
    if expected == 0:
        assert e.type == SystemExit
        assert e.value.code == 0
    else:
        assert e.type == SystemExit
        assert e.value.code == str(expected)


def test_main(conf):
    test_file = ""
    copied_file = ""
    if conf["shadertools"][0] == "shadertrap":
        test_file = "test_identical.shadertrap"
        copied_file = "testdata/shadertrap_shaders/shader_1.shadertrap"
    elif conf["shadertools"][0] == "amber":
        test_file = "test_identical.amber"
        copied_file = "testdata/amber_shaders/shader_1.amber"
    else:
        pytest.mark.skip("Unknown shader tool")
    script_location = os.getcwd()
    try:
        sys.argv = ["reduction_helper.py", "--shader-name", test_file, "--config-file", conf["conf_path"]]
        # Copy a shadertrap from the testdata to the execdir
        shutil.copy(copied_file, conf["exec_dirs"].execdir + test_file)
        # Execute the function expecting a SystemExit
        with pytest.raises(SystemExit) as e:
            main()
        assert e.type == SystemExit
        assert e.value.code == 0

    # Restore the original working directory when the test is done
    finally:
        if os.path.isfile(conf["exec_dirs"].execdir + test_file):
            clean_files(conf["exec_dirs"].execdir, [test_file])
        os.chdir(script_location)
