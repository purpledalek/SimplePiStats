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

# get images for service icons; add line denoting the ip of remote docker container
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
        "services": ["SimplePiStats"],
        "custom_css": '""'
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)

if not os.path.exists("static/custom_js"):
    os.makedirs("static/custom_js", exist_ok=True)

if not os.path.exists("docker_ports.json"):
    with open("docker_ports.json", "w") as file:
        file.write("{}")

if not os.path.exists("remote_ips.txt"):
    with open("remote_ips.txt", "w"):
        pass
    

# Set up listen address and port numbers
listen_address = conf_get("address")
port = conf_get("port")

def pre_append(command, lis):
    if type(command) == tuple:
        for i in reversed(command):
            lis.insert(0, i)
    else:
        lis.insert(0, command)
    return lis


# todo: fix remote docker error
def check_docker(remote: bool = False, ip: str = None):
    output = ""
    if remote == True:
        docker_ps = subprocess.run(pre_append(("ssh", ip), ["sudo", "docker", "ps", "--format", "json"]), stdout=subprocess.PIPE, text=True).stdout.strip().split("\n")
    else:
        docker_ps = subprocess.run(["sudo", "docker", "ps", "--format", '{"Names":"{{.Names}}","Status":"{{.Status}}","Ports":"{{.Ports}}"}'], stdout=subprocess.PIPE, text=True).stdout.strip().split("\n")
    if docker_ps == []:
        output = "<div class='innerContainer'><div class='text'>No Docker containers found. Are you sure any are running? If you don't want to see this section you can hide it using settings</div><div>"
    else:
        changes = False
        with open("docker_ports.json", "r") as file:
            docker_ports = json.loads(file.read())
        for i in docker_ps:
            container_data = json.loads(i)
            name = container_data.get("Names")
            if name not in docker_ports.keys():
                changes = True
                docker_ports[name] = ""
            output += f"<div id='{name}' class='innerContainer'><div class='text'>"
            docker_port = docker_ports.get(name)
            if docker_port != "":
                output += f"<a class=\"container_stats\" id={docker_port} target=\"_blank\">{name}</a>"
            else:
                output += f"<p class=\"container_stats\" id={name}>{name}</p>"
            if remote == True:
                output += f"<p class='container_stats'> – on {ip}</p>"
            output += "</a>" if remote == True else "</p>"
            status = container_data.get("Status").replace("Up", "Container last restarted") + " ago"
            image = add_image(name, True, status)
            output += image if image != None else ""
            if status.startswith("Exited"):
                status_icon = "<p id=\"status\"> 🔴 </p>"
                status = "Container last restarted N/A"
            else:
                status_icon = "<p id=\"status\"> 🟢 </p>"
            output += f"{status_icon}</div>"
            output += f"<p id='containerReboot'>{status}</p>"
            output += f"<div class='buttons'><button onclick='handle_button_action(\"stop/{name}\", \"docker\")'>Stop</button><button onclick='handle_button_action(\"restart/{name}\", \"docker\")'>Restart</button></div>"
            output += "</div>"
        if changes == True:
            with open("docker_ports.json", "w") as file:
                file.write(json.dumps(docker_ports, indent=len(docker_ports)))
    return output

def add_image(application:str, is_docker: bool, status_check):
    for file in os.listdir("service_icons"):
        if application.lower() == file.split(".")[0].lower():
            if is_docker == False:
                if status_check == "active":
                    return f"<img class=\"service_icon\" src=\"service_icons/{file}\">"
                else:
                    return f"<img class=\"service_icon bw\" src=\"service_icons/{file}\">"
            else:
                if status_check.startswith("Container last restarted"):
                    return f"<img class=\"service_icon\" src=\"service_icons/{file}\">"
                else:
                    return f"<img class=\"service_icon bw\" src=\"service_icons/{file}\">"
