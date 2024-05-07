import subprocess
import time
import datetime
from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import waitress
import threading
import sys
import dateparser
import pytz
import humanize
import configparser
import ast
import re
import json

app = Flask(__name__)

config = configparser.ConfigParser()

config.read("config.ini")

def conf_get(option: str):
    return ast.literal_eval(config.get("SimplePiStats", option))

# get images for service icons
@app.route('/service_icons/<path:filename>')
def get_image(filename):
    return send_from_directory("service_icons", filename)

if not os.path.exists(r"./config.ini"):
    config["SimplePiStats"] = {
        "address": '"0.0.0.0"',
        "port": "5555",
        "bg_color": '"#084e0a"',
        "commands": [],
        "drives": [],
        "services": [],
        "custom_css": '""'
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)

# Set up listen address and port numbers
listen_address = conf_get("address")
port = conf_get("port")

def service_check(service_):
    output = ""
    stop = True
    restart = True

    if "--no_stop" in service_.lower():
        stop = False
        service_ = service_.lower().replace(" --no_stop", "")
    if "--no_restart" in service_.lower():
        restart = False
        service_ = service_.lower().replace(" --no_restart", "")
    if "/" in service_:
        service = service_.split("/")[0]
        output += f"<div class=\"service innerContainer\" id=\"{service}\"> <div class=\"text\">"
        port = service_.split("/")[1]
        desc = subprocess.run(["systemctl", "show", "-p", "Description", service], stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
        if "-" in desc:
            desc = service.title()
        output += f"<a class=\"service_stats\" id=\"{port}\" target=\"_blank\">{desc}</a>"
    else:
        service = service_
        output += f"<div class=\"service innerContainer\" id=\"{service}\"> <div class=\"text\">"
        desc = subprocess.run(["systemctl", "show", "-p", "Description", service], stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
        if "-" in desc:
            desc = service.title()
        output += "<p class=\"service_stats\">" + desc + "</p>"
    status_check = subprocess.run(["systemctl", "is-active", service], stdout=subprocess.PIPE, text=True).stdout.strip()
    for file in os.listdir(r"service_icons"):
        if service.lower() == file.split(".")[0].lower():
            if status_check == "inactive":
                output += f"<img class=\"service_icon bw\" src=\"service_icons/{file}\">"
            else:
                output += f"<img class=\"service_icon\" src=\"service_icons/{file}\">"
        else:
            pass
    if status_check == "active":
        service_boot_time = subprocess.run(["systemctl", "show", "--property=ActiveEnterTimestamp", service], stdout=subprocess.PIPE, text=True).stdout.strip().removeprefix("ActiveEnterTimestamp=")
        reboot_duration = datetime.datetime.now().replace(tzinfo=pytz.utc, microsecond=0) - dateparser.parse(service_boot_time).replace(tzinfo=pytz.utc, microsecond=0)
        if reboot_duration.seconds < 60:
            reboot_duration = "less than a minute ago"
        else:
            reboot_duration = humanize.naturaltime(reboot_duration, minimum_unit='seconds')
        output += f"<p id=\"status\"> 🟢 </p></div><p id=\"serviceReboot\">Service last restarted {reboot_duration}</p>"
    else:
        output += "<p id=\"status\"> 🔴 </p></div><p id=\"serviceReboot\">Service last restarted N/A</p>"
    if stop == True or restart == True:
        output += f"<div class=\"buttons\">"
        if stop == True:
            output += f"<button onclick=\"handle_button_action('stop/{service}')\" class=\"button\"id=\"stop\">Stop</button>"
        if restart == True:
            output += f"<button onclick=\"restart_confirm('{service}'); handle_button_action('restart/{service}')\"class=\"button\" id=\"restart\">Restart</button>"
        output += "</div>"
    output += "</div>"
    return output


@app.route("/speed_test", methods=['POST'])
def speed_test():
    response = subprocess.Popen('/usr/bin/speedtest --accept-license --accept-gdpr', shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
    ping = re.search('Latency:\s+(.*?s)', response, re.MULTILINE)
    download = re.search('Download:\s+(.*?s)', response, re.MULTILINE)
    upload = re.search('Upload:\s+(.*?s)', response, re.MULTILINE)

    ping = ping.group(1)
    download = download.group(1)
    upload = upload.group(1)

    return jsonify({"ping": ping, "download": download, "upload": upload})

checkboxes = ["serverTimeToggle", "speedTestToggle", "numbersToggle", "diskToggle", "servicesToggle", "commandsToggle", "cfToggle", "fontToggle", "mysteryToggle"]

if not os.path.exists(r".checkbox_states.json"):
    with open(r".checkbox_states.json", 'w') as file:
        init_dict = {}
        for box in checkboxes:
            init_dict[box] = "unchecked"
        file.write(json.dumps(init_dict, indent=len(init_dict)))
        file.close()

def create_command_buttons():
    buttons = []
    commands = conf_get("commands")
    if commands == []:
        buttons.append("<p>No commands found. Please add command names in settings > Edit config to use this feature, or you can hide it using settings. See the <a href=\"https://github.com/purpledalek/SimplePiStats/blob/main/readme.md#editing-config-file\" target=\"_blank\">readme</a> for more info.</p>")
    else:
        for line in commands:
            spl = line.split(":")
            buttons.append(f"<button onclick='runCommand(\"{spl[1].strip()}\")' style=\"margin: 10px\">{spl[0].strip()}</button>")
    return buttons

@app.route('/')
def index():
    # get output
    hostname = subprocess.check_output(['hostname']).decode().strip()
    cpu_lookup = subprocess.Popen(["top", "-n", "1", "-b"], stdout=subprocess.PIPE, text=True)
    time.sleep(.1)
    for line in cpu_lookup.communicate()[0].split("\n"):
        if line.startswith("%Cpu(s)"):
            cpu = round(100 - float(line.split(",")[3].strip().replace("id", "")), 2)
    if cpu <= 40:
        cpu_status = "happy"
    elif cpu <= 74:
        cpu_status = "neutral"
    else:
        cpu_status = "angry"

    with open(r".checkbox_states.json", "r") as file:
        file_contents = json.load(file)
        file.close()

    # 0 - 40 :]
    # 41 - 74 :|
    # 75 - 100 >:[

    boot_time = dateparser.parse(subprocess.Popen(["uptime", "--since"], stdout=subprocess.PIPE, text=True).communicate()[0].strip().replace("\n", "")).astimezone(pytz.utc)

    server_time = datetime.datetime.strptime(subprocess.Popen(["date"], stdout=subprocess.PIPE, text=True).communicate()[0].strip().replace("\n", ""), "%a %d %b %H:%M:%S %Z %Y")
    services = []

    __services__ = conf_get("services")
    if __services__ == []:
        services = ["<p>No services found. Please add services in settings > Edit config to use this feature, or you can hide it using settings. See the <a href=\"https://github.com/purpledalek/SimplePiStats/blob/main/readme.md#editing-config-file\" target=\"_blank\">readme</a> for more info.</p>"]
    else:
        for service in __services__:
            if isinstance(service, list):
                group_title = service.pop(0).title()
                for file in os.listdir(r"service_icons"):
                    if group_title.lower() == file.split(".")[0].lower():
                        group_title = f"<img class=\"group_title_icon\" src=\"service_icons/{file}\">" + group_title
                    else:
                        pass
                services.append("<div style='margin-bottom: 20px;'><b>" + group_title + "</b></div>")
                for serv in service:
                    services.append(service_check(serv))
            else:
                if service != "":
                    services.append(service_check(service))
    temp_lookup = subprocess.Popen(["/usr/bin/vcgencmd", "measure_temp"], stdout=subprocess.PIPE, text=True)
    time.sleep(.1)
    for line in temp_lookup.communicate()[0].split("\n"):
        if line.startswith("temp="):
            temp = float(line.lstrip("temp=").rstrip("'C"))
            Celsius = temp
            Fahrenheit = round(temp * 9 / 5 + 32, 1)
    if Celsius <= 50:
        temp = "1"
    elif Celsius <= 70:
        temp = "2"
    else:
        temp = "3"
    command_buttons = create_command_buttons()
    return render_template("SimplePiStats.html", hostname=hostname, cpu_status=cpu_status, cpu_status_numbers=str(cpu) + "%", boot_time=boot_time, temp=temp, Celsius=str(Celsius) + "°C", Fahrenheit=str(Fahrenheit) + "°F", services=" ".join(services), time_checkbox_state=file_contents.get(checkboxes[0]), speed_checkbox_state=file_contents.get(checkboxes[1]), numbers_checkbox_state=file_contents.get(checkboxes[2]), disk_checkbox_state=file_contents.get(checkboxes[3]), services_checkbox_state=file_contents.get(checkboxes[4]), commands_checkbox_state=file_contents.get(checkboxes[5]), fahrenheit_checkbox_state=file_contents.get(checkboxes[6]), font_checkbox_state=file_contents.get(checkboxes[7]), mystery_checkbox_state=file_contents.get(checkboxes[8]), command_buttons=" ".join(command_buttons), server_time=server_time, div_color=conf_get("bg_color"), port=port, commandsConfig=conf_get("commands"), drivesConfig=conf_get("drives"), servicesConfig=conf_get("services"), addressConfig=listen_address, custom_css=conf_get("custom_css"))

@app.route('/disk_usage', methods=['POST'])
def disk_usage():
    drives_text_file = conf_get("drives")
    if drives_text_file == []:
        ext_drives = ["<p>No external drive paths found. Please add paths in settings > Edit config to use this feature, or you can hide it using settings. See the <a href=\"https://github.com/purpledalek/SimplePiStats/blob/main/readme.md#editing-config-file\" target=\"_blank\">readme</a> for more info.</p>"]
    else:
        paths = []
        for path in drives_text_file:
            paths.append(path.split(" ")[0])
        ext_drives = []
        count = 0
        for drive_loc in drives_text_file:
            full_drive_path = drives_text_file[count].replace("\n", "")
            drive_title = drive_loc.replace("\n", "")
            commands = ["du", "-d1", "-h", drive_title if " --exclude" not in drive_title else drive_title.split(" --exclude=")[0]]
            if " --exclude=" in drive_title:
                full_drive_path = full_drive_path.split(" --exclude=")[0]
                exclude_paths = drive_title.split(" --exclude=")[1:]
                drive_title = drive_title.split(" --exclude=")[0]
                for path in exclude_paths:
                    commands.append(f"--exclude={path}")
            drive_data = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
            if "/".join(drive_loc.split(" ")[0].split("/")[:-1]) not in paths:
                capacity = subprocess.run(["df", "-h", "--output=size", drive_title], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip() + "B"
            else:
                capacity = ""
            div_start = '<div class=\"driveDiv innerContainer\" id=\"' + full_drive_path + '\">'
            ext_drives.append(div_start)
            ext_drives.append("<h3 class=\"driveHeading\">" + full_drive_path + capacity.replace("Size\n", "<br>Capacity") + "</h3>")
            drive = drive_data.split("\n")
            for drive in drive:
                used, name = drive.split("\t")
                if name + "\n" in drives_text_file and name != full_drive_path:
                    pass
                else:
                    if name == full_drive_path:
                        name = "Total"
                    ext_drives.append('<h4 class=\"driveTitle\">' + name.replace(full_drive_path, "") + '</h4>')
                    ext_drives.append(f"<p class=\"driveData\">{used}B used</p>")
            ext_drives.append("</div>")
            count = count + 1
    return " ".join(ext_drives)

@app.route('/save_color', methods=['POST'])
def save_color():
    data_div_color = request.json['data_div_color']
    config["SimplePiStats"]["bg_color"]='"' + data_div_color + '"'
    with open("config.ini", "w") as config_file:
        config.write(config_file)
    return '', 204

@app.route('/edit_config', methods=['POST'])
def edit_config():
    config_data = request.json['config_data']
    changed = False
    for key, value in config_data:
        key = key.replace("Config", "")
        if key == "bg_color" or key == "address" or key == "custom_css":
            value = '"' + value + '"'
        if value != config.get("SimplePiStats", key):
            changed = True
            config.set("SimplePiStats", key, value)
    if changed == True:
        with open(r"config.ini", "w") as config_file:
            config.write(config_file)
        changed = False
    return '', 204

@app.route('/button_action', methods=['POST'])
def button_action():
    button_action_ = str(request.json['button_id']).split("/")
    subprocess.run(["sudo", "systemctl", button_action_[0], button_action_[1]])
    time.sleep(0.5)
    status_check = subprocess.run(["systemctl", "is-active", button_action_[1]], stdout=subprocess.PIPE, text=True).stdout.strip()
    if status_check == "active":
        service_boot_time = subprocess.run(["systemctl", "show", "--property=ActiveEnterTimestamp", button_action_[1]], stdout=subprocess.PIPE, text=True).stdout.strip().removeprefix("ActiveEnterTimestamp=")
        status_message = f" 🟢 "
        reboot_duration = datetime.datetime.now().replace(tzinfo=pytz.utc, microsecond=0) - dateparser.parse(service_boot_time).replace(tzinfo=pytz.utc, microsecond=0)
        if reboot_duration.seconds < 60:
            reboot_duration = "less than a minute ago"
        else:
            reboot_duration = humanize.naturaltime(reboot_duration, minimum_unit='seconds')
        service_reboot = f"Service last restarted {reboot_duration} "
    else:
        status_message = " 🔴 "
        service_reboot = "Service last restarted N/A"
    return jsonify({"service": button_action_[1], "status": status_message, "serviceReboot": service_reboot})


@app.route("/update_settings", methods=["POST"])
def update_settings():
    file_contents = {}
    for value in checkboxes:
        file_contents[value] = "checked" if value in request.form else "unchecked"
    file = open(r".checkbox_states.json", 'w')
    file.write(json.dumps(file_contents, indent=len(file_contents)))
    file.close()
    return '', 204

@app.route('/run_command', methods=['POST'])
def run_command():
    command_text = request.get_json().get("command_text", "").split(" ")
    try:
        return subprocess.run(command_text, cwd="/".join(command_text[1].split("/")[:-1]), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
    except:
        return subprocess.run(command_text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()

def reboot():
    subprocess.run(["sudo", "reboot"], stdout=subprocess.PIPE, text=True).stdout.strip()

@app.route('/restart_system', methods=['POST'])
def restart_system():
    threading.Thread(target=reboot).start()
    return jsonify({"status": "System restarting..."})

if listen_address == "0.0.0.0":
    ip_addresses = subprocess.check_output(['hostname', '-I']).decode().strip().split(" ")
    print(f"\033[0;32mSimplePiStats is currently running on http://{ip_addresses.pop(0)}:{port}")
    if len(ip_addresses) >= 1:
        print(f"it can also be reached on http://{ip_addresses.pop(0)}:{port}")
else:
    print(f"\033[0;32mSimplePiStats is currently running on http://{listen_address}:{port}")
print("\033[0m")
sys.stdout.flush()

waitress.serve(app, host=listen_address, port=port)
