import pytest

from scripts.utils.Compiler import Compiler
from scripts.utils.analysis_utils import attribute_compiler_results, comparison_helper


@pytest.mark.parametrize("seed, group",
                         [(0, [["a"], ["a_x", "b", "c", "d"]]),
                          (1, [["a"], ["a_x", "b", "c", "d"]]),
                          (2, [["a", "a_x", "c"], ["b", "d"]]),
                          (3, [["a", "a_x"], ["b", "c"], ["d"]]),
                          (4, [["a", "a_x", "b", "d"], ["c"]]),
                          (5, [["a", "a_x", "c"], ["b", "d"]]),
                          (15, [["a", "a_x", "b", "c"], ["d"]]),
                          (333, [["a"], ["a_x", "b", "c", "d"]]),
                          (522, [["a"], ["a_x"], ["b"], ["c"], ["d"]]),
                          (2358, [["a", "a_x", "b"], ["c", "d"]]),
                          (9999, [["a", "b", "c", "d"], ["a_x"]])])
def test_comparison_helper(seed, group):
    file_list = list(
        map(lambda text: "testdata/keptbuf/" + text + "_" + str(seed) + ".txt", ["a", "a_x", "b", "c", "d"]))
    assert comparison_helper(file_list) == group


@pytest.mark.parametrize("results, group", [([["a", "b"], ["c"]], "c"),
                                            ([["a"], ["b"]], "a"),
                                            ([["a", "c"], ["b", "d"]], "angle"),
                                            ([["b", "d", "e"], ["a", "f"]], "angle"),
                                            ([["a", "b"], ["c", "d"]], "more than two"),
                                            ([["a"], ["b"], ["c"], ["d"]], "more than two")])
def test_attribute_compiler_results(results, group):
    compiler_dict = {"a": Compiler("a", "a", "angle", "", "", []),
                     "b": Compiler("b", "b", "independent", "", "", []),
                     "c": Compiler("c", "c", "angle", "", "", []),
                     "d": Compiler("d", "d", "independent", "", "", []),
                     "e": Compiler("e", "e", "independent", "", "", []),
                     "f": Compiler("f", "f", "angle", "", "", [])}
    assert attribute_compiler_results(results, compiler_dict) == group
