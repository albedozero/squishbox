# SquishBox
Python fluidsynth wrapper/interface for a stompbox sound module powered by fluidsynth (because that's what happens if you stomp on a box full of fluid).

## Explanation
This project provides the software front-end for a sound module consisting of a small linux SBC (e.g. a Raspberry Pi) connected to a 16x2 character LCD, a couple of momentary stompswitches for user input, and a USB sound card for audio output. An example is described in [this instructable](https://www.instructables.com/id/Raspberry-Pi-Stompbox-Synth-Module/). The end result could look something like this:

![SquishBox image](/images/example.jpg)

The wiring could be realized as in this diagram:

![SquishBox schematic](/images/squishboxhat.png)
The *squishbox.py* python script controls the LCD, handles the buttons, and uses the included version of the [PyFluidSynth]() library *fluidsynth.py* to call and interact with fluidsynth.

## Installation
Files in the package may be copied to any convenient place (i.e. */home/pi*). [FluidSynth](http://www.fluidsynth.org) must be installed. On Raspbian the simplest method is to use aptitude from the command line:
```
sudo apt-get install fluidsynth
```
The Python script requires non-standard libraries RPi.GPIO, PyYaml, and RPLCD. Recent versions of Raspbian should have the first installed by default. The second two can be installed from PyPI by entering:
```
sudo pip install RPLCD pyyaml
```
The user will most likely want the software to run at bootup. To effect this, modify the */etc/rc.local* file, adding the following just before the final `exit 0` line:
```
sudo python /home/pi/squishbox.py &
```

## Usage
Short taps of either button will switch between instrument patches. Holding either button for a approximately two seconds enters a settings menu, and holding either button for roughly five seconds provides the option to restart the program, reboot the Pi, or shut the Pi down. The settings menu options are:
- Update Patch - saves any changes made to the current patch to file
- Save New Patch - saves the current patch and any changes as a new patch
- Choose Bank - allows switching between any number of patch sets specified in the config file
- Set Gain - set the overall output volume (fluidsynth's 'gain' option), too high gives distorted output
- Chorus/Reverb - enter a sub-menu to modify the current set's reverb and chorus settings
- MIDI Connect - attempts to connect a USB MIDI device to fluidsynth
- Bluetooth Pair - put the computer in discovery mode so another bluetooth device can be paired with it
- Wifi Status - report the current IP address

## Configuration
The *config_squishbox.yaml* is written in the [YAML](http://www.yaml.org/spec/1.2/spec.html) format and specifies things such as patch/effect settings, soundfont locations, and MIDI routing. The included file can be extensively modified to use different soundfonts and produce different patches and behavior. The expected structure of the file is:

- *settings* - a dictionary of global program settings
  - *sfdirs* (required) - sequence of paths to search for soundfonts used in patches
  - *gain* - initial gain level for fluidsynth
  - *fluidsettings* - dictionary of options: values to pass directly to fluidsynth
  - *soundfont* - a default soundfont file to use for all patches if not specified by the patch
- *sets* - a sequence of patch lists and chorus, reverb, and MIDI router settings for each one
  - *chorus_level* - output level of chorus unit
  - *chorus_nr* - number of delay lines for chorus
  - *chorus_depth* - modulation depth (ms)
  - *chorus_speed* - modulation speed in Hz
  - *chorus_type* - 0 or 1, where 0=sine and 1=triangle
  - *reverb_level* - output level of reverb unit
  - *reverb_roomsize* - size of the room simulated by reverb
  - *reverb_width* - amount of early reflection (brightness) of reverb
  - *reverb_damping* - high-frequency damping amount
  - *router_rules* - a sequence of MIDI message routing rules to send to fluidsynth when each patch in this set is selected; a rule can be one of the following:
    - *clear* - clears any previous routing rules
    - *default* - clears any previous routing rules and restores 1-1 routing for all message types
    - a dictionary defining a router rule; closely follows the format used by the fluidsynth command shell
      - *type* (required) - one of the message types defined by fluidsynth; if this is all that is given routing defaults to 1-1 for this type
      - *chan* - a sequence describing the channel routing in the form *min, max, mul, add*, where *min-max* is the incoming channel range to accept, and the channel number is then multiplied by *mul* and added to *add*.
      - *par1* - routes parameter 1 (e.g note value or CC value) in the same way as *chan*
      - *par2* - routes parameter 2 if there is one (e.g. note velocity)
  - *patches* a sequence of patches, where each patch is a dictionary containing the following items
    - *name* (required) - this text is displayed on the LCD when the patch is selected
    - *0-15* - the MIDI channel the following soundfont preset will be applied to; N.B. not all channels have to be assigned; channels with no assignment will retain whatever preset they were last assigned
      - *soundfont* - a soundfont file
      - *bank* (required) - the bank number in the soundfont file
      - *program* (required) - the program number in the soundfont file
      - *cc* - a dictionary of control change numbers: values(0-127) to send on this channel when the patch is selected. Any modified CC values will be saved to the patch if it is updated.
    - *router_rules* - router rules for this patch, applied after set-wide router rules; if no router rules are specified by set or patch defaults to 1-1 routing for all types

## Included Soundfont
The *ModWaves.sf2* soundfont is included as an example of using modulators in a soundfont. In this case, the resonance and cut-off frequency of the low-pass filter are routed to CC 70 and 74 (per the general MIDI spec), respectively. This allows a MIDI controller to modify these values interactively by sending control change messages. Modulators can be used to control a wide range of synthesis parameters in FluidSynth (e.g. ADSR envelope, LFO frequency/depth, modulation envelope, etc.), making FluidSynth a very powerful and versatile live softsynth. I highly recommend [Polyphone](http://polyphone-soundfonts.com/en/) for editing soundfonts.
