# How to install
Simply change directory (`cd`) into the directory where you want to store SimplePiStats, then run this command!

`bash <(curl -s https://raw.githubusercontent.com/purpledalek/SimplePiStats/main/install.sh)` Running this command after installation will also let you update it (hint; be sure to run from the same folder as the original installation!)

Alternatively, you can go to the `releases` page and download the `install.sh` file from there

# How to use
Type the following into a web browser `<your pi's local ip address>:5555`. If you need help finding your Pi's local IP address, simply ssh into the Pi, and type in `hostname -I`, your Pi's local IP address is everything before the space.

## How to read the CPU state
:] Means your Pi's CPU is happy! (Under 40%)

:| Means your Pi's CPU is under a bit of load, but it's still okay (Between 40% and 75%)

\>:[ Means your Pi is Angry. (Over 75%)

## How to read the temperature
🔥 Means your Pi's temperature is around normal. (Below 50°C)

🔥🔥 Means your Pi's temperature is a little bit warm. (Between 50 and 70°C)

🔥🔥🔥 Means your Pi's H O T! (above 70°C, and you should probably do something rather quickly.)

# How to add services
Add the names of the services you want to track the activity of to a text file called `service_names.txt` which will be generated after the webpage is run if it does not exist, (which is in `static -> services`) with a new service on each line. To add a group of services please add them in a comma separated list surrounded by square brackets. The first item in the list will serve as the service title.

Example: `[service title, service 1, service 2, ... etc.]`

If you wish to include an icon next to your service name please place a png in the services folder with the same name as you've given the service in the document. This will also work if your service is in a group.

If the service you're adding has an associated webpage on a certain port, such as Syncthing, you can put the port number after the service name (using a `/` as a delimiter) to get a link to that service's HTML page/GUI. For example, adding `syncthing/8384` will create a button next to the syncthing listing that takes you straight to your machine's local GUI. This will also work if your service is in a group.

note. images may be unstable on iPhone, refreshing is the only known fix for this issue