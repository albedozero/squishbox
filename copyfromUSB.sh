#!/bin/sh

cd /mnt/usbdrv
find -name '*.sf2' -exec cp --parents -f {} /home/pi/ \;
cd /home/pi
find -type d -exec chmod 0777 {} \;
find -type f -exec chmod 0666 {} \;
