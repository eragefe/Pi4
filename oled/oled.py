#! /usr/bin/env python

import time
import subprocess
from socket import error as socket_error
import os.path
import RPi.GPIO as GPIO

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
from mpd import MPDClient, MPDError, CommandError, ConnectionError

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

serial = i2c(port=1, address=0x3C)
device = sh1106(serial, rotate=0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)
state17 = GPIO.input(17)

class MPDConnect(object):
    def __init__(self, host='localhost', port=6600):
        self._mpd_client = MPDClient()
        self._mpd_client.timeout = 10
        self._mpd_connected = False

        self._host = host
        self._port = port

    def connect(self):
        if not self._mpd_connected:
            try:
                self._mpd_client.ping()
            except(socket_error, ConnectionError):
                try:
                    self._mpd_client.connect(self._host, self._port)
                    self._mpd_connected = True
                except(socket_error, ConnectionError, CommandError):
                    self._mpd_connected = False

    def disconnect(self):
        self._mpd_client.close()
        self._mpd_client.disconnect()

    def _play_pause(self):
        self._mpd_client.pause()
        #return False

    def _next_track(self):
        self._mpd_client.next()
        #return False

    def _prev_track(self):
        self._mpd_client.previous()
        #return False

    def spdif(self):
        self._mpd_client.clear()
        #os.system("aplay /root/spdif176400.wav")
        self._mpd_client.add("alsa://hw:0,1")
        self._mpd_client.play()
        self._mpd_client.repeat(0)
        #return False

    def fetch(self):
        song_info = self._mpd_client.currentsong()

        if 'file' in song_info:
            file = song_info['file']
        else:
            file = ''
        if 'artist' in song_info:
            artist = song_info['artist']
        else:
            artist = ''
        if 'title' in song_info:
            title = song_info['title']
        else:
            title = ''

        song_stats = self._mpd_client.status()
        state = song_stats['state']

        if 'elapsed' in song_stats:
            elapsed = song_stats['elapsed']
            m,s = divmod(float(elapsed), 60)
            h,m = divmod(m, 60)
            eltime = "%02d:%02d" % (m, s)
        else:
            eltime ="00:00"

        if 'audio' in song_stats:
            bit = song_stats['audio'].split(':')[1]
            frequency = song_stats['audio'].split(':')[0]
            z, f = divmod( int(frequency), 1000 )
            if ( f == 0 ):
                frequency = str(z)
            else:
                frequency = str( float(frequency) / 1000 )
            bitrate = song_stats['bitrate']

            audio_info =  bit + ":" + frequency
        else:
            audio_info = ""

        vol = song_stats['volume']
        rep = song_stats['repeat']
        ran = song_stats['random']

        return({'file':file, 'state':state, 'artist':artist, 'title':title, 'eltime':eltime, 'volume':int(vol), 'random':int(ran), 'repeat':int(rep), 'audio_info':audio_info})

font = ImageFont.truetype('/root/pi3/oled/Verdana.ttf', 47)
font2 = ImageFont.truetype('/root/pi3/oled/Verdana.ttf', 13)
font3 = ImageFont.truetype('/root/pi3/oled/Verdana.ttf', 23)
font4 = ImageFont.truetype('/root/pi3/oled/Arial-Bold.ttf', 20)

with canvas(device) as draw:
    device.contrast(0)
    img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gdis3.png'))
    logo = Image.open(img_path)
    draw.bitmap((25, 0), logo, fill="white")
for level in range(0, 255, 3):
    device.contrast(level)
    time.sleep(0.1)

with canvas(device) as draw:
    eth = os.popen('ip addr show eth0 | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip()
    wlan = os.popen('ip addr show wlan0 | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip()
    draw.text((5, 0), "Ethernet",  font=font2, fill=255)
    draw.text((5, 15), str(eth),  font=font2, fill=255)
    draw.text((5, 35), "Wireless",  font=font2, fill=255)
    draw.text((5, 50), str(wlan),  font=font2, fill=255)
time.sleep(8)

def main():
  client = MPDConnect()
  client.connect()
#  client.spdif()

  while True:

    info = client.fetch()
    file = info['file']
    state = info['state']
    vol = info['volume']
    rep = info['repeat']
    ran = info['random']
    eltime = info['eltime']
    artist = info['artist']
    title = info['title']
    audio = info['audio_info']
    
    with open("/boot/input") as file:
        contents = file.read()
    if "streamer" in contents:
        client.spdif()
        
    if file == 'alsa://hw:0,1':
      with canvas(device) as draw:

       if vol>0 and vol<100:
         draw.text((35,0), "coaxial", font=font2, fill=255)
         draw.text((0,13),str(vol), font=font, fill=255)
         draw.text((70,40),"SPDIF", font=font2, fill=255)
       if vol==100:
         draw.text((35,0), "coaxial", font=font2, fill=255)
         draw.text((0,13),"--", font=font, fill=255)
         draw.text((70,40),"SPDIF", font=font2, fill=255)

    if state == 'stop' and file != 'alsa://hw:0,1':
      with canvas(device) as draw:

       if vol>0 and vol<100:
         draw.text((0,13),str(vol), font=font, fill=255)
       if vol==100:
         draw.text((0,13),"--", font=font, fill=255)

    if state == 'play' and file != 'alsa://hw:0,1':
      with canvas(device) as draw:

       if vol>0 and vol<100:
         draw.text((35,0), audio, font=font2, fill=255)
         draw.text((0,13),str(vol), font=font, fill=255)
         draw.text((80,50),str(eltime), font=font2, fill=255)
         draw.text((87,20),">>", font=font4, fill=255)
       if vol==100:
         draw.text((35,0), audio, font=font2, fill=255)
         draw.text((0,13),"--", font=font, fill=255)
         draw.text((80,50),str(eltime), font=font2, fill=255)
         draw.text((87,20),">>", font=font4, fill=255)

    if state == 'pause' and file != 'alsa://hw:0,1':
      with canvas(device) as draw:
       if vol>0 and vol<100:

         draw.text((35,0), audio, font=font2, fill=255)
         draw.text((0,13),str(vol), font=font, fill=255)
         draw.text((80,50),str(eltime), font=font2, fill=255)
         draw.text((87,20)," ||", font=font4, fill=255)
       if vol==100:
         draw.text((35,0), audio, font=font2, fill=255)
         draw.text((0,13),"--", font=font, fill=255)
         draw.text((80,50),str(eltime), font=font2, fill=255)
         draw.text((87,20)," ||", font=font4, fill=255)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
