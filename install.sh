#!/usr/bin/env bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
runfile=$parent_path/startup.sh
settingsfile=$parent_path/settings.py
defaultsettingsfile=$parent_path/settings_default.py

# Create the settingsfile from the default one if it doesn't exist
if [ -f "$settingsfile" ]; then
    echo "$settingsfile exists."
else
    cp $defaultsettingsfile $settingsfile
fi

# Fix permissions for the runfile
chmod 755 $runfile

# Add the runfile to the crontab
! (crontab -l | grep -q "$runfile") && (crontab -l; echo "@reboot $runfile") | crontab -