MESA_VERSION="mesa-21.1.7"

# Download mesa
curl -fsSL -o mesa-src.tar.xf "https://archive.mesa3d.org/${MESA_VERSION}.tar.xz"
tar xf mesa-src.tar.xf

# Install mesa
cd ${MESA_VERSION}
mkdir build
mkdir install
cd build
echo "Meson"
meson -D prefix="${HOME}/${MESA_VERSION}/install" -D dri-drivers-path=${HOME}/llvmpipe/install -D egl=enabled -D gles1=enabled -D gles2=enabled -D dri-drivers= -D vulkan-drivers="" -D gallium-drivers=swrast -D glx=dri -Dplatform=x11
echo "ninja"
ninja
ninja install
