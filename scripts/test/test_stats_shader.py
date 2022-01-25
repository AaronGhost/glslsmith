import os
import shutil

import pytest

from scripts.stats_shader import find_shader_main_body, report_wrapper_call, print_file_report, stats_shader
from scripts.test.testhelper import load_file


class TestStatsShader:
    example1_text = "Lines: 26\nBytes: 641\nWrapper calls: 2\n"
    example2_text = "Lines: 25\nBytes: 861\nWrapper calls: 7\n"

    @pytest.mark.parametrize("origin_file, expected",
                             [("example1.glsl", "result1.txt"),
                              ("example2.glsl", "result2.txt")])
    def test_find_shader_main_body(self, origin_file, expected):
        assert find_shader_main_body(load_file("stats_shader/" + origin_file)) == load_file("stats_shader/" + expected)

    def test_report_wrapper_call(self):
        assert report_wrapper_call("void main()\n{\n}\n") == 0
        assert report_wrapper_call(load_file("stats_shader/result1.txt")) == 2
        assert report_wrapper_call(load_file("stats_shader/result2.txt")) == 7

    @pytest.mark.parametrize("origin_file, expected",
                             [("example1.glsl", example1_text),
                              ("example2.glsl", example2_text)])
    def test_print_file_report(self, capsys, origin_file, expected):
        print_file_report("testdata/stats_shader/" + origin_file)
        outputs = capsys.readouterr()
        assert outputs.out == expected

    @pytest.mark.parametrize("origin_file, output_text",
                             [("shader_1.shadertrap", example1_text), ("shader_2.shadertrap", example2_text)])
    def test_stats_shader(self, capsys, tmpdir, origin_file, output_text, conf):
        location = tmpdir.join(origin_file)
        shutil.copy("testdata/stats_shader/" + origin_file, location)
        assert os.path.isfile(location)
        stats_shader(conf["exec_dirs"].graphicsfuzz, conf["shadertools"][0], location,
                     str(tmpdir.join("tmp.shadertrap")))
        outputs = capsys.readouterr()
        assert outputs.out == output_text
        assert len(os.listdir(tmpdir)) == 1
