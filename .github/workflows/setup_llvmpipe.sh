MESA_VERSION="mesa-21.1.7"

# Install llvmpipe dependencies
sudo apt-get install -y libegl1-mesa-dev
sudo apt-get build-dep -y mesa
pip install Mako
sudo apt-get install -y ninja-build
sudo apt-get install -y meson

# Download mesa
curl -fsSL -o mesa-src.tar.xf "https://archive.mesa3d.org/${MESA_VERSION}.tar.xz"
tar xf mesa-src.tar.xf

# Install mesa
mkdir build
mkdir install
cd build
meson -D prefix="${HOME}/llvmpipe/install" -D dri-drivers-path=${HOME}/llvmpipe/install -D egl=enabled -D gles1=enabled -D gles2=enabled -D dri-drivers=auto -D vulkan-drivers="" -D gallium-drivers=swrast -D glx=dri
ninja
ninja install
