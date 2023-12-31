import subprocess
import time
import datetime
from flask import Flask, render_template, request, jsonify, session
import os

app = Flask(__name__)


@app.route('/')
def index():
    # get output
    cpu_lookup = subprocess.Popen(["top", "-n", "1", "-b"], stdout=subprocess.PIPE, text=True)
    time.sleep(.1)
    for line in cpu_lookup.communicate()[0].split("\n"):
        if line.startswith("%Cpu(s)"):
            cpu = round(100 - float(line.split(",")[3].strip().replace("id", "")), 2)
    if cpu <= 40:
        cpu_status = ":]"
    elif cpu <= 74:
        cpu_status = ":|"
    else:
        cpu_status = ">:["

    temp_lookup = subprocess.Popen(["/usr/bin/vcgencmd", "measure_temp"], stdout=subprocess.PIPE, text=True)
    time.sleep(.1)
    for line in temp_lookup.communicate()[0].split("\n"):
        if line.startswith("temp="):
            cpu_temp = float(line.lstrip("temp=").rstrip("'C"))
    if cpu_temp <= 50:
        temp = "🔥"
    elif cpu_temp <= 60:
        temp = "🔥🔥"
    else:
        temp = "🔥🔥🔥"

    up_since = subprocess.Popen(["uptime", "--since"], stdout=subprocess.PIPE, text=True)
    last_boot = up_since.communicate()[0].strip().replace("\n", "")
    boot_time = str(datetime.datetime.strptime(last_boot, "%Y-%m-%d %H:%M:%S"))

    services = []

    if not os.path.exists(r"services.txt"):
        with open(r"services.txt", 'w') as file:
            pass

    __services__ = open(r"services.txt", "r").read().split("\n")
    if __services__ == [""]:
        services = ["No services found.", "Please add service names", "to services.txt to use this feature,", "or see the readme.md for more info."]
    else:
        for service in __services__:
            if service != "":
                output = ""
                status_check = subprocess.run(["systemctl", "is-active", service], stdout=subprocess.PIPE, text=True).stdout.strip()
                desc = subprocess.run(["systemctl", "show", "-p", "Description", service], stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
                if "-" in desc:
                    output += service.title()
                else:
                    output += desc
                if status_check == "active":
                    output += " 🟢 "
                else:
                    output += " 🔴 "
                output += status_check
                services.append(output)
    return render_template("SimplePiStats.html", cpu_status=cpu_status, boot_time=boot_time, temp=temp, services=" <br> ".join(services))


def purple_dalek():
    print(f"{'Purple Dalek' if purple_dalek.__name__.replace('_', ' ').title() == 'Purple Dalek' else 'Purple Dalek'} wrote this")


# 0 - 40 :]
# 41 - 74 :|
# 75 - 100 >:[


if __name__ == '__main__':
    purple_dalek()
    app.run(host="0.0.0.0", port=5555)
