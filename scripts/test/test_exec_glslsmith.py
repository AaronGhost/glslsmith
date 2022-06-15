import os.path
import shutil
from unittest.mock import MagicMock

import pytest
from scripts.exec_glslsmith import write_output_to_file, glsl_output, validate_compiler, syntax_check, save_test_case, \
    exec_glslsmith
from scripts.test.testhelper import compare_files, restrict_compilers
from scripts.utils.Compiler import Compiler
from scripts.utils.Reducer import Reducer
from scripts.utils.ShaderTool import ShaderTool
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
    compare_files("testdata/exec_glslsmith/test_0_re.comp", tmpdir.join("shaders").join("test_0_re.comp"))

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
    compare_files("testdata/exec_glslsmith/" + result, str(tmpdir) + "/" + location)


def test_save_test_case(tmpdir, compilers_dict):
    tmpdir.mkdir("dumpshaders")
    tmpdir.mkdir("keptshaders")
    tmpdir.mkdir("keptbuffers")
    tmpdir.mkdir("dumpbuffers")
    # Copy shader over
    shutil.copy("testdata/exec_glslsmith/test_0.shadertrap", str(tmpdir) + "/dumpshaders/test.shadertrap")

    # Copy test buffers over
    name_list = ["a", "ba", "c", "d_x"]
    for name in name_list:
        shutil.copy("testdata/exec_glslsmith/buffer_" + name + "_1.txt",
                    str(tmpdir) + "/dumpbuffers/buffer_" + name + "_1.txt")
    compilers_dict = restrict_compilers(compilers_dict, name_list)

    save_test_case(str(tmpdir) + "/keptshaders/", str(tmpdir) + "/dumpbuffers/", str(tmpdir) + "/keptbuffers/",
                   compilers_dict, str(tmpdir) + "/dumpshaders/test.shadertrap", "1",
                   ShaderTool("shadertrap", "shadertrap/unused", ".shadertrap"))
    assert os.path.isfile(tmpdir.join("keptshaders/1.shadertrap"))
    for name in name_list:
        assert os.path.isfile(tmpdir.join("keptbuffers/" + name + "_1.txt"))

    assert len(os.listdir(tmpdir.join("dumpshaders"))) == 0
    assert len(os.listdir(tmpdir.join("dumpbuffers"))) == 0


def prepare_tmp_env(execdirs, tmpdir):
    tmpdir.mkdir("execdir")
    execdirs.execdir = str(tmpdir.join("execdir")) + "/"
    tmpdir.mkdir("shaderoutput")
    execdirs.shaderoutput = str(tmpdir.join("shaderoutput")) + "/"
    tmpdir.mkdir("keptshaders")
    execdirs.keptshaderdir = str(tmpdir.join("keptshaders")) + "/"
    tmpdir.mkdir("bufferoutput")
    execdirs.dumpbufferdir = str(tmpdir.join("bufferoutput")) + "/"
    tmpdir.mkdir("keptbuffers")
    execdirs.keptbufferdir = str(tmpdir.join("keptbuffers")) + "/"
    return execdirs


def test_exec_glslsmith_options(tmpdir, conf, capsys):
    # Temp environment
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)

    # Test on glsl-only + constrained seed
    with pytest.raises(SystemExit) as e:
        exec_glslsmith(execdirs, ["unused"], conf["reducers"][0], conf["shadertools"][0], 0, 2, glsl_only=True)
        assert e.type == SystemExit
        assert e.value.code == 0
        assert len(os.listdir(tmpdir.join("execdir"))) == 0
        assert os.path.isfile(tmpdir.join("shaderoutput/test_0_re.comp"))
        assert os.path.isfile(tmpdir.join("shaderoutput/test_1_re.comp"))
        capsys.readouterr()

    # Test on syntax-only
    with pytest.raises(SystemExit) as e:
        exec_glslsmith(execdirs, build_compiler_dict(conf["compilers"], ["swiftshader"]), conf["reducers"][0],
                       conf["shadertools"][0], 0, 2, syntax_only=True)
        assert e.type == SystemExit
        assert e.value.code == 0
        assert len(os.listdir(tmpdir.join("execdir"))) == 0
        syntax_outputs = capsys.readouterr().out
        assert "Shader 0 validated" in syntax_outputs
        assert "Shader 1 validated" in syntax_outputs

    # Test on normal case without difference
    exec_glslsmith(execdirs, build_compiler_dict(conf["compilers"]), conf["reducers"][0],
                   conf["shadertools"][0], 0, 2)
    assert len(os.listdir(tmpdir.join("bufferoutput"))) == 2*len(conf["compilers"])
    assert len(os.listdir(tmpdir.join("execdir"))) == 0


def test_exec_glslsmith_generation_error(mocker, conf):
    mocker.patch('scripts.exec_glslsmith.call_glslsmith_generator', return_value=(False, "Generation error"))
    with pytest.raises(SystemExit) as e:
        exec_glslsmith(conf["exec_dirs"], build_compiler_dict(conf["compilers"]), conf["reducers"][0],
                       conf["shadertools"][0], -1, 50)
        assert e.type == SystemExit
        assert e.value.code == 1


def test_exec_glslsmith_force_diff_files(mocker, conf, tmpdir):
    execdirs = prepare_tmp_env(conf["exec_dirs"], tmpdir)

    mocker.patch('scripts.exec_glslsmith.comparison_helper', return_value=[["llvmpipe"], ["swiftshader"]])
    mocker.patch('scripts.exec_glslsmith.attribute_compiler_results', return_value="# 3015\n")

    exec_glslsmith(execdirs, build_compiler_dict(conf["compilers"]), conf["reducers"][0],
                   conf["shadertools"][0], 0, 1)
    assert os.path.isfile(tmpdir.join("keptshaders/0" + conf["shadertools"][0].file_extension))
    assert len(os.listdir(tmpdir.join("keptbuffers"))) == len(conf["compilers"])
