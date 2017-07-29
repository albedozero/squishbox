#!/usr/bin/python

import RPi.GPIO as GPIO
from RPLCD import CharLCD
from time import sleep
from subprocess import call
from os import getpid
from yaml import safe_load, dump
import fluidsynth

POLL_TIME=0.025
BTN_L=13
BTN_R=12

SQBX_NULL=0
SQBX_TAP=1
SQBX_PRESS=2
SQBX_HOLD=3
SQBX_LONGPRESS=4
SQBX_LONGHOLD=5

r_holdtime=0
r_state=0
l_holdtime=0
l_state=0
def poll_stompswitches():
    global r_holdtime, r_state, l_holdtime, l_state
    if GPIO.input(BTN_R)==GPIO.HIGH:
        r_holdtime += POLL_TIME        
        if r_holdtime>=3.5:
            if r_state<SQBX_LONGPRESS:
                r_state=SQBX_LONGPRESS
            else:
                r_state=SQBX_LONGHOLD
        elif r_holdtime>=1.0:
            if r_state<SQBX_PRESS:
                r_state=SQBX_PRESS
            else:
                r_state=SQBX_HOLD
    if GPIO.input(BTN_L)==GPIO.HIGH:
        l_holdtime += POLL_TIME        
        if l_holdtime>=3.5:
            if l_state<SQBX_LONGPRESS:
                l_state=SQBX_LONGPRESS
            else:
                r_state=SQBX_LONGHOLD
        elif l_holdtime>=1.0:
            if l_state<SQBX_PRESS:
                l_state=SQBX_PRESS
            else:
                l_state=SQBX_HOLD
    if GPIO.input(BTN_R)==GPIO.LOW:
        if r_holdtime>0 and r_state<SQBX_TAP:
            r_state=SQBX_TAP
        else:
            r_holdtime=0
            r_state=SQBX_NULL
    if GPIO.input(BTN_L)==GPIO.LOW:
        if l_holdtime>0 and l_state<SQBX_TAP:
            l_state=SQBX_TAP
        else:
            l_holdtime=0
            l_state=SQBX_NULL

def waitfortap(t):
    for i in range(int(t/POLL_TIME)):
        sleep(POLL_TIME)
        poll_stompswitches()
        if r_state==SQBX_TAP or l_state==SQBX_TAP:
            return

def waitforrelease(tmin=0):
    t=0
    while True:
        sleep(POLL_TIME)
        t+=POLL_TIME
        poll_stompswitches()
        if r_state+l_state==SQBX_NULL and t>=tmin:
            return
            
def midi_connect():
    # try to connect a midi input device
    # use 'aconnect -i' to see where yours shows up
    for d in ['20:0','20:1','24:0','24:1']:
        call(['aconnect', d, '128:0'])
    
def menu_mode():
    i=0
    while True:
        lcd.cursor_pos=(1,0)
        lcd.write_string("%16s" % ['Update Patch',
                                   'Save New Patch',
                                   'Choose Bank',
                                   'Set Gain',
                                   'Chorus/Reverb',
                                   'MIDI Connect',
                                   'Bluetooth Pair',
                                   'Wifi Status'][i])
        for j in range(int(10/POLL_TIME)):
            sleep(POLL_TIME)
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state==SQBX_TAP:
                i=(i+1)%8
                break
            elif l_state==SQBX_TAP:
                i=(i-1)%8
                break
            elif l_state==SQBX_PRESS or r_state==SQBX_PRESS:
                if i==0:
                    update_patch()
                    lcd.cursor_pos=(1,0)
                    lcd.write_string("        Updated!")
                    waitforrelease(1)
                elif i==1:
                    save_new_patch()                    
                    lcd.cursor_pos=(1,0)
                    lcd.write_string("           Saved!")
                    waitforrelease(1)
                elif i==2:
                    lcd.cursor_pos=(1,0)
                    lcd.write_string("                 ")
                    choose_patchbank()
                elif i==3:
                    modify_gain()
                elif i==4:
                    modify_fxunit()
                elif i==5:
                    lcd.clear()
                    midi_connect()
                    waitforrelease()
                elif i==6:
                    bluetooth_pair()
                elif i==7:
                    wifi_status()
                return
            elif r_state==SQBX_LONGPRESS or l_state==SQBX_LONGPRESS:
                system_menu()
                return
        else:
            return

