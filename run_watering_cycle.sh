#!/bin/bash

load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
}

load_env

# Get API URL from environment variable, with fallback to .env file
SOLENOID_CONTROLLER_HOST=${SOLENOID_CONTROLLER_HOST:-$(grep SOLENOID_CONTROLLER_HOST .env 2>/dev/null | cut -d '=' -f2)}

# Check if SOLENOID_CONTROLLER_HOST is set
if [ -z "$SOLENOID_CONTROLLER_HOST" ]; then
    echo "Error: SOLENOID_CONTROLLER_HOST is not set. Please set it in your environment or in a .env file."
    exit 1
fi

# JSON data to send
JSON_DATA='{"solenoidState": true}'

# Perform the curl POST request
curl -X POST \
     -H "Content-Type: application/json" \
     -d "$JSON_DATA" \
     "${SOLENOID_CONTROLLER_HOST}/control"

if [ $? -eq 0 ]; then
    echo "Watering cycle triggered successfully."
    echo "`date`" >> ~/watering.log
else
    echo "Failed to trigger watering cycle. Please check your API endpoint and try again."
fi
