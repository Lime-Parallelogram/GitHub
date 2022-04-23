#!/bin/bash
# Helpful script to install service files and place python script in the /usr/sbin directory

echo "Installing OctoClock service to '/usr/sbin'. Configuration and settings must now be edited in /etc/octoclock."

mkdir -p /etc/octoclock

cp -r config/* /etc/octoclock
cp -r clock.py /usr/sbin/octoclock
sed -i 's/CONFIG_DIR = "config\/"/CONFIG_DIR = "\/etc\/octoclock\/"/g' /usr/sbin/octoclock

cp -r octoclock.service /etc/systemd/system/

systemctl enable octoclock
systemctl start octoclock

echo "OctoClock service is now installed and running. Manipulate it using normal systemctl operations such as 'sudo systemctl status octoclock'"