import sys
from subprocess import run
import os
import shutil
import argparse
import common


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Execute Glslsmith generator and sort results")
    parser.add_argument('--seed', dest='seed', default=-1)
    parser.add_argument('--shader-count', dest='shadercount', default=50, type=int)
    parser.add_argument('--syntax-only', dest='syntaxonly', action='store_true')
    parser.add_argument('--generate-only', dest='generateonly', action='store_true')
    parser.add_argument('--no-generation', dest='nogeneration',action='store_true')
    parser.add_argument('--diff-files-only', dest='diffonly', action='store_true')
    parser.add_argument('--no-compiler-validation', dest='validatecompilers', action='store_false')
    parser.add_argument('--continuous', dest='continuous', action='store_true')
    parser.add_argument('--config-file', dest='config', default="config.xml")
    ns = parser.parse_args(sys.argv[1:])
    # temp value for compiler validation (not revalidating on loops)
    validate_compilers = ns.validatecompilers
    # Get the config files (execution directories and tested compilers)
    exec_dirs = common.load_dir_settings(ns.config)
    compilers = common.load_compilers_settings(ns.config)
    batch_nb = 1
    # go to generation location
    seed = 0
    if ns.seed != -1:
        seed = ns.seed
    while batch_nb == 1 or ns.continuous:
        if not ns.diffonly:
            if not ns.nogeneration:
                # generate programs and seed reporting
                cmd = ["mvn", "-f", exec_dirs.graphicsfuzz + "pom.xml", "-pl", "glslsmith", "-q", "-e"
                    , "exec:java", "-Dexec.mainClass=com.graphicsfuzz.GeneratorHandler"]

                args = r'-Dexec.args=--shader-count ' + str(ns.shadercount) + r' --output-directory ' + exec_dirs.shaderoutput
                if ns.seed != -1:
                    args += r' --seed ' + str(ns.seed)
                cmd += [args]

                process_return = run(cmd, capture_output=True, text=True)
                if ("ERROR") in process_return.stdout:
                    print("error with glslsmith, please fix them before running the script again")
                    print(process_return.stdout)
                    return
                for line in process_return.stdout.split("\n"):
                    if "Seed:" in line:
                        print(line)
                        seed = int(line.split(':')[1])

                print("Generation of " + str(ns.shadercount) + " shaders done")
                if ns.generateonly:
                    return

            # execute actions on generated shaders
            if ns.syntaxonly:
                # Execute the program with the default implementation
                for i in range(ns.shadercount):
                    cmd = [exec_dirs.shadertrap,
                           exec_dirs.shaderoutput + "test_" + str(i) + ".shadertrap"]
                    process_return = run(cmd, capture_output=True, text=True)
                    if "SUCCESS!" not in process_return.stderr:
                        print("Error on shader " + str(i))
                        print(process_return.stderr)
                    else:
                        print("Shader " + str(i) + " validated")
                # Clean the directory after usage and exit
                buffers = common.find_buffer_file(os.getcwd())
                common.clean_files(os.getcwd(), buffers)
                print("Compilation of all programs done")
                return
            # Validate compilers on the first program instance
            if validate_compilers:
                for compiler in compilers:
                    cmd_ending = [exec_dirs.shadertrap, "--show-gl-info",
                                  "empty.shadertrap"]
                    cmd = common.build_env_from_compiler(compiler) + cmd_ending
                    process_return = run(cmd, capture_output=True, text=True)
                    buffers = common.find_buffer_file(os.getcwd())
                    common.clean_files(os.getcwd(), buffers)
                    if compiler.renderer not in process_return.stdout:
                        print("compiler not found or not working: " + compiler)
                        print(process_return.stdout)
                        print(process_return.stderr)
                        return
                print("compilers validated")
                validate_compilers = False
            buffers = common.find_buffer_file(exec_dirs.dumpbufferdir)
            common.clean_files(exec_dirs.dumpbufferdir, buffers)
            # Execute program compilation on each compiler and save the results for the batch
            for i in range(ns.shadercount):
                for compiler in compilers:
                    cmd_ending = [exec_dirs.shadertrap,
                                  exec_dirs.shaderoutput + "test_" + str(i) + ".shadertrap"]
                    cmd = common.build_env_from_compiler(compiler) + cmd_ending
                    process_return = run(cmd, capture_output=True, text=True)
                    # Detect error at compilation time
                    if 'SUCCESS!' not in process_return.stderr:
                        print("Error on shader " + str(i) + " with " + compiler.name)
                        print(process_return.stderr)
                    # Concatenate files to a single output per test
                    buffer_files = common.find_buffer_file(os.getcwd())
                    file_result = "buffer_" + compiler.name + "_" + str(i) + ".txt"
                    common.concatenate_files(file_result, buffer_files)
                    # Move the results to the dumpbuffer
                    shutil.move(file_result, exec_dirs.dumpbufferdir)
                    buffer_files.append(file_result)
                    common.clean_files(os.getcwd(), buffer_files)
        # Compare outputs and save buffers
        # Check that we can compare outputs across multiple compilers
        if len(compilers) == 1:
            print("Impossible to compare outputs for only one compiler")
            return
        for i in range(ns.shadercount):
            # Reference buffers for a given shader instance
            buffers_files = []
            for compiler in compilers:
                buffers_files.append(exec_dirs.dumpbufferdir + "buffer_" + compiler.name + "_" + str(i) + ".txt")
            # Compare and check back the results
            values = common.comparison_helper(buffers_files)
            if len(values) != 1:
                print("Different results across implementations for shader " + str(seed + i))
                # Move shader
                shutil.move(exec_dirs.shaderoutput + "test_" + str(i) + ".shadertrap",
                            exec_dirs.keptshaderdir + str(seed + i) + ".shadertrap")
                # Move buffers
                for compiler in compilers:
                    shutil.move(exec_dirs.dumpbufferdir + "buffer_" + compiler.name + "_" + str(i) + ".txt",
                                exec_dirs.keptbufferdir + compiler.name + "_" + str(seed + i) + ".txt")
        # Set flag for while loop and print the number of batch
        print("Batch " + str(batch_nb) + " processed")
        batch_nb += 1


if __name__ == "__main__":
    main()
