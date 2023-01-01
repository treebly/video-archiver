#!/bin/sh
set -e

shortcuts run "Get Download IDs"
if [[ ! -e $1 ]]; then
	exit 0
fi
./archive.py -n --log-path other.log -f $1
shortcuts run "Clear Download IDs" -i $1
rm $1