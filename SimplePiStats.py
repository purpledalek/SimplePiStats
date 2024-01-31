import subprocess
import time
import datetime
from flask import Flask, render_template, request, jsonify, session
import os
import waitress
import socket

app = Flask(__name__)
port = 5555


def service_check(service_):
    if "/" in service_:
        service = service_.split("/")[0]
    else:
        service = service_
    output = f"<div class=\"service\" id=\"{service}\"> <div class=\"text\">"
    status_check = subprocess.run(["systemctl", "is-active", service], stdout=subprocess.PIPE, text=True).stdout.strip()
    desc = subprocess.run(["systemctl", "show", "-p", "Description", service], stdout=subprocess.PIPE, text=True).stdout.replace("Description=", "")
    for file in os.listdir(r"static/services/icons"):
        if service.lower() == file.split(".")[0].lower():
            output += f"<img class=\"service_icon\" src=\"static/services/icons/{file}\">"
        else:
            pass
    if "-" in desc:
        output += "<p class=\"service_stats\">" + service.title() + "</p>"
    else:
        output += "<p class=\"service_stats\">" + desc + "</p>"
    if status_check == "active":
        output += "<p id=\"status\"> 🟢 </p>"
    else:
        output += "<p id=\"status\"> 🔴 </p>"
    output += "</div> <div class=\"buttons\">"
    output += f"<button onclick=\"handle_button_action('start/{service}')\" class=\"button\"id=\"start\">Start</button>"
    output += f"<button onclick=\"handle_button_action('stop/{service}')\" class=\"button\"id=\"stop\">Stop</button>"
    output += f"<button onclick=\"handle_button_action('restart/{service}')\" class=\"button\" id=\"restart\">Restart</button>"
    if "/" in service_:
        port = service_.split("/")[1]
        output += (f"<a id=\"{service_}\"><button class=\"button\" style=\"margin: 20px; float: right;\">Link to local {service_.split('/')[0].replace('_', ' ').title()} page</button></a>\n<script>document.getElementById(\"{service_}\").href = \"http://\" + window.location.hostname + \":{port}\"</script>")
    output += "</div></div>"
    return output


if not os.path.exists(r"./static/services/service_names.txt"):
    with open(r"./static/services/service_names.txt", "w"):
        pass

if not os.path.exists(r"./static/checkbox_states.txt"):
    with open(r"./static/checkbox_states.txt", 'w') as file:
        file.write("unchecked\nunchecked\nunchecked")
        file.close()


@app.route('/')
def index():
    # get output
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

    with open(r"./static/checkbox_states.txt", "r") as file:
        file_contents = file.read().split("\n")
        file.close()

    # 0 - 40 :]
    # 41 - 74 :|
    # 75 - 100 >:[

    up_since = subprocess.Popen(["uptime", "--since"], stdout=subprocess.PIPE, text=True)
    last_boot = up_since.communicate()[0].strip().replace("\n", "")
    boot_time = str(datetime.datetime.strptime(last_boot, "%Y-%m-%d %H:%M:%S"))

    services = []

    __services__ = open(r"static/services/service_names.txt", "r").read().split("\n")
    if __services__ == [""]:
        services = ["<p>No services found. Please add service names to service_names.txt to use this feature, or see the <a href=\"https://github.com/purpledalek/SimplePiStats/blob/main/readme.md\" target=\"_blank\">readme</a> for more info.</p>"]
    else:
        for service in __services__:
            if service.startswith("[") and service.endswith("]"):
                formatted = service.strip("[" "]").split(", ")
                services_l = formatted[1:]
                group_title = "<b>" + formatted.pop(0).title()
                for file in os.listdir(r"static/services/icons"):
                    if group_title.lower() == file.split(".")[0].lower():
                        group_title = f"<img class=\"group_title_icon\" src=\"static/services/icons/{file}\">" + group_title
                    else:
                        pass
                services.append("<div style=\"height: 35px\"></div>" + group_title + "</b>")
                for serv in services_l:
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
            Fahrenheit = temp * 9 / 5 + 32
    if Celsius <= 50:
        temp = "1"
    elif Celsius <= 70:
        temp = "2"
    else:
        temp = "3"

    return render_template("SimplePiStats.html", cpu_status=cpu_status, cpu_status_numbers=str(cpu) + "%", boot_time=boot_time, temp=temp, Celsius=str(Celsius) + "°C", Fahrenheit=str(Fahrenheit) + "°F", services=" <br> ".join(services), numbers_checkbox_state=file_contents[0], services_checkbox_state=file_contents[1])


@app.route('/button_action', methods=['POST'])
def button_action():
    button_action_ = str(request.json['button_id']).split("/")
    subprocess.run(["sudo", "systemctl", button_action_[0], button_action_[1]])
    time.sleep(0.5)
    status_check = subprocess.run(["systemctl", "is-active", button_action_[1]], stdout=subprocess.PIPE, text=True).stdout.strip()
    if status_check == "active":
        status_message = " 🟢 "
    else:
        status_message = " 🔴 "
    return jsonify({"service": button_action_[1], "status": status_message})


@app.route("/update_settings", methods=["POST"])
def update_settings():
    if request.form.get("numbers_toggle"):
        numbers_state = "checked"
    else:
        numbers_state = "unchecked"

    if request.form.get("services_toggle"):
        services_state = "checked"
    else:
        services_state = "unchecked"

    if request.form.get("c_f_toggle"):
        c_f_toggle = "checked"
    else:
        c_f_toggle = "unchecked"
    file = open(r"./static/checkbox_states.txt", 'w')
    file.write(numbers_state + "\n" + services_state + "\n" + c_f_toggle)
    file.close()
    return '', 204

ip_addresses = subprocess.check_output(['hostname', '-I']).decode().strip().split(" ")
del ip_addresses[-1]
print(f"SimplePiStats is currently running on http://{ip_addresses.pop(0)}:{port}")
if len(ip_addresses) >= 1 :
    for item in ip_addresses:
        ip_addresses.insert(ip_addresses.index(item)+1, f"http://{item}:{port}")
        ip_addresses.remove(item)
    print(f"it can also be reached on {', '.join(ip_addresses)}")
waitress.serve(app, host="0.0.0.0", port=port)
