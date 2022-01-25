import pytest

from scripts.common import load_dir_settings, load_compilers_settings, load_reducers_settings, load_shader_tools


def pytest_addoption(parser):
    parser.addoption("--config_file", action="store")


@pytest.fixture(scope="session")
def conf(request):
    conf_path = request.config.getoption("--config_file")
    conf_dict = {"exec_dirs": load_dir_settings(conf_path),
                 "compilers": load_compilers_settings(conf_path),
                 "reducers": load_reducers_settings(conf_path),
                 "shadertools": load_shader_tools(conf_path)}
    return conf_dict
