lastSha=xxxxxxxxxxxxxxxxx
shaFromGH=$( git ls-remote https://github.com/purpledalek/SimplePiStats.git main | cut -f 1)
if [ "$shaFromGH" == "$lastSha" ]; then
    echo "SimplePiStats is up to date!"
else
    echo "Updating SimplePiStats..."
    cd ../
    bash <(curl -s https://raw.githubusercontent.com/purpledalek/SimplePiStats/main/non-venv_install.sh)
fi
