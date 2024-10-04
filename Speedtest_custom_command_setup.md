# Speedtest custom command setup

If you wish to have a speedtest on SimplePiStats, just run the following commands on your pi

```bash
cd /usr/bin
wget https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-aarch64.tgz
tar zxvf ookla-speedtest-1.2.0-linux-aarch64.tgz
rm ookla-speedtest-1.2.0-linux-aarch64.tgz
```

then add this into `SimplePiStats/custom_js` as something like `speedtest.js`

```js
commandBox = document.getElementById("runCommand")
testButton = document.createElement("button")
testButton.innerText = "Run speed test"
testButton.addEventListener("click", function() {speedtest()})
commandBox.insertBefore(testButton , commandBox.querySelector("#commandReturn"))

function speedtest() {
    runCommand("speedtest")
}
```

This will give you the full output from the `speedtest` command as if you had run it on the Pi manually in the "Command output" box.

Please note; to get an output other than "Please wait..." could take a while depending on your internet connection, as SimplePiStats waits until the entire speedtest is done, and it has a response back from Ookla.