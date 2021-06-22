import argparse
import filecmp
import os
import subprocess
import sys

from scripts import common


def main():
    parser  = argparse.ArgumentParser(description="Tool to compile and compare shader output in order to help shader reduction")
    parser.add_argument("--overrider-compilers", dest="restrict_compilers", default=[], nargs="+")
    parser.add_argument('--shader-name', dest='shader',default='test.shadertrap')
    parser.add_argument('--ref', type=int, dest="ref", default=-1)
    parser.add_argument('--crash-only', dest='crash',action='store_true')
    parser.add_argument('--config-file', dest='config', default="config.xml")
    ns = parser.parse_args(sys.argv[1:])
    # Parse directory config
    exec_dirs = common.load_dir_settings(ns.config)
    compilers = common.load_compilers_settings(ns.config)
    compilers_dict = {}
    for compiler in compilers:
        if not ns.restrict_compilers or compiler in ns.restrict_compilers:
            compilers_dict[compiler.name] = compiler
    os.chdir("../")

    # Execute the shadertrap file with the different drivers

    results = common.execute_compilation(compilers_dict.values(), exec_dirs.shadertrap, ns.shader, verbose=True)
    if all(results):
        print("No crash")
    else:
        return
    flag = True
    if ns.ref != -1:
        for compiler_name in compilers_dict.keys():
            comparison_result = common.comparison_helper(["buffer_" + compiler_name + ".txt", exec_dirs.keptbufferdir + str(ns.ref)+".txt"])
            if len(comparison_result) == 2:
                print("Buffer difference between test and reference result: " + compiler_name)
                flag = False
        if flag:
            print("No difference between test and reference")

    buffers = []
    for compiler_name in compilers_dict.keys():
        buffers.append("buffer_"+compiler_name + ".txt")
    comparison_result = common.comparison_helper(buffers)
    if len(comparison_result) >= 2:
        text = ""
        for same_result_buffers in comparison_result:
            text += "("
            for buffer_name in same_result_buffers:
                text += buffer_name.split("_")[1].split(".")[0]
                if len(same_result_buffers) != 1 and buffer_name is not same_result_buffers[-2]:
                    text += ", "
            if same_result_buffers is not comparison_result[-2]:
                text += "), "
            else:
                text +=") and "
        text += " show different results"
        print(text)
    else:
        print("No differences between implementations")



if __name__ == "__main__":
    main()
