# How to install
Simply run this command!

`bash <(curl -s https://raw.githubusercontent.com/purpledalek/SimplePiStats/main/install.sh)`

Running this command after installation will also let you update it!

# How to use
Type the following into a web browser `<your pi's local ip address>:5555`. If you need help finding your Pi's local IP address, simply ssh into the Pi, and type in `hostname -I`, your Pi's local IP address is everything before the space.

# How to read the stats
## How to read the CPU state
:] Means your Pi's CPU is happy!

:| Means your Pi's CPU is under a bit of load.

\>:] Angy.

## How to read the temperature
🔥 Means your Pi's temperature is around normal.

🔥🔥 Means your Pi's temperature is a little bit warm.

🔥🔥🔥 Means your Pi's temperature is above 60 degrees, and you should probably do something very quickly.

# How to add services
Add the names of the services you want to track the activity of to a text file called `services.txt`, with a new service on each line.