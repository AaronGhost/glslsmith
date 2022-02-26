# Copyright 2021 The glslsmith Project Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
meson -D prefix="${HOME}/llvmpipe/install" -D dri-drivers-path=${HOME}/llvmpipe/install -D egl=enabled -D gles1=enabled -D gles2=enabled -D dri-drivers=auto -D vulkan-drivers=swarst -D gallium-drivers=swrast -D glx=dri -Dplatform=x11
echo "ninja"
ninja
ninja install