def system_menu():
    i=0
    while True:
        lcd.clear()
        lcd.write_string("%16s" % ['Shutdown?',
                                   'Restart?',
                                   'Reboot?'][i])
        for j in range(int(10/POLL_TIME)):
            sleep(POLL_TIME)
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state==SQBX_TAP:
                i=(i+1)%3
                break
            elif l_state==SQBX_TAP:
                i=(i-1)%3
                break
            elif l_state==SQBX_PRESS or r_state==SQBX_PRESS:
                if i==0:
                    lcd.clear()
                    lcd.write_string("Shutting down...Wait 30s, unplug")
                    call('sudo shutdown -h now'.split())
                elif i==1:
                    lcd.clear()
                    lcd.write_string("Restarting...")
                    waitforrelease(1)
                    call('sudo python squishbox.py &'.split())
                elif i==2:
                    lcd.clear()
                    lcd.write_string("Rebooting...")
                    call('sudo reboot'.split())
        else:
            return
 
            
def shutdown_confirm():
    lcd.clear()
    lcd.write_string("Shutdown?       ")
    for i in range(int(10/POLL_TIME)):
        sleep(POLL_TIME)
        poll_stompswitches()
        if l_state==SQBX_TAP or r_state==SQBX_TAP:
            return
        if l_state==SQBX_PRESS or r_state==SQBX_PRESS:
            lcd.clear()
            lcd.write_string("Shutting down...")
            call('sudo shutdown -h now'.split())

def midi_route(type, par1=[], par2=[], chan=[]):
    fluid.router_begin(type)
    if len(chan)>0:
        fluid.router_chan(*chan)
    if len(par1)>0:
        fluid.router_par1(*par1)
    if len(par2)>0:
        fluid.router_par2(*par2)
    fluid.router_end()
    
def choose_patchbank():
    global patches, sno, pno
    while True:
        bt=0
        for i in range(int(10/POLL_TIME)):
            sleep(POLL_TIME)
            bt+=POLL_TIME/0.25
            if bt>2.0:
                lcd.cursor_pos=(0,0)
                lcd.write_string("%02d" % sno)
                bt=0
            if bt>1.0:
                lcd.cursor_pos=(0,0)
                lcd.write_string("  ")
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state==SQBX_TAP:
                sno=(sno+1)%len(sets)
                patches=sets[sno]['patches']
                pno=min(pno, len(patches)-1)
                load_patch()
                set_chorus_reverb()
                break
            elif l_state==SQBX_TAP:
                sno=(sno-1)%len(sets)
                patches=sets[sno]['patches']
                pno=min(pno, len(patches)-1)
                load_patch()
                set_chorus_reverb()
                break
            elif l_state==SQBX_PRESS or r_state==SQBX_PRESS:
                return
        else:
            return     

def modify_gain():
    global settings
    lcd.clear()
    lcd.write_string("Set Gain:       ")
    waitforrelease()
    while True:
        lcd.cursor_pos=(1,0)
        lcd.write_string("%16.2f" % settings['gain'])
        for i in range(int(5/POLL_TIME)):
            sleep(POLL_TIME)
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state>SQBX_NULL:
                settings['gain']+=0.1
            elif l_state>SQBX_NULL:
                settings['gain']-=0.1
            if settings['gain']>5.0:
                settings['gain']=5.0
            if settings['gain']<0.0:
                settings['gain']=0.0
            fluid.setting('synth.gain', settings['gain'])
            break
        else:
            write_cfg()
            return
            
def enter_fxunitparam(param, format, inc, min, max):
    global sets
    val=sets[sno][param]
    waitforrelease()
    while True:
        lcd.cursor_pos=(1,0)
        lcd.write_string(format % val)
        for i in range(int(5/POLL_TIME)):
            sleep(POLL_TIME)
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state>SQBX_NULL:
                val+=inc
            elif l_state>SQBX_NULL:
                val-=inc
            if val>max:
                val=max
            if val<min:
                val=min
            sets[sno][param]=val
            set_chorus_reverb()
            break
        else:
            write_cfg()
            return
            
