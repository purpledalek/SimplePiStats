#!/bin/bash

# Move the service_names.txt amd checkbox_states files if they exist
echo Preparing for install...
if [ -s SimplePiStats/static/services/service_names.txt ]; then
  sudo mv SimplePiStats/static/services /
fi

if [ -s SimplePiStats/static/checkbox_states.txt ]; then
  sudo mv SimplePiStats/static/checkbox_states.txt /
fi

# Remove previous installation
if [ -d SimplePiStats ]; then
  rm -rf SimplePiStats
fi

# Clone the latest version of the repo
echo Cloning from repo...
git clone https://github.com/purpledalek/SimplePiStats.git SimplePiStats > /dev/null 2>&1

cd SimplePiStats || return

# Install dependencies
echo Installing dependencies...
pip install -r requirements.txt  > /dev/null 2>&1

# Update service file with correct paths
echo Setting up file structure...
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$(pwd)|; s|User=.*|User=$(whoami)|" SimplePiStats.service

# Remove existing service file and directory
echo Setting up service and relocating files...
if [ -f /lib/systemd/system/SimplePiStats.service ]; then
  sudo systemctl stop SimplePiStats
  sudo rm -f /lib/systemd/system/SimplePiStats.service
fi

# Copying the updated service file
sudo cp SimplePiStats.service /lib/systemd/system/SimplePiStats.service


if [ -d /services ]; then
  rm -rf static/services
  sudo mv /services static/
fi

if [ -f /checkbox_states.txt ]; then
  rm -rf static/checkbox_states.txt
  sudo mv /checkbox_states.txt static/
fi

echo Starting service...
# Enable and start the service
sudo systemctl enable SimplePiStats
sudo systemctl start SimplePiStats

# Remove unnecessary local files
echo Cleaning up...
rm install.sh readme.md SimplePiStats.service
if [ -f static/services/icons/placeholder.txt ]; then
rm static/services/icons/placeholder.txt
fi

echo Install complete!