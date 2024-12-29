#!/usr/bin/sh

# Check to see if compatible with HomeAssistant

set -e

# Check the latest supported version
echo "Default supported version"
poetry add homeassistant --dry-run | grep -Po "\s+homeassistant\s+\((\d+\.\d+\.\d+\))"

# Check target versions
for ver in "$@"
do
    poetry add homeassistant==$ver --dry-run
    echo "$ver is supported"
done