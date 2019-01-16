#!/usr/bin/python3
"""
Copyright (c) 2018 Bill Peterson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import time
import re
import yaml
from subprocess import call, check_output

import stompboxpi as SB

def midi_connect():
    mididevs={}
    for client in check_output(['aconnect','-i']).split(b'client'):
        x=re.match(b" (\d+:) '([ \w]*)'",client)
        if not x:
            continue
        ports=re.findall(b"\n +(\d+) '",client)
        mididevs[x.group(2)]=[x.group(1)+p for p in ports]
    del mididevs[b'System']
    del mididevs[b'Midi Through']
    for d in mididevs.keys():
        for p in mididevs[d]:
            call(['aconnect', p, fluidport])
    
def midi_route(type, par1=[], par2=[], chan=[]):
    fluid.router_begin(type)
    if chan:
        fluid.router_chan(*chan)
    if par1:
        fluid.router_par1(*par1)
    if par2:
        fluid.router_par2(*par2)
    fluid.router_end()

def set_chorus_reverb():
    try:
        if 'chorus_nr' in bank:
            fluid.set_chorus_nr(bank['chorus_nr'])
        if 'chorus_level' in bank:
            fluid.set_chorus_level(bank['chorus_level'])
        if 'chorus_depth' in bank:
            fluid.set_chorus_depth(bank['chorus_depth'])
        if 'chorus_speed' in bank:
            fluid.set_chorus_speed(bank['chorus_speed'])
        if 'chorus_type' in bank:
            fluid.set_chorus_type(bank['chorus_type'])
        if 'reverb_roomsize' in bank:
            fluid.set_reverb_roomsize(bank['reverb_roomsize'])
        if 'reverb_damping' in bank:
            fluid.set_reverb_damping(bank['reverb_damping'])
        if 'reverb_level' in bank:
            fluid.set_reverb_level(bank['reverb_level'])
        if 'reverb_width' in bank:
            fluid.set_reverb_width(bank['reverb_width'])
    except NameError:
        if 'chorus_nr' in bank:
            fluid.set_chorus(nr=bank['chorus_nr'])
        if 'chorus_level' in bank:
            fluid.set_chorus(level=bank['chorus_level'])
        if 'chorus_depth' in bank:
            fluid.set_chorus(depth=bank['chorus_depth'])
        if 'chorus_speed' in bank:
            fluid.set_chorus(speed=bank['chorus_speed'])
        if 'chorus_type' in bank:
            fluid.set_chorus(type=bank['chorus_type'])
        if 'reverb_roomsize' in bank:
            fluid.set_reverb(roomsize=bank['reverb_roomsize'])
        if 'reverb_damping' in bank:
            fluid.set_reverb(damping=bank['reverb_damping'])
        if 'reverb_level' in bank:
            fluid.set_reverb(level=bank['reverb_level'])
        if 'reverb_width' in bank:
            fluid.set_reverb(width=bank['reverb_width'])
    
def select_sfpreset(p):
    (n,bank,prog)=p
    fluid.program_select(0,sfid,bank,prog)
    for ch in range(1,16):
        fluid.program_unset(ch)
    fluid.router_clear()
    fluid.router_default()

def load_soundfont(f):
    global sfid, sfpresets
    if sfid:
        fluid.sfunload(sfid,1)
    sfid=fluid.sfload(f)
    sfpresets=[]
    for b in range(129): # banks can go higher, but we'd be here all day
        for p in range(128):
            name=fluid.sfpreset_name(sfid,b,p)
            if not name:
                continue
            sfpresets.append((name,b,p))

def select_patch(p):
    fluid.router_clear()
    if 'router_rules' in bank:
        for rule in bank['router_rules']:
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
        x=fluid.program_select(ch,
                             sfids[p[ch]['soundfont']],
                             p[ch]['bank'],
                             p[ch]['program'])
        if 'cc' in p[ch]:
            for cc,val in p[ch]['cc'].items():
                fluid.cc(ch,cc,val)
        
def update_patch(p):
    for ch in range(16):
        (sfid,bank,prog)=fluid.program_info(ch)
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
# check for any nonzero cc values, avoid those reserved for special functions
        for (f,l) in [(1,3),(5,5),(7,31),(33,63),(65,65),(70,83),(85,95),(102,119)]:
            for cc in range(f,l+1):
                val=fluid.get_cc(ch,cc)
                if val>0: # 0 --> cc not changed
                    if 'cc' not in p[ch]:
                        p[ch]['cc']={}
                    p[ch]['cc'][cc]=val
    write_bank()

def add_patch(name='noname'):
    global patches,pno
    pnew=len(patches)
    patches.append({'name':name})
    if 'router_rules' in patches[pno]:
        patches[pnew]['router_rules']=[]
        for rule in patches[pno]['router_rules']:
            patches[pnew]['router_rules'].append(dict(rule))
    update_patch(patches[pnew])
    
def load_bank(file):
    global bank, sfids
    try:
        f=open(file)
        x = yaml.safe_load(f)
    except yaml.YAMLError or IOError:
        return False
    f.close()
    sfused=[]
    bank=x
    for p in bank['patches']:
        for ch in range(16):
            if ch not in p:
                continue
            sf=p[ch]['soundfont']
            if sf not in sfused:
                sfused.append(sf)
    for sf in list(sfids.keys()):
        if sf not in sfused:
            fluid.sfunload(sfids[sf],1)
            del sfids[sf]
    for sf in sfused:
        if sf not in sfids:
            if 'soundfonts' in bank and sf in bank['soundfonts']:
                id=fluid.sfload(bank['soundfonts'][sf])
            else:
                id=fluid.sfload(sf)
            sfids[sf]=id
    set_chorus_reverb()
    fluid.setting('synth.gain', bank.get('gain',0.5))
    return True
    
def write_bank(newbank=''):
    if not newbank:
        newbank=config['currentbank']
    try:
        f = open(newbank,'w')
        yaml.dump(bank,f)
    except yaml.YAMLError or IOError:
        return False
    f.close()
    return True
    
def write_config():
    try:
        f = open('/home/pi/squishbox_settings.yaml','w')
        yaml.dump(config,f)
    except yaml.YAMLError or IOError:
        return False
    f.close()
    return True

def soundfont_menu():
    global config, patches, sfids, sfid
    k=SB.choose_opt(['Save as Patch','Exit Soundfont'],1)
    if k==0:
        newsfid=fluid.sfload(config['soundfont'])
        sfids[config['soundfont']]=newsfid
        pnew=len(patches)
        patches.append({'name':sfpresets[sfp][0]})
        patches[pnew][0]={'soundfont': config['soundfont'],
                          'bank': sfpresets[sfp][1],
                          'program': sfpresets[sfp][2]}
        write_bank()
    if k==1:
        config['soundfont']=''
        fluid.sfunload(sfid)
        sfid=0
        select_patch(patches[pno])
        write_config()

def patch_menu():
    global patches, pno
    k=SB.choose_opt(['Update Patch','Save New Patch','Rename Patch','Delete Patch'],1)
    if k==0:
        update_patch(patches[pno])
        SB.lcd_message("updated!        ",1)
        SB.waitforrelease(1)
    elif k==1:
        newname=patches[pno]['name']
        x=re.search('[0-9]*$',newname)
        if x.group():
            newname=re.sub('[0-9]*$',"%d" % (int(x.group())+1),newname)
        else:
            newname+='2'
        pnew=len(patches)
        patches.append({'name':newname})
        if 'router_rules' in patches[pno]:
            patches[pnew]['router_rules']=[]
            for rule in patches[pno]['router_rules']:
                patches[pnew]['router_rules'].append(dict(rule))
        update_patch(patches[pnew])
    elif k==2:
        SB.lcd_message("Rename Patch:   ")
        a=SB.char_input(patches[pno]['name'])
        if a:
            patches[pno]['name']=a
            write_bank()
    elif k==3:
        if len(patches)<2:
            SB.lcd_message("only 1 patch!   ",1)
            SB.waitforrelease(1)
        else:
            del patches[pno]
            pno=(pno-1)%len(patches)
            select_patch(patches[pno])
            write_bank()

def switch_bank():
    global config
    SB.lcd_message("Load Bank:      ")
    bpaths=check_output("find /home/pi -name '*.yaml'",shell=True).strip()
    banks=[x[9:] for x in bpaths.decode('ascii').split('\n')]
    del banks[banks.index('squishbox_settings.yaml')]
    i=SB.choose_opt(banks, row=1, scroll=True)
    if i>=0:
        SB.lcd_message("loading patches ",1)
        if not load_bank(banks[i]):
            SB.lcd_message("bank load error!",1)
            SB.waitforrelease(2)            
            return False
        config['currentbank']=banks[i]
        if config['uselastbank']:
            config['initialbank']=banks[i]
        write_config()
        SB.waitforrelease(1)
        return True
    return False

def saveasnew_bank():
    global config
    x=re.search('([0-9]*).yaml$',config['currentbank'])
    if x.group(1):
        f=re.sub('[0-9]*.yaml$',"%d.yaml" % (int(x.group(1))+1),config['currentbank'])
    else:
        f=re.sub('\.yaml$','2.yaml',config['currentbank'])
    SB.lcd_message("New Bank:       ")
    newbank=SB.char_input(f)
    if newbank:
        if not re.search('\.yaml$',newbank):
            newbank+='.yaml'
        if not write_bank(newbank):
            SB.lcd_message("bank save error!",1)
            SB.waitforrelease(1)
            return
        call(['sudo','chmod','666',newbank])
        config['currentbank']=newbank
        if config['uselastbank']:
            config['initialbank']=newbank
        write_config()
        SB.lcd_message("new bank saved! ",1)
        SB.waitforrelease(1)

def chorverb_menu():
    global bank
    opts=['Chorus Voices','Chorus Level','Chorus Speed',
          'Chorus Depth','Chorus Type','Reverb Size',
          'Reverb Damping','Reverb Width','Reverb Level']
    while True:
        SB.lcd_message("Chorus/Reverb   ")
        i=SB.choose_opt(opts,1)
        if i<0:
            return
        SB.lcd_message("%-16s" % opts[i])
        if i==0:
            bank['chorus_nr']=SB.choose_val(fluid.get_chorus_nr(),1,0,99,'%16d')
        elif i==1:
            bank['chorus_level']=SB.choose_val(fluid.get_chorus_level(),0.1,0.0,10.0,'%16.1f')
        elif i==2:
            bank['chorus_depth']=SB.choose_val(fluid.get_chorus_depth(),0.1,0.0,21.0,'%16.1f')
        elif i==3:
            bank['chorus_speed']=SB.choose_val(fluid.get_chorus_speed(),0.1,0.3,5.0,'%16.1f')
        elif i==4:
            bank['chorus_type']=SB.choose_val(fluid.get_chorus_type(),1,0,1,'%16d')
        elif i==5:
            bank['reverb_roomsize']=SB.choose_val(fluid.get_reverb_roomsize(),0.1,0.0,1.0,'%16.1f')
        elif i==6:
            bank['reverb_damping']=SB.choose_val(fluid.get_reverb_damp(),0.1,0.0,1.0,'%16.1f')
        elif i==7:
            bank['reverb_width']=SB.choose_val(fluid.get_reverb_width(),1.0,0.0,100.0,'%16.1f')
        elif i==8:
            bank['reverb_level']=SB.choose_val(fluid.get_reverb_level(),0.01,0.00,1.00,'%16.2f')
        set_chorus_reverb()
        write_bank()

def wifi_settings():
    ssid=check_output(['iwgetid','wlan0','--raw']).strip().decode('ascii')
    ip=re.sub(b'\s.*',b'',check_output(['hostname','-I'])).decode('ascii')
    if ssid=="":
        statusmsg="Not connected   \n"+' '*16
    else:
        statusmsg="%16s\n%-16s" % (ssid,ip)
    j=SB.choose_opt([statusmsg,"Add Network..   \n"+' '*16])
    if j==1:
        SB.lcd_message("Network (SSID):")
        newssid=SB.char_input()
        if not newssid:
            return
        SB.lcd_message("Password:")
        newpsk=SB.char_input()
        if not newpsk:
            return
        SB.lcd_message("adding network.."+' '*16)
        f=open('/etc/wpa_supplicant/wpa_supplicant.conf','a')
        f.write('network={\n  ssid="%s"\n  psk="%s"\n}\n' % (newssid,newpsk))
        f.close()
        call('sudo service networking restart'.split())
        SB.waitforrelease(1)
            
def open_soundfont():
    global config
    sfpath=check_output("find /home/pi -name '*.sf2'",shell=True).strip()
    sf=[x[9:] for x in sfpath.decode('ascii').split('\n')]
    s=SB.choose_opt(sf,row=1,scroll=True)
    if s<0:
        return False
    SB.lcd_message("loading...      ",1)
    load_soundfont(sf[s])
    config['soundfont']=sf[s]
    write_config()
    SB.waitforrelease(1)
    return True
            
def add_fromusb():
    SB.lcd_clear()
    SB.lcd_message("looking for USB \n")
    b=check_output('sudo blkid'.split())
    x=re.findall(b'/dev/sd[a-z]\d*',b)
    if x:
        SB.lcd_message("copying files.. ",1)
        for u in x:
            call(['sudo','mount',u,'/mnt/usbdrv/'])
            call(['sudo','/home/pi/copyfromUSB.sh'])
            call(['sudo','umount',u])
        SB.lcd_clear()
        SB.lcd_message("copying files.. \ndone!")
        SB.waitforrelease(1)
    else:
        SB.lcd_message("USB not found!  ",1)
        SB.waitforrelease(1)

### STARTUP ###
SB.lcd_clear()
SB.lcd_message("Squishbox v2.0",0)
SB.lcd_message("setting up",1)

# load main settings file
try:
    f = open('/home/pi/squishbox_settings.yaml')
    config = yaml.safe_load(f)
except yaml.YAMLError or IOError:
    SB.lcd_message("bad config file!",1)
    time.sleep(10)
f.close()

# to do --
# if fluidversion is in settings,
#  set some environment variable so 
#  fluidsynth.py knows where it is, then
# import fluidsynth.py after this line
import importlib
fluidsynth = importlib.import_module(config.get('fluidversion','fluidsynth'))

# start fluidsynth
SB.lcd_message("starting fluid  ",1)
fluid=fluidsynth.Synth(channels=16)
for opt,val in config['fluidsettings'].items():
    fluid.setting(opt,val)
fluid.start(driver='alsa', device='hw:0', midi_driver='alsa_seq')
x=re.search(b"client (\d+:) 'FLUID Synth",check_output(['aconnect','-o']))
if not x:
    while True:
        SB.lcd_message("no fluid midi!  ")
        time.sleep(10)
fluidport=x.group(1).decode()+'0'
midi_connect()

# load bank
SB.lcd_message("loading patches ",1)
bank={}
sfids={}
if not load_bank(config['initialbank']):
    while True:
        SB.lcd_message("bank load error!",1)
        SB.waitfortap(10)
        if switch_bank():
            break        
config['currentbank']=config['initialbank']
patches=bank['patches']
sfp=0
sfid=0
sfpresets=[]

pno=0
select_patch(patches[pno])
sfp=0
sfid=0
sfpresets=[]
if config['soundfont']:
    load_soundfont(config['soundfont'])
    select_sfpreset(sfpresets[sfp])
SB.reset_scroll()
### MAIN ###
while True:
    time.sleep(SB.POLL_TIME)
    SB.poll_stompswitches()
    if config['soundfont']:
        SB.lcd_scroll(sfpresets[sfp][0])
        SB.lcd_message("%16s" % ("preset %03d:%03d" % sfpresets[sfp][1:3]),1)
        if SB.r_state==SB.STATE_TAP:
            sfp=(sfp+1)%len(sfpresets)
        elif SB.l_state==SB.STATE_TAP:    
            sfp=(sfp-1)%len(sfpresets)
        if SB.r_state==SB.STATE_TAP or SB.l_state==SB.STATE_TAP:
            select_sfpreset(sfpresets[sfp])
            SB.reset_scroll()
            continue
        elif SB.r_state==SB.STATE_HOLD:
            soundfont_menu()
            continue
    else:
        SB.lcd_scroll(patches[pno]['name'])
        SB.lcd_message("%16s" % ("patch: %d/%d" % (pno+1,len(patches))),1)
        if SB.r_state==SB.STATE_TAP:
            pno=(pno+1)%len(patches)
        elif SB.l_state==SB.STATE_TAP:    
            pno=(pno-1)%len(patches)
        if SB.r_state==SB.STATE_TAP or SB.l_state==SB.STATE_TAP:
            select_patch(patches[pno])
            SB.reset_scroll()
            continue
        elif SB.r_state==SB.STATE_HOLD:
            patch_menu()
            continue
    if SB.r_state+SB.l_state==SB.STATE_NONE:
        continue
    elif SB.l_state==SB.STATE_HOLD:
        SB.lcd_message("Settings:       ")
        k=SB.choose_opt(['Switch Bank','Save New Bank','Set Gain','Chorus/Reverb','Advanced..','Power Down'],1)
        if k==0:
            if switch_bank():
                patches=bank['patches']
                pno=0
                select_patch(patches[pno])
        elif k==1:
            saveasnew_bank()
        elif k==2:
            SB.lcd_message("Output Gain:    ")
            g=SB.choose_val(bank['gain'],0.1,0.0,5.0,"%16.2f")
            bank['gain']=g
            fluid.setting('synth.gain', g)
            write_bank()
        elif k==3:
            chorverb_menu()
        elif k==4:
            SB.lcd_message("Advanced:       ")
            j=SB.choose_opt(['Open Soundfont','MIDI Reconnect','Wifi Settings','Add From USB'],1)
            if j==0:
                if open_soundfont():
                    sfp=0
                    select_sfpreset(sfpresets[sfp])
            if j==1:
                SB.lcd_message("reconnecting..  ",1)
                midi_connect()
                SB.waitforrelease(1)
            if j==2:
                wifi_settings()
            if j==3:
                add_fromusb()
        elif k==5:
            SB.lcd_message("Shutting down...\nWait 30s, unplug",0)
            call('sudo shutdown -h now'.split())

                
