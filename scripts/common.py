import filecmp
from xml.dom import minidom
import os


class DirSettings:
    def __init__(self, graphcisfuzz, shadertrap, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir):
        self.graphicsfuzz = graphcisfuzz
        self.shadertrap = shadertrap
        self.shaderoutput = shaderoutput
        self.dumpbufferdir = dumpbufferdir
        self.keptbufferdir = keptbufferdir
        self.keptshaderdir = keptshaderdir

def load_dir_settings(filename):
    xmldoc = minidom.parse(filename)
    dirs = xmldoc.getElementsByTagName("dirsettings")[0]
    graphicsfuzz = dirs.getElementsByTagName("graphicsfuzz")[0].childNodes[0].data
    shadertrap = dirs.getElementsByTagName("shadertrap")[0].childNodes[0].data
    shaderoutput = dirs.getElementsByTagName("shaderoutput")[0].childNodes[0].data
    dumpbufferdir = dirs.getElementsByTagName("dumpbufferdir")[0].childNodes[0].data
    keptbufferdir = dirs.getElementsByTagName("keptbufferdir")[0].childNodes[0].data
    keptshaderdir = dirs.getElementsByTagName("keptshaderdir")[0].childNodes[0].data
    return DirSettings(graphicsfuzz,shadertrap, shaderoutput, dumpbufferdir, keptbufferdir, keptshaderdir)

class Compiler:
    def __init__(self,name, renderer, type, ldpath, vkfilename, othervens):
        self.name = name
        self.renderer = renderer
        self.type = type
        self.ldpath = ldpath
        self.vkfilename = vkfilename
        self.otherenvs = othervens

    def __str__(self):
        return self.name


def load_compilers_settings(filename):
    xmldoc = minidom.parse(filename)
    compilers = []
    compilersxml = xmldoc.getElementsByTagName("compiler")
    for compiler in compilersxml:
        name = compiler.getElementsByTagName("name")[0].childNodes[0].data
        renderer = compiler.getElementsByTagName("renderer")[0].childNodes[0].data
        type = compiler.getElementsByTagName("type")[0].childNodes[0].data
        ldpath = compiler.getElementsByTagName("LD_LIBRARY_PATH")[0].childNodes[0].data
        vkfilename = compiler.getElementsByTagName("VK_ICD_FILENAMES")[0].childNodes[0].data
        otherenvs = []
        otherenvsxml = compiler.getElementsByTagName("otherenvs")
        if otherenvsxml.length != 1:
            nb_envs  = int(otherenvsxml.getElementByTagName("length")[0].childNodes[0].data)
            for i in range(nb_envs):
                otherenvs.append(otherenvsxml.getElementByTagName("env_"+str(i))[0].childNodes[0].data)
        compilers.append(Compiler(name, renderer, type, ldpath, vkfilename, otherenvs))
    return compilers


def concatenate_files(outputname, files):
    out = b''
    for fileadd in files:
        if 'buffer' in fileadd:
            with open(fileadd, 'rb') as f:
                out += f.read()
    with open(outputname, 'wb') as dumpfile:
        dumpfile.write(out)


def clean_files(dir, files_list):
    ref = os.getcwd()
    os.chdir(dir)
    for file in files_list:
        if os.path.isfile(file):
            os.remove(file)
    os.chdir(ref)


def build_env_from_compiler(compiler):
    cmd_env = []
    if compiler.ldpath != " " or compiler.otherenvs != [] or compiler.type == "angle":
        cmd_env.append("env")
        if compiler.ldpath != " ":
            cmd_env.append("LD_LIBRARY_PATH="+compiler.ldpath)
        if compiler.type == "angle":
            cmd_env.append("ANGLE_DEFAULT_PLATFORM=vulkan")
        if compiler.vkfilename != " ":
            cmd_env.append("VK_ICD_FILENAMES="+compiler.vkfilename)
        for otherenv in compiler.otherenvs:
            cmd_env.append(otherenv)
    return cmd_env


def find_buffer_file(dir):
    file_list = os.listdir(dir)
    buffer_files = []
    if dir[-1] != "/":
        dir += "/"
    for file in file_list:
        if os.path.isfile(dir+file):
            if "buffer_" in file:
                buffer_files.append(file)
    return buffer_files


def comparison_helper(files):
    comparison_values = []
    for file in files:
        comparison_values.append([file])

    i = 0
    while i < len(comparison_values) - 1:
        reference = comparison_values[i]
        for next_files in comparison_values[i+1:]:
            if next_files != reference[0]:
                if filecmp.cmp(reference[0],next_files[0],False):
                    reference += next_files
                    comparison_values.remove(next_files)
        i+= 1

    return comparison_values