def modify_fxunit():
    global sets
    i=0
    while True:
        lcd.cursor_pos=(0,0)
        lcd.write_string("Chorus/Reverb:  ")
        lcd.write_string("%16s" % ['Chorus Voices',
                                   'Chorus Level',
                                   'Chorus Speed',
                                   'Chorus Depth',
                                   'Chorus Type',
                                   'Reverb Size',
                                   'Reverb Damping',
                                   'Reverb Width',
                                   'Reverb Level'][i])
        for j in range(int(5/POLL_TIME)):
            sleep(POLL_TIME)
            poll_stompswitches()
            if r_state+l_state==SQBX_NULL:
                continue
            elif r_state==SQBX_TAP:
                i=(i+1)%9
                break
            elif l_state==SQBX_TAP:
                i=(i-1)%9
                break
            elif l_state==SQBX_PRESS or r_state==SQBX_PRESS:
                lcd.clear()
                if i==0:
                    lcd.write_string("Chorus Voices   ")
                    sets[sno]['chorus_nr']=fluid.get_chorus_nr()
                    enter_fxunitparam('chorus_nr','%16d',1,0,99)
                elif i==1:
                    lcd.write_string("Chorus Level    ")
                    sets[sno]['chorus_level']=fluid.get_chorus_level()
                    enter_fxunitparam('chorus_level','%16.1f',0.1,0.0,10.0)
                elif i==2:
                    lcd.write_string("Chorus Depth(ms)")
                    sets[sno]['chorus_depth']=fluid.get_chorus_depth()
                    enter_fxunitparam('chorus_depth','%16.1f',0.1,0.0,21.0)
                elif i==3:
                    lcd.write_string("Chorus Speed(Hz)")
                    sets[sno]['chorus_speed']=fluid.get_chorus_speed()
                    enter_fxunitparam('chorus_speed','%16.1f',0.1,0.3,5.0)
                elif i==4:
                    lcd.write_string("Type 0:sin 1:tri")
                    sets[sno]['chorus_type']=fluid.get_chorus_type()
                    enter_fxunitparam('chorus_type','%16d',1,0,1)
                elif i==5:
                    lcd.write_string("Reverb Size     ")
                    sets[sno]['reverb_roomsize']=fluid.get_reverb_roomsize()
                    enter_fxunitparam('reverb_roomsize','%16.1f',0.1,0.0,1.2)
                elif i==6:
                    lcd.write_string("Reverb Damping  ")
                    sets[sno]['reverb_damping']=fluid.get_reverb_damp()
                    enter_fxunitparam('reverb_damping','%16.1f',0.1,0.0,1.0)
                elif i==7:
                    lcd.write_string("Reverb Width    ")
                    sets[sno]['reverb_width']=fluid.get_reverb_width()
                    enter_fxunitparam('reverb_width','%16.1f',1.0,0.0,100.0)
                elif i==8:
                    lcd.write_string("Reverb Level    ")
                    sets[sno]['reverb_level']=fluid.get_reverb_level()
                    enter_fxunitparam('reverb_level','%16.2f',0.01,0.00,1.00)
                break
        else:
            return

def set_chorus_reverb():
    if 'chorus_nr' in sets[sno]:
        fluid.set_chorus(nr=sets[sno]['chorus_nr'])
    if 'chorus_level' in sets[sno]:
        fluid.set_chorus(level=sets[sno]['chorus_level'])
    if 'chorus_depth' in sets[sno]:
        fluid.set_chorus(depth=sets[sno]['chorus_depth'])
    if 'chorus_speed' in sets[sno]:
        fluid.set_chorus(speed=sets[sno]['chorus_speed'])
    if 'chorus_type' in sets[sno]:
        fluid.set_chorus(type=sets[sno]['chorus_type'])
    if 'reverb_roomsize' in sets[sno]:
        fluid.set_reverb(roomsize=sets[sno]['reverb_roomsize'])
    if 'reverb_damping' in sets[sno]:
        fluid.set_reverb(damping=sets[sno]['reverb_damping'])
    if 'reverb_level' in sets[sno]:
        fluid.set_reverb(level=sets[sno]['reverb_level'])
    if 'reverb_width' in sets[sno]:
        fluid.set_reverb(width=sets[sno]['reverb_width'])
            
def load_patch():
    lcd.clear()
    p=patches[pno]
    lcd.cursor_pos=(0,0)
    lcd.write_string("%02d-%02d:%-10s" % (sno,pno,p['name'][:10]))
    fluid.router_clear()
    if 'router_rules' in sets[sno]:
        for rule in sets[sno]['router_rules']:
            midi_route(**rule)
    if 'router_rules' in p:
        for rule in p['router_rules']:
            if rule=='default':
                fluid.router_default()
            elif rule=='clear':
                fluid.router_clear()
            else:
                midi_route(**rule)
    if 'rule' not in locals():
        fluid.router_default()
    for ch in range(16):
        if ch not in p:
            continue
        if 'soundfont' in p[ch]:
            sf=p[ch]['soundfont']
        elif 'soundfont' in settings:
            sf=settings['soundfont']
        else:
            continue
        fluid.program_select(ch,sfids[sf],p[ch]['bank'],p[ch]['program'])
        if 'cc' not in p[ch]:
            continue
        for cc,val in p[ch]['cc'].iteritems():
            fluid.cc(ch,cc,val)
        
def update_patch():
    global patches
    p=patches[pno]
    for ch in range(16):
        (sfid,bank,prog,name)=fluid.channel_info(ch)
        if sfid not in sfids.values():
            continue
        if ch not in p:
            p[ch]={}
        for sf in sfids.keys():
            if sfids[sf]==sfid:
                p[ch]['soundfont']=sf
                break
        p[ch]['bank']=bank
        p[ch]['program']=prog
        if 'cc' in p[ch]:
            del p[ch]['cc']
