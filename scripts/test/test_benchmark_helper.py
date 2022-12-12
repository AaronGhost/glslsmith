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

import sys

from scripts.benchmark_helper import count_calls, main


def test_count_calls(tmpdir):
    for i in range(5):
        count_calls(tmpdir.join("x.log"))
        with open(tmpdir.join("x.log")) as fid:
            lines = fid.readlines()
            assert lines[1] == str(i+1)+"\n"
            assert len(lines) == 3


def test_main(tmpdir):
    sys.argv = ["benchmark_helper.py", "--log", (str(tmpdir.join("y.log")))]
    for i in range(9):
        main()
        with open(tmpdir.join("y.log")) as fid:
            lines = fid.readlines()
            assert lines[1] == str(i+1)+"\n"
            assert len(lines) == 3


