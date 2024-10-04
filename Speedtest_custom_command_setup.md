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
    runCommand("echo Please wait...")
    runCommand("speedtest")
}
```

This will give you the full output from the `speedtest` command as if you had run it on the Pi manually in the "Command output" box. Feel free to copy this code and insert it into `custom_js`. If, however, you want to reduce the output of this command, then read on.

```js
async function test() {
    runCommand("echo Please wait...")
        output = await runCommand("speedtest", false, true)
        const download_regex = /Download: (.*) \(/
        download = download_regex.exec(output)
        const upload_regex = /Upload: (.*) \(/
        upload = upload_regex.exec(output)
        ping_regex = /Idle Latency: (.*ms) /
        ping = ping_regex.exec(output)
        runCommand("echo Download: " + download[1] + "\nUpload: " + upload[1] + "\nPing: " + ping[1])
}
```
(Please note that the function is now asynchronous)

Now pressing the button will only print out the download and upload speed results, along with the latency (or ping), making the information more concise. This uses JavaScript regex to parse the section(s) of the result you're looking for. This code can be copied verbatim, or modified to suit your needs.

Please note; to get an output other than "Please wait..." could take a while depending on your internet connection, as SimplePiStats waits until the entire speedtest is done, and it has a response back from Ookla.