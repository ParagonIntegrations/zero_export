#!/usr/bin/env bash

# sleep to allow the system to boot before initiating
sleep 60

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd $parent_path
runfile=$parent_path/main.py
python $runfile &
