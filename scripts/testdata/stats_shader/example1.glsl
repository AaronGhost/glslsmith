#version 310 es
int SAFE_DIV_ASSIGN(inout int p0, int p1);
int SAFE_DIV(int p0, int p1);
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
layout(std430, binding = 1) buffer buffer_1 {
 readonly int ext_1;
 readonly uint ext_2[2];
};
layout(std430, binding = 5) buffer buffer_5 {
 coherent uint ext_8;
 coherent int ext_9;
 writeonly uint ext_10;
};
int SAFE_DIV(int A, int B)
{
 return B == 0 || A == -2147483648 && B == -1 ? A / 2 : A / B;
}
int SAFE_DIV_ASSIGN(inout int A, int B)
{
 return B == 0 || A == -2147483648 && B == -1 ? (A /= 2) : (A /= B);
}
void main()
{
 SAFE_DIV_ASSIGN(ext_9, - (1 - SAFE_DIV(1, ext_1)));
}

