#version 310 es
int SAFE_ABS(int p0);
int SAFE_DIV(int p0, int p1);
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
layout(std430, binding = 1) buffer buffer_1 {
 readonly uint ext_3;
 coherent int ext_4;
};
layout(std430, binding = 3) buffer buffer_3 {
 writeonly uint ext_7[9];
};
int SAFE_DIV(int A, int B)
{
 return B == 0 || A == -2147483648 && B == -1 ? A / 2 : A / B;
}
int SAFE_ABS(int A)
{
 return A == -2147483648 ? 2147483647 : abs(A);
}
void main()
{
 const ivec4 var_0[2] = ivec4[2](ivec4(1), ivec4(1));
 (ext_7[SAFE_ABS(((((var_0[SAFE_ABS((var_0[SAFE_ABS(ext_4) % var_0.length()]).b) % var_0.length()]).ttss.gb.yy[1] - ext_4) - (- var_0[SAFE_ABS(var_0[SAFE_ABS(var_0[SAFE_ABS(ext_4) % var_0.length()].brg[1]) % var_0.length()].z) % var_0.length()].rgga.zx.yxx[0])) - (SAFE_DIV(- ext_4, - 2018396466)))) % ext_7.length()]) = 1u;
}

