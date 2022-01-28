import pytest

from scripts.utils.Compiler import Compiler
from scripts.utils.analysis_utils import attribute_compiler_results


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
