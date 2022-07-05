![Tests](https://github.com/AaronGhost/glslsmith/actions/workflows/default-workflow.yml/badge.svg)

# glslsmith

glslsmith is a random shader generator developed to find bugs in GLSL compilers.
The generator code can be found as part of the Graphicsfuzz repository. This repository contains scripts codes which enable to install and run automatically the generator to identify bugs.

The bugs found so far thanks to the tool can be found in the https://github.com/AaronGhost/glslsmith-bugs-tracker/issues. You are more than welcome to add your own bugs in the repository.


## Installation

The graphicsfuzz component of the project requires maven to run. For Debian-based distribution run:
```
apt install maven
```

Clone the repository and run the install command with python3 from the root of the project. 
```
python3 install.py
```
You can manually edit the resulting config file (located in scripts/config.xml) to add or change the settings of a non-functioning compiler.

By default, the script install glsl-reduce as default reducer, it is discouraged to change that behaviour. Extra reducers can however be added. Please note, the project does not support multi-threading for the reducer.


An example of config file is given below


## Running the project
 
To run the project in continuous mode and look for potential bug in graphics compiler, use the ```execute_glslsmith``` script.

By default execute_glslsmith generates a single batch of shaders, execute them as either interesting or not and keep the resulting shaders in ```glslsmithoutput/keptshaders```.
Corresponding buffers can be found in ```glslsmithoutput/keptbuffers```

```
cd scripts
python3 execute_glslsmith.py
```

To launch the project in autonomous mode, provide the following options:
* ```--continuous``` to loop through new batch generations indefinitely
* ```--reduce``` to reduce interesting shaders at the end of each batch execution

To change the reducer used, pass the extra ```--reducer REDUCER_NAME``` option.

Please note, by default time-outs will not be reduced.

## Getting statistics about current kept shaders

The stats_buffer scripts enables to get some statistics about the kept shaders.
To work correctly, you will need both the shaders and the buffers outputs (in ```glslsmithoutput/keptshaders``` and ```glslsmithoutput/keptbuffers```)

```
python3 stats_buffer.py
```

By default, the script only reports summary information. To get more extensive information about the shaders showing different values with one of the compiler, run
```
python3 stats_buffer.py --report-seed COMPILER
```

If you are looking at a file and want to know which compiler presented a different value:
```
python3 stats_buffer.Py --report-seed all | grep 4_LAST_DIGITS
```

## Performing manual reduction

The script which helps with manual reduction is ```reduction_helper.py```:
* Provide the name of the shader
* Read the error code (1000: crash, 2000: timeout, 3000: one compiler "miscompilation", 4000:different values across compilers)

```
python3 reduction_helper.py --shader-name SHADER
```

By default, the script erases the buffers and the post-processed shader at the end of the execution.
* To prevent the suppression of the buffers, pass the ```--no-cleaning``` option.
* To deactivate the post-processing step, pass the ```--no-postprocessing``` option.

A typical manual reduction includes a couple of calls to verify if an error code is produced with:
```
python3 reduction_helper.py --shader-name SHADER --no-cleaning
```
And potential calls to (to verify if the post-processing is needed to create the bug):
```
python3 reduction_helper.py --shader-name SHADER --no-cleaning --no-postprocessing
```

You can also reduce the file directly on the post-processed version of the shader (the file is a bit more difficult to read).


## Performing automatic reduction

Use ```automate_reducer.py``` to perform automatic reduction:

* To reduce all non-already reduced shaders in the keptshaders directoy:
```
python3 automate_reducer.py --batch-reduction
```
* To reduce a single shader
```
python3 automate_reducer.py --test-file-name SHADER_NAME
```

To force the reduction of shaders which times out, pass the extra option
```
python3 automate_reducer.py --test-file-name SHADER_NAME --reduce-timeout
```

To collect statistics, on the reduction attempts (time and number of test calls):

```
python3 automate_reducer.py --test-file-name SHADER_NAME --instrumentation
python3 automate_reducer.py --batch-reduction --instrumentation
```

## Trouble-shouting the framework

### Trouble-shouting the GraphicsFuzz installation

* If server-thrift gen refuses to compiler, either:
  * Change the source and targets version to 1.8 in the pom file (server-thrift-file)
  ```xml
  <properties>
    <maven.compiler.source>1.6</maven.compiler.source>
    <maven.compiler.target>1.6</maven.compiler.target>
  </properties>
  ```
  * Enforce that the java compiler, uses java 8
* If glslangValidator is not found in maven (.m2/[...]/bin/linux/glslangValidator)
  * Install glslangValidator (either via apt or sources)
  * Create the bin directory and the linux directory
  * Create a symlink to glslangValidator
  
### Example of config file 

```xml
<?xml version="1.0" ?>
<config>
	<dirsettings>
		<graphicsfuzz>[ROOT]/graphicsfuzz/</graphicsfuzz>
		<execdir>[ROOT]</execdir>
		<shaderoutput>./glslsmithoutput/shaders/</shaderoutput>
		<dumpbufferdir>./glslsmithoutput/buffers/</dumpbufferdir>
		<keptbufferdir>./glslsmithoutput/keptbuffers/</keptbufferdir>
		<keptshaderdir>./glslsmithoutput/keptshaders/</keptshaderdir>
	</dirsettings>
	<compilers>
		<compiler>
			<name>nvidia</name>
			<renderer>NVIDIA</renderer>
			<type>independent</type>
			<LD_LIBRARY_PATH> </LD_LIBRARY_PATH>
			<VK_ICD_FILENAMES> </VK_ICD_FILENAMES>
			<otherenvs> </otherenvs>
		</compiler>
		<compiler>
			<name>llvmpipe</name>
			<renderer>llvmpipe</renderer>
			<type>independent</type>
			<LD_LIBRARY_PATH>[WHERE libEgl IS]/</LD_LIBRARY_PATH>
			<VK_ICD_FILENAMES> </VK_ICD_FILENAMES>
			<otherenvs> </otherenvs>
		</compiler>
		<compiler>
			<name>swiftshader</name>
			<renderer>SwiftShader</renderer>
			<type>angle</type>
			<LD_LIBRARY_PATH>[angle]/out/Debug</LD_LIBRARY_PATH>
			<VK_ICD_FILENAMES>[angle]/out/Debug/vk_swiftshader_icd.json</VK_ICD_FILENAMES>
			<otherenvs> </otherenvs>
		</compiler>
	</compilers>
	<shadertools>
		<shadertool>
			<name>shadertrap</name>
			<path>[shadertrap]/build/src/shadertrap/shadertrap</path>
			<extension>.shadertrap</extension>
		</shadertool>
		<shadertool>
			<name>amber</name>
			<path>[amber]/out/Debug/amber</path>
			<extension>.amber</extension>
		</shadertool>
	</shadertools>
	<reducers>
		<reducer>
			<name>glsl-reduce</name>
			<command>mvn -f [ROOT]/graphicsfuzz/pom.xml -pl reducer exec:java "-Dexec.mainClass=com.graphicsfuzz.reducer.tool.GlslReduce" -Dexec.args="[ROOT]/test.json [ROOT]/interesting.sh --output=[ROOT]/"</command>
			<interesting>interesting.sh</interesting>
			<input_file>test.comp</input_file>
			<output_file>test_reduced_final.comp</output_file>
			<extra_files>
				<length>1</length>
				<file_0>test.json</file_0>
			</extra_files>
		</reducer>
	</reducers>
</config>
```

### Manually reinstall graphicsFuzz

```
cd graphicsfuzz
mvn -Dmaven.test.skip=True install
```
