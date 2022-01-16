import pytest

from scripts.stats_shader import find_shader_main_body, report_wrapper_call
from testhelper import load_file


class TestStatsShader:
    @pytest.mark.parametrize("origin_file, expected",
                             [("example1.glsl", "result1.txt"),
                              ("example2.glsl", "result2.txt")])
    def test_find_shader_main_body(self, origin_file, expected):
        assert find_shader_main_body(load_file("stats_shader/" + origin_file)) == load_file("stats_shader/" + expected)

    def test_report_wrapper_call(self):
        assert report_wrapper_call("void main()\n{\n}\n") == 0
        assert report_wrapper_call(load_file("stats_shader/result1.txt")) == 2
        assert report_wrapper_call(load_file("stats_shader/result2.txt")) == 7
