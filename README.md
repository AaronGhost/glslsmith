# glslsmith

glslsmith is a random shader generator developped to find bugs in glsl compilers.
The generator code can be found as part of the Graphicsfuzz repository. This repository contains scripts codes which enable to install and run automatically the generator to identify bugs.

## Installation

Clone the repository and run the install command with python3 for an easy installation.
```
python3 install.py
```
You can manually edit the resulting config file (located in scripts/config.xml) to add or change the settings of a non-functioning compiler)

## Running the project
 
Run the execute_glslsmith.py in the scripts directory. 
```
cd scripts
python3 execute_glslsmith.py --continuous
```

Other options are available to process only a batch or specify a seed value.