# check for any nonzero cc values, avoid those reserved for special functions
        for cc in [1,2,3,5,7,9]+range(11,32)+range(33,64)+range(70,96)+range(102,120):
            val=fluid.get_cc(ch,cc)
            if val>0: # 0 --> cc not changed
                if 'cc' not in p[ch]:
                    p[ch]['cc']={}
                p[ch]['cc'][cc]=val                    
    write_cfg()

def save_new_patch():
    global patches,pno
    pnew=len(patches)
    patches.append({'name':patches[pno]['name']})
    if 'router_rules' in patches[pno]:
        patches[pnew]['router_rules']=[]
        for rule in patches[pno]['router_rules']:
            patches[pnew]['router_rules'].append(dict(rule))
    pno=pnew
    update_patch()

def bluetooth_pair():
    lcd.clear()
    lcd.write_string("Pairing Mode... ")
    call('sudo hciconfig hci0 piscan'.split())
    waitfortap(90)
    lcd.cursor_pos=(1,0)
    lcd.write_string("Stopping...     ")
    call('sudo hciconfig hci0 noscan'.split())                    
    waitforrelease(1)

def wifi_status():
    f=open('/tmp/wifistatus','w')
    call('iwgetid wlan0 --raw'.split(),stdout=f)
    call('hostname -I'.split(),stdout=f)
    f.close()
    ssid,ip = open('/tmp/wifistatus').read().split('\n')[:2]
    lcd.clear()
    waitforrelease()
    if ssid=="":
        lcd.write_string("Not connected")
    else:
        lcd.write_string("%16s\n%-16s" % (ssid,ip.split()[0]))
    waitfortap(10)
        
def write_cfg():
    f = open('/home/pi/config_jampi.yaml','w')
    dump(config,f)
    f.close()

### SETUP ###    
    
# look for /tmp/squishbox.pid containing PID of
# an already-running version of this script and kill it
# there can be only one
try:
    f=open('/tmp/squishbox.pid','r')
    for pid in f.read().split():
        if pid!=str(getpid()):
            call(['sudo','kill',pid])
    f.close()
    call('rm /tmp/squishbox.pid'.split())
except:
    pass
f=open('/tmp/squishbox.pid','a')
f.write(str(getpid()))
f.write('\n')
f.close()

# set up gpios for buttons, and be quiet about it
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_L, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BTN_R, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

lcd = CharLCD(pin_rs=17, pin_rw=None, pin_e=18, pins_data=[27,22,23,24],
                    numbering_mode=GPIO.BCM,
                    pin_backlight=5, backlight_enabled=True,
                    cols=16, rows=2)
lcd.clear()
lcd.write_string("squishbox v0.96")
lcd.backlight_enabled=True

# load settings file with patches and stuff
f = open('/home/pi/config_squishbox.yaml')
config = safe_load(f)
f.close()
sets = config['sets']
settings = config['settings']

# start an instance of fluidsynth
fluid=fluidsynth.Synth(channels=16)
for opt,val in settings['fluidsettings'].iteritems():
    fluid.setting(opt,val)
if 'gain' in settings:
    fluid.setting('synth.gain', settings['gain'])

# initialize the audio and midi devices
fluid.start(driver='alsa', device='hw:Device,0', midi_driver='alsa_seq')

# try to connect a midi controller
midi_connect()

# load necessary soundfonts
sfids={}
for s in sets:
    for p in s['patches']:
        for ch in range(16):
            if ch not in p:
                continue
            sf=p[ch]['soundfont']
            if sf in sfids.keys():
                continue
            for dir in settings['sfdirs']:
                id=fluid.sfload(dir+sf)
                if id>0:
                    sfids[sf]=id
                    break
                   
sno=0
patches=sets[sno]['patches']
pno=0
lcd.clear()
load_patch()
set_chorus_reverb()
### MAIN ###
while True:
    st=0
    while True:
        sleep(POLL_TIME)
        st+=POLL_TIME/0.25
        t=int(st)
        if t>3:
            if t<len(patches[pno]['name'])-6:
                lcd.cursor_pos=(0,6)
                lcd.write_string("%-10s" % (patches[pno]['name'][t-3:t+7]))
            elif t>len(patches[pno]['name'])+1:
                lcd.cursor_pos=(0,6)
                lcd.write_string("%-10s" % (patches[pno]['name'][:10]))
                st=0
        poll_stompswitches()
        if r_state+l_state==SQBX_NULL:
            continue
        elif r_state==SQBX_TAP:
            pno=(pno+1)%len(patches)
            load_patch()
            break
        elif l_state==SQBX_TAP:
            pno=(pno-1)%len(patches)
            load_patch()
            break
        elif r_state==SQBX_PRESS or l_state==SQBX_PRESS:
            menu_mode()
            lcd.clear()
            load_patch()
            break
