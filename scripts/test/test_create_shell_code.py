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
import sys

from scripts.test.conftest import prepare_tmp_env
from scripts.create_shell_code import build_shell_test
from scripts.utils.execution_utils import build_compiler_dict


def test_build_shell_test_no_error(tmpdir, mocker, conf):
    def exit_with_0(*args, **kwargs):
        sys.exit(0)

    # Test that the code is correct for a given error code
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)
    # Patch the comparison process to get a return code
    mocker.patch('scripts.create_shell_code.reduction_helper.execute_reduction', side_effect=exit_with_0)
    # Call build_shell_test expecting to not crash
    assert build_shell_test(build_compiler_dict(conf["compilers"]), execdirs, conf["shadertools"][0], "test.shadertrap",
                            "test.comp", -1, "interesting.sh") == "0000"


def test_build_shell_test_error(tmpdir, mocker, conf):
    def exit_with_3016(*args, **kwargs):
        sys.exit("3016")

    # Test that the code is correct for a given error code
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)
    # Patch the comparison process to get a return code
    mocker.patch('scripts.create_shell_code.reduction_helper.execute_reduction', side_effect=exit_with_3016)
    assert build_shell_test(build_compiler_dict(conf["compilers"]), execdirs, conf["shadertools"][0], "test.shadertrap",
                            "test.comp", -1, "interesting.sh") == "3016"
    assert os.path.isfile(os.path.join(execdirs.execdir, "interesting.sh"))
    with open(os.path.join(execdirs.execdir, "interesting.sh"), "r") as f:
        lines = f.readlines()
        assert len(lines) == 26
        assert lines[0] == "#!/usr/bin/env bash\n"
        assert lines[18] == "ERROR_CODE_IN_FILE=$( (python3 ${ROOT}/scripts/reduction_helper.py --config-file ${" \
                            "ROOT}/scripts/config.xml --shader-name ${ROOT}/test.shadertrap --host shadertrap 2>&1 > " \
                            "/dev/null) || true)\n"
    os.remove(os.path.join(execdirs.execdir, "interesting.sh"))
    # Test double-run option
    assert build_shell_test(build_compiler_dict(conf["compilers"]), execdirs, conf["shadertools"][0], "test.shadertrap",
                            "test.comp", -1, "interesting.sh", True) == "3016"
    assert os.path.isfile(os.path.join(execdirs.execdir, "interesting.sh"))
    with open(os.path.join(execdirs.execdir, "interesting.sh"), "r") as f:
        lines = f.readlines()
        assert len(lines) == 26
        assert lines[0] == "#!/usr/bin/env bash\n"
        assert lines[18] == "ERROR_CODE_IN_FILE=$( (python3 ${ROOT}/scripts/reduction_helper.py --config-file ${" \
                            "ROOT}/scripts/config.xml --shader-name ${ROOT}/test.shadertrap --host shadertrap " \
                            "--double-run 2>&1 > /dev/null) || true)\n"

# TODO create a test for the produced shell code
def test_main():
    pass

