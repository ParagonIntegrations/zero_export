#!/usr/bin/env bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
runfile=$parent_path/startup.sh

# Remove the crontab entry
crontab -l | grep -v "@reboot $runfile"  | crontab -