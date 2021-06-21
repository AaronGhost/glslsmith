import collections
import os.path
import subprocess
from xml.dom import minidom
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Configure and install the glslsmith scripts")
    parser.add_argument("--configure-only", help="Skips the first installation part", dest="configureonly", action="store_true")

    ns = parser.parse_args(sys.argv[1:])

    if not ns.configureonly:
        print('This script helps to configure and install glslsmith, a random project generator built as part of graphicsfuzz')
        print('It has been sought as a way to provide system-dependent path to the execution scripts')
        print('All paths can be given as relative to this position or as absolute path')

        print('\n[1/4] installing the program generator')

        execute_with_popen(['git', 'submodule', 'init'])
        execute_with_popen(['git', 'submodule', 'update'])
        #execute_with_popen(["mvn","-Dmaven.test.skip=true","-q", "-am","-pl",":graphicsfuzz", "package"],"./graphicsfuzz")
        execute_with_popen(["mvn","-Dmaven.test.skip=true","-q", "install"],"./graphicsfuzz")

    print('\n[2/4] Configuration of the generator working directories')
    print('Let any directory empty to use the default one which will be created in the project')
    mkdirs = []
    outputshaders = "./glslsmithoutput/shaders/"
    input_value = input('Specify a location to dump the generated shaders (default: '+outputshaders+"): ")
    if input_value != "":
        outputshaders = normalize_path(input_value)
    else:
        mkdirs.append(outputshaders)
    dumpbuffer = "./glslsmithoutput/buffers/"
    input_value = input('Specify a location to dump the buffers from execution (default: '+dumpbuffer+"): ")
    if input_value != "":
        dumpbuffer = normalize_path(input_value)
    else:
        mkdirs.append(dumpbuffer)
    keptbuffer = "./glslsmithoutput/keptbuffers/"
    input_value = input("Specify a location to dump the buffers exhibiting different values across compilers (default: "+keptbuffer+"): ")
    if input_value != "":
        keptbuffer = normalize_path(input_value)
    else:
        mkdirs.append(keptbuffer)
    keptshader = "./glslsmithoutput/keptshaders/"
    input_value = input("Specify a location to dump the associated shaders (default: "+keptshader+"): ")
    if input_value != "":
        keptshader = normalize_path(input_value)
    else:
        mkdirs.append(keptshader)
    for mkdir_dir in mkdirs:
        current_dir = ""
        for dir in mkdir_dir.split("/"):
            if dir != "." and not os.path.isdir(current_dir+"/"+dir):
                if current_dir == "":
                    execute_with_popen(["mkdir", dir])
                else:
                    execute_with_popen(["mkdir", dir],current_dir)
            current_dir += dir + "/"


    print("\n[3/4] Configuration of shader embedding language")
    print("At the moment, the only supported language to embed the shader is shadertrap")
    input_value = input("Please specify the path of the shadertrap executable: ")
    while input_value == "":
        input_value = input("Please specify the path of the shadertrap executable: ")
    shadertrap_dir = input_value

    print("\n[4/4] Configuration of the tested compilers")
    print("Multiple compilers are necessary to test the buffer outputs associated with a specific shader")
    print("For each compiler, please specify:")
    print("- a compiler name (used to identify the buffer)")
    print("- a renderer string (used to validate the compiler at runtime)")
    print("- the type (independent / angle with the associated ANLGE_DEFAULT_PLATFORM environment variable")
    print("- the LD_LIBRARY_PATH environment variable value")
    print("- VK_ICD_FILENAMES environment variable value")
    print("- other environment variables if necessary")
    print("\nIf an environment variable is not required, simply let the value empty")

    compiler_number = 1
    compilers = []

    while True:
        print("Enter the values for the compiler n°"+str(compiler_number)+":")
        compiler_name = input("Specify the compiler name:")
        compiler_renderer = input("Specify the renderer string to validate the compiler:")
        compiler_type = input("Specify the compiler type (independent/angle):")
        ldpath = input("Specify LD_LIBRARY_PATH (or press enter):")
        if ldpath == "":
            ldpath = " "
        vkfilename = input("Specify VK_ICD_FILENAMES (or press enter):")
        if vkfilename == "":
            vkfilename = " "
        otherenvs = []
        while True:
            otherenvs_decision = input("Do you want to add another environment variable? [y/N]:")
            if otherenvs_decision != "y":
                break
            otherenv = input("Specify the extra environment variable:")
            otherenvs.append(otherenv)
        extra_compiler_decision = input("\nDo you want to add another compiler? [y/N]:")

        compilers.append([compiler_name, compiler_renderer, compiler_type, ldpath, vkfilename, otherenvs])
        if extra_compiler_decision != "y":
            break
        compiler_number += 1

    # Build xml file

    config_location = "./scripts/config.xml"
    print("\nCurrent configuration will be saved to: "+config_location)
    impl = minidom.getDOMImplementation()
    config_document = impl.createDocument(None, "config",None)
    # Dir settings
    dirsettings = config_document.createElement("dirsettings")
    graphicsfuzz = config_document.createElement("graphicsfuzz")
    graphicsfuzz.appendChild(config_document.createTextNode('./graphicsfuzz/'))
    dirsettings.appendChild(graphicsfuzz)
    shadertrap = config_document.createElement("shadertrap")
    shadertrap.appendChild(config_document.createTextNode(shadertrap_dir))
    dirsettings.appendChild(shadertrap)
    shaderoutput = config_document.createElement("shaderoutput")
    shaderoutput.appendChild(config_document.createTextNode(outputshaders))
    dirsettings.appendChild(shaderoutput)
    dumpbufferdir = config_document.createElement("dumpbufferdir")
    dumpbufferdir.appendChild(config_document.createTextNode(dumpbuffer))
    dirsettings.appendChild(dumpbufferdir)
    keptbufferdir = config_document.createElement("keptbufferdir")
    keptbufferdir.appendChild(config_document.createTextNode(keptbuffer))
    dirsettings.appendChild(keptbufferdir)
    keptshaderdir = config_document.createElement("keptshaderdir")
    keptshaderdir.appendChild(config_document.createTextNode(keptshader))
    dirsettings.appendChild(keptshaderdir)

    # Compilers settings
    compilers_xml = config_document.createElement("compilers")
    for compiler in compilers:
        compiler_xml = config_document.createElement("compiler")
        name = config_document.createElement("name")
        name.appendChild(config_document.createTextNode(compiler[0]))
        compiler_xml.appendChild(name)
        renderer = config_document.createElement("renderer")
        renderer.appendChild(config_document.createTextNode(compiler[1]))
        compiler_xml.appendChild(renderer)
        type = config_document.createElement("type")
        type.appendChild(config_document.createTextNode(compiler[2]))
        compiler_xml.appendChild(type)
        ldpath = config_document.createElement("LD_LIBRARY_PATH")
        ldpath.appendChild(config_document.createTextNode(compiler[3]))
        compiler_xml.appendChild(ldpath)
        vkfilename = config_document.createElement("VK_ICD_FILENAMES")
        vkfilename.appendChild(config_document.createTextNode(compiler[4]))
        compiler_xml.appendChild(vkfilename)
        otherenvs = config_document.createElement("otherenvs")
        if compiler[5]:
            length = config_document.createElement("length")
            length.appendChild(config_document.createTextNode(len(compiler[5])))
            otherenvs.appendChild(length)
            i = 0
            for otherenv in compiler[5]:
                otherenv_xml = config_document.createElement("env_"+str(i))
                otherenv_xml.appendChild(config_document.createTextNode(otherenv))
                otherenvs.appendChild(otherenv_xml)
                i+= 1
        else:
            otherenvs.appendChild(config_document.createTextNode(" "))
        compiler_xml.appendChild(otherenvs)
        compilers_xml.appendChild(compiler_xml)

    # Dump xml file
    config_document.documentElement.appendChild(dirsettings)
    config_document.documentElement.appendChild(compilers_xml)
    config_file = open(config_location, "w")
    config_file.write(config_document.toprettyxml())



def normalize_path(path):
    if path[-1] != "/":
        path += "/"
    return path


def execute_with_popen(cmdline, directory='./'):
    process = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=directory)
    print(subprocess.list2cmdline(process.args))

    while True:
        output = process.stdout.readline()
        if output.strip() != "":
            print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            if return_code == -1:
                return
            # Process has finished, read rest of the output
            lines = process.stdout.readlines()
            if len(lines) == 0:
                print("ok")
            for line in lines:
                if line.strip() != "":
                    print(output.strip())
            break

if __name__ == "__main__":
    main()
