import filecmp
import os.path
import shutil

import pytest
from scripts.exec_glslsmith import write_output_to_file, glsl_output, validate_compiler, syntax_check
from scripts.utils.Compiler import Compiler
from scripts.utils.execution_utils import build_compiler_dict


def test_validate_compiler(tmpdir, conf):
    # Test with a valid compiler
    shadertool = conf["shadertools"][0]
    if shadertool.name == "shadertrap":
        assert "no_crash" == validate_compiler(str(tmpdir), conf["compilers"][0], shadertool)

    # Bogus compiler (test exit on error)
    with pytest.raises(SystemExit) as e:
        validate_compiler(str(tmpdir), Compiler("bogus", "bogus", "independent", "", "", []), shadertool)
        assert e.type == SystemExit
        assert e.value.code == 1


def test_syntax_check(tmpdir, capsys, conf):
    # Valid file
    shadertool = conf["shadertools"][0]
    compilers_dict = build_compiler_dict(conf["compilers"])
    tmpdir.mkdir("shaders")
    shutil.copy("testdata/exec_glslsmith/test_0" + shadertool.file_extension,
                str(tmpdir) + "/shaders/test_0" + shadertool.file_extension)
    first_compiler = list(compilers_dict.values())[0]
    syntax_check({first_compiler.name: first_compiler}, str(tmpdir), conf["exec_dirs"].graphicsfuzz,
                 str(tmpdir) + "/shaders/",
                 shadertool, "0")
    outputs = capsys.readouterr().out
    assert outputs == "Shader 0 validated\n"
    # Bogus file
    syntax_check({first_compiler.name: first_compiler}, str(tmpdir), conf["exec_dirs"].graphicsfuzz,
                 str(tmpdir) + "/shaders/",
                 shadertool, "1")
    outputs = capsys.readouterr().out
    assert "Error on shader 1" in outputs


def test_glsl_output(tmpdir, conf):
    # Valid code
    file_extension = conf["shadertools"][0].file_extension
    location = "test_0" + file_extension
    tmpdir.mkdir("shaders")
    shutil.copy("testdata/exec_glslsmith/" + location, str(tmpdir) + "/shaders/" + location)
    glsl_output(tmpdir, conf["exec_dirs"].graphicsfuzz, str(tmpdir.join("shaders")) + "/", conf["shadertools"][0],
                str(0))
    assert os.path.isfile(tmpdir.join("shaders/test_0_re.comp"))
    assert filecmp.cmp("testdata/exec_glslsmith/test_0_re.comp", tmpdir.join("shaders").join("test_0_re.comp"),
                       shallow=False)

    # No-code (test exit on error)
    with pytest.raises(SystemExit) as e:
        glsl_output(tmpdir, conf["exec_dirs"].graphicsfuzz, str(tmpdir.join("shaders")) + "/", conf["shadertools"][0],
                    str(1))
        assert e.type == SystemExit
        assert e.value.code == 1


@pytest.mark.parametrize("text, location, result", [
    ("# cp1", "file1.txt", "file1_result.txt"), ("# Whatever\n", "file2.shadertrap", "file2_result.shadertrap")])
def test_write_output_to_file(tmpdir, text, location, result):
    shutil.copy("testdata/exec_glslsmith/" + location, str(tmpdir) + "/" + location)
    write_output_to_file(text, str(tmpdir) + "/" + location)
    assert filecmp.cmp("testdata/exec_glslsmith/" + result, str(tmpdir) + "/" + location, shallow=False)
