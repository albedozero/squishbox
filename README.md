This version of the squishbox software is no longer maintained. The latest version is at https://github.com/GeekFunkLabs/squishbox

# SquishBox
Python fluidsynth wrapper/interface for a stompbox sound module powered by [Fluidsynth](http://www.fluidsynth.org) (because that's what happens if you stomp on a box full of fluid).

![SquishBox image](/images/squishbox_relief1.jpg)

## Explanation
This project provides the software front-end for a soundfont-playing sound module consisting of a small linux SBC (e.g. a Raspberry Pi) connected to an LCD, a couple of momentary stompswitches for user input, and an external sound card for hi-def audio output. More details of the project are described [Hackaday.io](https://hackaday.io/project/9097-jampi). This version assumes the following components:

- Raspberry Pi 3 SBC
- PCM5102 DAC
- 16x2 Character LCD
- 2 momentary stompswitches
- 2 1/4" TRS jacks

![SquishBox schematic](/images/hat_wiring.jpg)

The `stompboxpi.py` python script provides library functions to initialize the LCD, poll the buttons, and display menus and allow crude text entry, while `squishbox.py` is the interface, calling and interacting with Fluidsynth using [PyFluidSynth](https://github.com/nwhitehead/pyfluidsynth).

## Installation
Full images can be found in the [releases](https://github.com/albedozero/squishbox/releases) section, and can be written to a micro SD card (4GB+) using the standard methods.

## Manual Installation
Files should be copied to the *pi* user's home directory `/home/pi`). [FluidSynth](http://www.fluidsynth.org) must be installed. On Raspbian the simplest method is to use aptitude from the command line:
```
sudo apt-get install fluidsynth
```
Newer versions of Fluidsynth can be built from source and used by modifying `fluidsynth.py`. For example, fluidsynth-2_0_3.py has been modified to point to the shared object library compiled into `fluidsynth-2.0.3/build/src/`.

Install some needed python modules. You might need to do a `sudo apt-get install python3-pip` first.
```
sudo pip install RPi.GPIO pyyaml
```
This setup also uses the deprecated (but still fine) [Adafruit Python CharLCD](https://github.com/adafruit/Adafruit_Python_CharLCD) library. Clone it wherever on your pi, then run
```
sudo python3 setup.py install
```
To activate the sound card, create the file `/etc/asound.conf` and enter the following:
```
pcm.!default  {
 type hw card 0
}
ctl.!default {
 type hw card 0
}
```
Next, edit `/boot/config.txt`, add the following line:
```
dtoverlay=hifiberry-dac
```
and make sure this line is commented:
```
#dtparam=audio=on
```
If you encounter sound issues, check the full instructions for the [Pimoroni DAC](https://learn.pimoroni.com/tutorial/phat/raspberry-pi-phat-dac-install).

The interface works best when installed as a service, so that it runs at startup. Create a `squishbox.service` file in `/etc/systemd/system/`:
```
[Unit]
Description=SquishBox
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/pi/squishbox.py
User=root
WorkingDirectory=/home/pi
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
and then enter `sudo systemctl enable squishbox`.

### Web Configuration Panel

The index.php file contains a web configuration panel that makes it easy to edit the configuration and patches of the Squishbox remotely, but requires a lot of setup to work. First, install the nginx web server with php:
```
sudo apt-get install nginx php-fpm
```
Next, in the file `/etc/nginx/sites-enabled/`, change the line
```
index index.html index.htm;
```
to
```
index index.php index.html index.htm;
```
and uncomment the lines
```
location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/var/run/php5-fpm.sock;
}
```
To install the YaML extension in PHP, execute
```
sudo apt-get install libyaml-dev
sudo apt-get install php-dev
sudo pecl install yaml
```
Copy `index.php` to `/var/www/html`. To allow the web server to write to `/home/pi`, execute `sudo chmod a+rwx /home/pi`, and type `sudo visudo` to add the following line to the `/etc/sudoers` file:
```
www-data ALL=(ALL) NOPASSWD: ALL
```
You may also need to execute a `sudo chmod a+rw /home/pi/*.yaml`. Now you can access the web configuration panel by pointing a browser at the Pi's IP address.

## Usage
Short taps of either button will switch between instrument patches or soundfont presets. Long-pressing (~2sec) right will enter the patch/soundfont menu, and long-pressing left will open the options menu.

- Patch Menu
  - Update Patch – Save the current patch with any updated control change/program change values
  - Save New Patch – Save the current patch and any updated control change/program change values as a new patch
  - Rename Patch – Enter a new name for the current patch using the cumbersome stompbox button text entry method
  - Delete Patch – Delete the current patch. Can’t do this if it’s the only patch left
- Soundfont Menu
  - Save as New Patch – Create a new patch in the current bank with the current soundfont preset loaded into MIDI channel 1
  - Exit Soundfont – Unload the current soundfont and return to patch mode
- Options Menu
  - Switch Bank – Load a different bank
  - Save as New Bank – Create a new bank from the current set of patches. Will suggest a name that can be modified with text entry. Scroll to the end of the name and long-press right to save.
  - Set Gain – Change the gain (volume) level of fluidsynth. Higher gain values are louder but require more simultaneous voices and thus processing power.
  - Chorus/Reverb – Modify the parameters of the chorus/reverb unit.
  - Advanced.. – Open the advanced options menu
  - Power Down – Shut down the Squishbox. You can always just unplug, but there is a risk of corrupting the SD card if you do.
- Advanced Options Menu
  - Open Soundfont – Choose an .sf2 file from the pi user’s home directory (/home/pi), open it, and switch to soundfont mode, in which the user can scroll through presets in the soundfont file.
  - MIDI Reconnect – Detect any connected MIDI controllers and attempt to link them to fluidsynth.
  - Wifi Settings – Show the current network name and IP address if connected. Tapping left or right reveals an option to add a network name and passkey using the stompswitches.
  - Add From USB – Hunts for a connected USB drive, finds all .sf2 files on it, and copies them to your Squishbox. Preserves folder structure, so if you have your fonts organized into different folders on your USB they will stay that way on the Squishbox.
    

Configuration files are in the [YAML](http://www.yaml.org/spec/1.2/spec.html) format. The file `squishbox_settings.yaml` contains global settings for the squishbox, and `bank0.yaml` contains some default patches. Both have enough comments that their structure should be easily understood. Additional bank files can be created as desired.

## Included Soundfont
The *ModWaves.sf2* soundfont is included as an example of using modulators in a soundfont. In this case, the resonance and cut-off frequency of the low-pass filter are routed to CC 70 and 74 (per the general MIDI spec), respectively. This allows a MIDI controller to modify these values interactively by sending control change messages. Modulators can be used to control a wide range of synthesis parameters in FluidSynth (e.g. ADSR envelope, LFO frequency/depth, modulation envelope, etc.), making FluidSynth a very powerful and versatile live softsynth. I highly recommend [Polyphone](http://polyphone-soundfonts.com/en/) for editing soundfonts. The [soundfont specification](https://en.wikipedia.org/wiki/SoundFont) can be a useful reference when editing soundfonts.
