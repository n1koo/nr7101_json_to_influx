#!/bin/bash

set -e

for name in nr7101_USERNAME nr7101_PASSWORD INFLUX_DB_HOST INFLUX_DB_DATABASE INFLUX_DB_USER INFLUX_DB_PASSWORD; do
    if [[ -z "${!name}" ]]; then
        echo "Variable $name not set!"
        exit 1
    fi
done

i=0
for ISP_NAME in telia elisa tele2; do
    ((i = i + 1))
    nr7101_IP=192.168.1.$i

    nr7101-tool https://$nr7101_IP $nr7101_USERNAME $nr7101_PASSWORD >$ISP_NAME.json
    python3 ./nr7101_json_to_influx.py --influx_db_host $INFLUX_DB_HOST --influx_db_database $INFLUX_DB_DATABASE --influx_db_user $INFLUX_DB_USER --influx_db_password $INFLUX_DB_PASSWORD --isp_name $ISP_NAME --input_json_file $ISP_NAME.json
done
