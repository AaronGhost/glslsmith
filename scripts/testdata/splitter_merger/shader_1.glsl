#version 310 es

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
layout(std430, binding = 0) buffer buffer_0 {
 uint ext_0[6];
} ;

void main()
{
  for(int i = 0; i < 6; i++){
    ext_0[i] = 1u;
  }
}
