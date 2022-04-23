#!/bin/bash
# Helpful script to automatically reverse the effects of install.sh

echo "Now removing OctoClock service. Configuration and settings will be deleted from /etc/octoclock."

rm -r /etc/octoclock

rm /usr/sbin/octoclock

systemctl stop octoclock
systemctl disable octoclock

rm /etc/systemd/system/octoclock.service

echo "OctoClock service successfully removed"
