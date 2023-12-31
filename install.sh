#!/bin/bash

repo_url="https://github.com/purpledalek/SimplePiStats.git"
clone_dir="SimplePiStats"

# Check if a previous installation exists and delete if so
if [ -d "$clone_dir" ]; then
  rm -rf "$clone_dir"
fi

# Clone the latest version of the repo
git clone "$repo_url" "$clone_dir"

# cd into newly created folder
cd SimplePiStats || return

# install dependencies
pip install flask

# change the working directory and user to be correct in the service file
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$(pwd)|; s|User=.*|User=$(whoami)|" service/SimplePiStats.service

if [ -f "/lib/systemd/system/SimplePiStats.service" ]; then
  sudo systemctl stop SimplePiStats.service
  rm -f "/lib/systemd/system/SimplePiStats.service"
fi

# copy the service file
sudo cp service/SimplePiStats.service /lib/systemd/system

# enable the service so it starts on boot then start it
sudo systemctl enable SimplePiStats
sudo systemctl start SimplePiStats

# remove files that are unnecessary to keep locally (it's only the now redundant local copy of the service file that is deleted, the one in /lib/systemd/system is kept intact)
rm install.sh
rm readme.md
rm -rf service