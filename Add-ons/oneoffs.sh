#!/bin/sh
set -e

shortcuts run "Get Download IDs"
if [[ ! -e ids.txt ]]; then
	exit 0
fi
./archive.py -n --log-path other.log -f ids.txt
shortcuts run "Clear Download IDs" -i ids.txt
rm ids.txt