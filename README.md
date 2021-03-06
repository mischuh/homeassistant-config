# Home Assistant

## samba share

    wins support = yes

### Share

    [homeassistant]
    comment = Pi shared folder
    path = /usr/share/homeassistant
    browseable = yes
    writeable = Yes
    only guest = no
    create mask = 0777
    directory mask = 0777
    public = no
    veto files = /Thumbs.db/.DS_Store/._.DS_Store/.apdisk/._*/
    delete veto files = yes

## influx

    docker exec -it influxdb influx -execute "CREATE DATABASE home_assistant;"
    <!-- > docker exec -it influxdb influx  -username admin -password 123admin -execute "CREATE USER admin WITH PASSWORD '123admin' WITH ALL PRIVILEGES;"
    > docker exec -it influxdb influx  -username admin -password 123admin -execute "CREATE USER homee WITH PASSWORD 'homee';"
    > docker exec -it influxdb influx  -username admin -password 123admin -execute "GRANT ALL ON home_assistant TO homee;" -->

## Z-Wave

### RASPBERRY PI

On Raspberry Pi you will need to enable the serial interface in the raspi-config tool before you can add Z-Wave to Home Assistant.

    sudo raspi-config

### Docker Compose

Allow priviliged access for docker container to get /dev/ttyACMXXX working

    priviliged: True

## UDEV

https://community.openhab.org/t/raspberry-pi-make-serial-usb-ports-persistent-via-symlinks/35847

Create a UDEV Rule:

    sudo cp config/system/99-usb-serial.rules /etc/udev/rules.d/

Add homeassistant user to the right groups:

    sudo adduser homeassistant dialout
    sudo adduser homeassistant tty
    sudo adduser homeassistant gpio
    # sudo usermod -aG gpio homeassistant

Optional: Reboot and test if symlink was created:

    ls /dev/tty*

## 433 Power Outlets

433 power outles are being controlled by MQTT events. I use [my own implementation](https://github.com/mischuh/rc433mq) for that. 
You will need an MQTT broker and two configuration files (by now). Combine it with homeassistants [MQTT Switch](https://www.home-assistant.io/components/switch.mqtt/)
and you can turn lights on an off and also have a state topic.


# Backup

Install:

    https://www.linux-tips-and-tricks.de/de/schnellstart-rbk

Config:

    sudo cp /usr/share/homeassistant/etc/backup/raspiBackup.conf /usr/local/etc/

Additional Packages

    sudo apt-get install sendemail

## FritzBox WLAN

https://community.home-assistant.io/t/control-guest-wifi-custom-component/34450/3
