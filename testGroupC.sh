cd scripts
# Generate the shaders
python exec_glslsmith.py --seed 0 --shader-count 10000 > groupC.log

python exec_glslsmith.py --seed 0 --shader-count 10000 --generationonly --recondition --extent extra > groupC.log
# For the 50 selected (identical groupA)