def service_check(service_):
    output = ""
    stop = True
    restart = True
    if "--no_stop" in service_.lower():
        stop = False
        service_ = service_.replace(" --no_stop", "")
    if "--no_restart" in service_.lower():
        restart = False
        service_ = service_.replace(" --no_restart", "")
    if "/" in service_:
        service = service_.split("/")[0]
        port = service_.split("/")[1].split(" ")[0]
        output_template = f"<a class=\"service_stats\" id=\"port\" target=\"_blank\">desc</a><p class=\"service_stats\">remote</p>"
    else:
        service, port = service_, ""
        output_template = "<p class=\"service_stats\">desc remote</p>"
    if "-r" in service_:
        remote_host = re.search(r".* -r (.*[0-9.])", service_)
        remote =  f" – on {remote_host.group(1)}"
        systemctl = "systemctl", "--host", remote_host.group(1)
        desc = subprocess.run(pre_append(systemctl, ["show", "-p", "Description", service]), stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
    else:
        remote = ""
        systemctl = "systemctl"
        desc = subprocess.run(pre_append(systemctl, ["show", "-p", "Description", service]), stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
    status_check = subprocess.run(pre_append(systemctl, ["is-active", service]), stdout=subprocess.PIPE, text=True).stdout.strip()
    output += f"<div class=\"service innerContainer\" id=\"{service}\"> <div class=\"text\">"
    if "-" in desc:
        desc = service.title()
    if service == "SimplePiStats":
        if status_check == "active":
            output += "<img class=\"service_icon\" src=\"static/favicon.png\">"
        else:
            output += "<img class=\"service_icon bw\" src=\"static/favicon.png\">"
    else:
        image = add_image(service, False, status_check)
        output += image if image != None else ""

    output += output_template.replace("desc", desc).replace("port", port).replace("remote", remote)
    if status_check == "active":
        service_boot_time = subprocess.run(pre_append(systemctl, ["show", "--property=ActiveEnterTimestamp", service]), stdout=subprocess.PIPE, text=True).stdout.strip().removeprefix("ActiveEnterTimestamp=")
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
            if "-r" in service_:
                output += f"<button onclick=\"handle_button_action('stop/{service}', 'systemd --remote/{remote_host.group(1)}' )\" class=\"button\"id=\"stop\">Stop</button>"
            else:
                output += f"<button onclick=\"handle_button_action('stop/{service}', 'systemd')\" class=\"button\"id=\"stop\">Stop</button>"
        if restart == True:
            if "-r" in service_:
                output += f"<button onclick=\"restart_confirm('{service}'); handle_button_action('restart/{service}', 'systemd --remote/{remote_host.group(1)}')\"class=\"button\" id=\"restart\">Restart</button>"
            else:
                output += f"<button onclick=\"restart_confirm('{service}'); handle_button_action('restart/{service}', 'systemd')\"class=\"button\" id=\"restart\">Restart</button>"
        output += "</div>"
    output += "</div>"
    return output


@app.route("/speed_test", methods=['POST'])
def speed_test():
    response = subprocess.Popen(['/usr/bin/speedtest'], shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
    ping = re.search(': (.*?ms)', response, re.MULTILINE)
    download = re.search('Download:\s+(.*?s)', response, re.MULTILINE)
    upload = re.search('Upload:\s+(.*?s)', response, re.MULTILINE)
    location = re.search('Hosted by .*\[(.*)]', response, re.MULTILINE)
    try:
        ping = ping.group(1)
    except:
        ping = re.search('Latency:\s+(.*?s)', response, re.MULTILINE)
        ping = ping.group(1)
    download = download.group(1)
    upload = upload.group(1)
    location = location.group(1)

    return jsonify({"ping": ping, "download": download, "upload": upload, "location": location})

checkboxes = ["serverTimeToggle", "speedTestToggle", "numbersToggle", "diskToggle", "servicesToggle", "commandsToggle", "dockerToggle", "cfToggle", "fontToggle", "mysteryToggle"]

if not os.path.exists(r".checkbox_states.json"):
    with open(r".checkbox_states.json", 'w') as file:
        init_dict = {}
        for box in checkboxes:
            init_dict[box] = "unchecked"
        file.write(json.dumps(init_dict, indent=len(init_dict)))
else:
    new_install = False
    with open(r".checkbox_states.json", 'r') as file:
        states = json.load(file)
        for box in checkboxes:
            if box not in states.keys():
                new_install = True
                states[box] = "unchecked"
    if new_install == True:
        with open(r".checkbox_states.json", 'w') as file:
            file.write(json.dumps(states, indent=len(states)))

def create_command_buttons():
    buttons = []
    commands = conf_get("commands")
    if commands == []:
        buttons.append("<p>No commands found. Please add command names in settings > Edit config to use this feature, or you can hide it using settings. See the <a href=\"https://github.com/purpledalek/SimplePiStats/blob/main/readme.md#editing-config-file\" target=\"_blank\">readme</a> for more info.</p>")
    else:
        for line in commands:
            spl = line.split(":")
            buttons.append(f"<button onclick='runCommand(\"{spl[1].strip()}\")'>{spl[0].strip()}</button>")
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
                services.append("<div class=\"innerContainer service\">")
                group_title = service.pop(0).title()
                service_icons = [icon.split(".")[0] for icon in os.listdir("service_icons")]
                if group_title.lower() in service_icons:
                    for file in os.listdir("service_icons"):
                        if file.lower().split(".")[0] == group_title.lower():
                            services.append(f"<img class=\"group_title_icon\" src=\"service_icons/{file}\"><h3 style=\"vertical-align: middle; display: inline;\">" + group_title + "</h3>")
                else:
                    services.append("<h3 style=\"vertical-align: middle; display: inline;\">" + group_title + "</h3>")
                for serv in service:
                    services.append(service_check(serv))
                    if service.index(serv) == len(service) - 1:
                        services.append("</div>")
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
    docker_containers = check_docker()
    with open("remote_ips.txt", "r") as file:
        file_content = file.readlines()
        if file_content != []:
            for line in file_content:
                try:
                    docker_containers += check_docker(True, line.replace("\n", ""))
                except:
                    pass
    output = ""
    custom_js = []
    for filename in os.listdir("static/custom_js"):
        with open(f"static/custom_js/{filename}") as file:
            custom_js.append(file.read())
    return render_template("SimplePiStats.html", hostname=hostname, cpu_status=cpu_status, cpu_status_numbers=str(cpu) + "%", boot_time=boot_time, temp=temp, Celsius=str(Celsius) + "°C", Fahrenheit=str(Fahrenheit) + "°F", services=" ".join(services), time_checkbox_state=file_contents.get(checkboxes[0]), speed_checkbox_state=file_contents.get(checkboxes[1]), numbers_checkbox_state=file_contents.get(checkboxes[2]), disk_checkbox_state=file_contents.get(checkboxes[3]), services_checkbox_state=file_contents.get(checkboxes[4]), commands_checkbox_state=file_contents.get(checkboxes[5]), fahrenheit_checkbox_state=file_contents.get(checkboxes[6]), font_checkbox_state=file_contents.get(checkboxes[7]), mystery_checkbox_state=file_contents.get(checkboxes[8]), command_buttons=" ".join(command_buttons), server_time=server_time, div_color=conf_get("bg_color"), port=port, commandsConfig=conf_get("commands"), drivesConfig=conf_get("drives"), servicesConfig=conf_get("services"), addressConfig=listen_address, custom_css=conf_get("custom_css"), docker_containers=docker_containers, custom_js="\n\n".join(custom_js))

@app.route('/get_docker_config', methods=['POST'])
def get_docker_config():
    with open("docker_ports.json", "r") as file:
        json_content = file.read()
    docker_ports_config = []
    as_json = json.loads(json_content)
    for i in as_json.items():
        docker_ports_config.append({"name":i[0], "port":i[1]})
    return jsonify({"docker_config": docker_ports_config})

@app.route('/disk_usage', methods=['POST'])
def disk_usage():
    drives_text_file = conf_get("drives")
    no_drives = False
    if drives_text_file == []:
        no_drives = True
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
    return jsonify({"driveList": " ".join(ext_drives), "noDrives": no_drives})

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
    file_path = request.json['file_path']
    new_data = {}
    for key, value in config_data:
        key = key.replace("Config", "")
        if key == "bg_color" or key == "address" or key == "custom_css":
            value = '"' + value + '"'
        if file_path.endswith(".ini"):
            type_ = "ini"
            if value != config.get("SimplePiStats", key):
                config.set("SimplePiStats", key, value)
        elif file_path.endswith(".json"):
            type_ = "json"
            print(key, value)
            new_data[key] = value
    print(new_data)
    if type_ == "ini":
        with open(file_path, "w") as file:
            config.write(file)
    if type_ == "json":
        with open(file_path, "w") as file:
            json_d = json.dumps(new_data, indent=len(new_data))
            file.write(json_d)
    return '', 204

@app.route('/systemd_button_action', methods=['POST'])
def systemd_button_action():
    button_action_ = str(request.json['button_id']).split("/")
    command = str(request.json['type']).split("/")[0]
    if command == "systemd --remote":
        ip = str(request.json['ip'])
        subprocess.run(["ssh", ip, "sudo", "systemctl", button_action_[0], button_action_[1]])
    else:
        subprocess.run(["sudo", "systemctl", button_action_[0], button_action_[1]])
    time.sleep(3)
    if command == "systemd":
        systemctl = "systemctl"
    elif command == "systemd --remote":
        systemctl = "systemctl", "--host", ip
    status_check = subprocess.run(pre_append(systemctl, ["is-active", button_action_[1]]), stdout=subprocess.PIPE, text=True).stdout.strip()
    if status_check == "active":
        service_boot_time = subprocess.run(pre_append(systemctl, ["show", "--property=ActiveEnterTimestamp", button_action_[1]]), stdout=subprocess.PIPE, text=True).stdout.strip().removeprefix("ActiveEnterTimestamp=")
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

@app.route('/docker_button_action', methods=['POST'])
def docker_button_action():
    button_action_ = str(request.json['button_id']).split("/")
    name = button_action_[1]
    subprocess.run(["sudo", "docker", button_action_[0], name], stdout=subprocess.DEVNULL)
    docker_ps = subprocess.run(["sudo", "docker", "ps", "-a", "--format", "{'Names':'{{.Names}}','Status':'{{.Status}}'}"], stdout=subprocess.PIPE, text=True).stdout.strip()
    for i in docker_ps.split("\n"):
        container_data = json.loads(i)
        if name == container_data.get("Names"):
            status = container_data.get("Status")
            if status.startswith("Exited"):
                status_message = " 🔴 "
                status = "Container last restarted N/A"
            else:
                status_message = " 🟢 "
                status = status.replace("Up", "Container last restarted") + " ago"
            
    return jsonify({"container": button_action_[1], "status": status_message, "containerReboot": status})


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
    for address in ip_addresses:
        search = re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", address)
        if search:
            print(f"it can also be reached on http://{address}:{port}")
else:
    print(f"\033[0;32mSimplePiStats is currently running on http://{listen_address}:{port}")
print("\033[0m")
sys.stdout.flush()

waitress.serve(app, host=listen_address, port=port)
