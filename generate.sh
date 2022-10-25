cd scripts
# Generate 1000 shaders using glslsmith without reconditioning
echo $(date +%s)
python exec_glslsmith.py --seed 0 --shader-count 1000 --generate-only
echo $(date +%s)

# Generate 1000 shaders using glslsmith with reconditioning
python exec_glslsmith.py --seed 0 --shader-count 1000 --generate-only --recondition
echo $(date +%s)
