#!/bin/bash

# Move the service_names.txt amd checkbox_states files if they exist
echo Preparing for install...
if [ -s SimplePiStats/config.ini ]; then
  sudo mv SimplePiStats/config.ini /
fi

if [ -d SimplePiStats/service_icons ]; then
  sudo mv SimplePiStats/service_icons /
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
python -m pip install -r requirements.txt --break-system-packages  > /dev/null 2>&1
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash > /dev/null 2>&1
sudo apt-get install speedtest > /dev/null 2>&1

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


if [ -d /service_icons ]; then
  rm -rf service_icons
  sudo mv /service_icons .
fi

if [ -f /config.ini ]; then
  rm -rf config.ini
  sudo mv /config.ini .
fi

# Remove unnecessary local files
echo Cleaning up...
rm install.sh readme.md SimplePiStats.service requirements.txt .gitignore
rm -rf .git

# Enable the service
sudo systemctl enable SimplePiStats
shaFromGH=$( git ls-remote https://github.com/purpledalek/SimplePiStats.git main | cut -f 1)
sed -i "1 s|lastSha=.*|lastSha=$shaFromGH|" update.sh

echo Install complete!

# (re)start the service and show logs once install complete
echo Starting service... Please wait...
sudo systemctl daemon-reload
sudo systemctl enable SimplePiStats
sudo systemctl restart SimplePiStats && timeout 10 journalctl -u SimplePiStats --since "0 seconds ago" -f --output=cat