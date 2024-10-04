# SimplePiStats
A simple UI designed for people running their Raspberry Pi as a server, and who quick and easy to read stats and control of their system.

## Please note: as of early October 2024, the built in speed test was removed. If you wish to re-enable this feature for your install, please see [This guide](https://github.com/purpledalek/SimplePiStats/blob/main/Speedtest_custom_command_setup.md)

## New features!
- The ability to display Docker container information and control containers the same way as systemd services

## How to install/update
Simply change directory (`cd`) into the directory where you want to store SimplePiStats, then run the following command:

`bash <(curl -s https://raw.githubusercontent.com/purpledalek/SimplePiStats/main/install.sh)`

If you with to use SimplePiStats without a virtual environment (venv), use the following command instead:

`bash <(curl -s https://raw.githubusercontent.com/purpledalek/SimplePiStats/main/non-venv_install.sh)`

## How to use
Type the following into a web browser `<your pi's local ip address>:5555`. If you need help finding your Pi's local IP address, simply ssh into the Pi, and type in `hostname -I`, your Pi's local IP address is everything before the space. If you wish to change which port SimplePiStats runs on, you can change the `port` value in the config in settings.

### How to read the CPU state
:] Means your Pi's CPU is happy! (Under 40%)

:| Means your Pi's CPU is under a bit of load, but it's still okay (Between 40% and 75%)

\>:[ Means your Pi is Angry. (Over 75%)

### How to read the temperature
🔥 Means your Pi's temperature is around normal. (Below 50°C)

🔥🔥 Means your Pi's temperature is a little bit warm. (Between 50 and 70°C)

🔥🔥🔥 Means your Pi's H O T! (above 70°C, and you should probably do something rather quickly.)

(Numbers can be accessed for these statistics in Settings if you want a more accurate readout)

## Editing config file
You can either edit the config file by clicking the `Edit config` button in settings, or in the command line with your text editor of choice. The correct syntax for each section is outlined below.
N.B. Editing the `config.ini` file in the command line will require a restart of the SimplePiStats service for the changes to take effect

### Commands
`commands = ["<name that you want on command button> : <command that you run in the console>"]`
(please note that file paths given in commands MUST be absolute)

### Drives
`drives = ["<absolute path to drive location> --exclude=<Any directories you want to exclude> --exclude=<You can do this as many directories as you want for a drive by adding another --exclude flag followed by the new path to exclude>"]`

### Services
`services = ["<name of the service you want to show>/<reference to the port number you want to link to, if any>*"]`

For any of these sections, you denote a new command/drive/service by adding it as a new list item.

*You can add "--no_stop" or "--no_restart" after a service name (or port if applicable) if you wish to not see the specified button. Adding "--no_stop --no_restart" will hide both buttons

### Monitoring services on remote machines
To monitor a service remotely, simply add the "-r" flag followed by the user and ip of the machine you want to get the stats off of.

Example: [`service_name>[/Port_number] -r <remote_user>@<remote_ip>`]

Note: this feature requires setting up a public/private key pair to be established between the machine running SimplePiStats and the remote machine(s) you want to get service stats from. For more info on that [go here](https://ionutbanu.medium.com/setting-up-key-pair-ssh-on-raspberry-pi-9822b20037a0).

To access the webUI of a service that's running on a remote machine, please use [Nginx Proxy Manager](https://nginxproxymanager.com/setup/)'s Stream feature. Simply install and open the Nginx proxy manager, add a stream with the port you want to forward *from* in the `Incoming Port` field, and the local ip and port of the machine you wish to connect to in the `Forward Host` and `Forward Port` boxes respectively. Also, go to the `docker-compose.yml` file for Nginx Proxy Manager and add the ports to that file as explained [here](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/1506#issuecomment-948360527) (this step is very important as it won't forward without this), then take the container down and back up again using `sudo docker compose down && sudo docker compose up -d`!

## Link to webUI of docker containers
To have a docker container name act as a hyperlink for the container's webUI, simply edit `docker_ports.json` or click on `Show config` then `Edit docker ports`, and add the number for the port in the quotes, next to the name of the container you want to link to. If this is a remote device, you'll have to make sure you have an Nginx stream set up, as explained above

## Adding logos to systemd services and docker containers
Simply add the image file to the `service_icons` directory.

## How to change the data background color
You can either change the background color of the data boxes using the color picker in settings, or by editing the hex value in the `config.ini` file

Please note: images may be unstable on iPhone, refreshing is the only known fix for this issue

## Adding custom CSS
You can add a custom CSS file by placing it in the `static` folder, then adding the filename to the config. For example if you have a CSS file called myCustomStyle.css, you can put that in the `static` folder and then add "myCustomStyle.css" to the custom_css line of the config. Any changes made to elements in your custom css file will overwrite the default style for that element.

## Adding custom JavaScript
You can add custom JavaScript by placing as many `.js` files into `custom_js`. Files will be loaded in alphabetical order, below all other JS on the page, just above the closing script tag. This can be used for many things, such as creating buttons that trigger alert or confirmation boxes, which then can be used to trigger other events.

## Possible features
- More icons for popular services