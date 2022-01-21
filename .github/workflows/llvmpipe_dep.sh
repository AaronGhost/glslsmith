# Install llvmpipe dependencies
sudo sed -i '/deb-src/s/^# //' /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y libegl1-mesa-dev
sudo apt-get build-dep -y mesa
pip install Mako
