#!/bin/sh

cd /mnt/usbdrv
find -name '*.sf2' -exec cp --parents -f {} /home/pi/ \;

