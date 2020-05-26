from flask import Flask, render_template, request
import subprocess
import os
import time
import RPi.GPIO as GPIO

app = Flask(__name__)
app.debug = True

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)

@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('app2.html')

@app.route('/wifi')
def wifi():
    wifi_ap_array = scan_wifi_networks()

    return render_template('wifi.html', wifi_ap_array = wifi_ap_array)

@app.route('/manual_ssid_entry')
def manual_ssid_entry():
    return render_template('manual_ssid_entry.html')

@app.route('/tidal')
def tidal():
    return render_template('tidal.html')

@app.route('/tidal_save_credentials', methods = ['GET', 'POST'])
def tidal_save_credentials():
    ssid = request.form['ssid']
    wifi_key = request.form['wifi_key']
    create_upmpdcli(ssid, wifi_key)
    os.system('mv upmpdcli.tmp /etc/upmpdcli.conf')
    os.system('cp /etc/upmpdcli.conf /etc/upmpdcli.conf')
    time.sleep(1)
    os.system('service upmpdcli restart')
    return render_template('save_credentials.html')

@app.route('/save_credentials', methods = ['GET', 'POST'])
def save_credentials():
    ssid = request.form['ssid']
    wifi_key = request.form['wifi_key']
    create_wpa_supplicant(ssid, wifi_key)
    os.system('mv wpa_supplicant.conf.tmp /etc/wpa_supplicant/wpa_supplicant.conf')
    os.system('cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf')
    time.sleep(1)
    os.system('/etc/init.d/networking restart')
    os.system('wpa_cli -i wlan0 reconfigure')
    return render_template('save_credentials.html')

@app.route('/dispon', methods = ['GET', 'POST'])
def dispon():
    GPIO.output(22, GPIO.HIGH)
    return render_template('app2.html')

@app.route('/dispoff', methods = ['GET', 'POST'])
def dispoff():
    GPIO.output(22, GPIO.LOW)
    return render_template('app2.html')

@app.route('/reboot', methods = ['GET', 'POST'])
def reboot():
    os.system('mpc volume +1')
    return render_template('app2.html')

@app.route('/poweroff', methods = ['GET', 'POST'])
def poweroff():
    os.system('mpc volume -1')
    return render_template('app2.html')

@app.route('/squeeze', methods = ['GET', 'POST'])
def squeeze():
    os.system('mpc clear')
    os.system('mpc add alsa://hw:0,1')
    os.system('mpc play')
    GPIO.output(17, GPIO.HIGH)
    return render_template('app_sq2.html')

@app.route('/upnp', methods = ['GET', 'POST'])
def upnp():
    os.system('mpc clear')
    os.system('mpc add alsa://hw:0,1')
    os.system('mpc play')
    GPIO.output(17, GPIO.LOW)
    return render_template('app_up2.html')

######## FUNCTIONS ##########

def scan_wifi_networks():
    iwlist_raw = subprocess.Popen(['iwlist', 'scan'], stdout=subprocess.PIPE)
    ap_list, err = iwlist_raw.communicate()
    ap_array = []

    for line in ap_list.decode('utf-8').rsplit('\n'):
        if 'ESSID' in line:
            ap_ssid = line[27:-1]
            if ap_ssid != '':
                ap_array.append(ap_ssid)

    return ap_array

def create_wpa_supplicant(ssid, wifi_key):

    temp_conf_file = open('wpa_supplicant.conf.tmp', 'w')

    temp_conf_file.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
    temp_conf_file.write('update_config=1\n')
    temp_conf_file.write('\n')
    temp_conf_file.write('network={\n')
    temp_conf_file.write('	ssid="' + ssid + '"\n')
    if wifi_key == '':
        temp_conf_file.write('	key_mgmt=NONE\n')
    else:
        temp_conf_file.write('	psk="' + wifi_key + '"\n')
    temp_conf_file.write('	}')
    temp_conf_file.close

def create_upmpdcli(ssid, wifi_key):

    temp_conf_file = open('upmpdcli.tmp', 'w')

    temp_conf_file.write('uprclautostart = 1\n')
    temp_conf_file.write('friendlyname = GDis-NGNP\n')
    temp_conf_file.write('iconpath = /boot/gdis_upnp.png\n')
    temp_conf_file.write('msfriendlyname = GDis-Tidal-server\n')
    temp_conf_file.write('tidaluser = ' + ssid + '\n')
    temp_conf_file.write('tidalpass = ' + wifi_key + '\n')
    temp_conf_file.write('tidalquality = lossless\n')
    temp_conf_file.close

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80)
