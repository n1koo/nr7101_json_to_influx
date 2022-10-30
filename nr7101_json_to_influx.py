from influxdb import InfluxDBClient
import json
import os
import sys
import argparse
import logging
import coloredlogs
from datetime import datetime


log = logging.getLogger("nr7101_json_to_influx")
LOGLEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=LOGLEVEL,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)])
coloredlogs.install(isatty=True, level=LOGLEVEL)


def _parse_args():
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description='Bridge between nr7101 sensor output json and InfluxDB')
    parser.add_argument(
        '--input_json_file', help='Location of the file to be parsed for data', default='telia.json', type=str)
    parser.add_argument('--influx_db_host', help='influx db host address',
                        default='127.0.0.1', type=str)
    parser.add_argument('--influx_db_port', help='influx db host port',
                        default=8086, type=int)
    parser.add_argument('--influx_db_database', help='influx db database name (eg default)',
                        default="nr7101", type=str)
    parser.add_argument('--influx_db_user', help='influx db user',
                        default="nr7101", type=str)
    parser.add_argument('--influx_db_password', help='influx db password',
                        default="nr7101", type=str)
    parser.add_argument('--dry-run', help='Output to console rather than sending to influx',
                        default=False, type=bool)
    parser.add_argument('--isp_name', help='Optional isp name to use as tag', type=str)
    args = parser.parse_args()
    return args


def _get_parsed_entry(measurement, value, tags, timestamp):
    return {"measurement": measurement,
            "tags": tags,
            "time": timestamp,
            "fields": {
                "value": value},
            }


def _parse_json(json_file: str, isp_name) -> dict:
    parsed_data = []
    with open(json_file, 'r', encoding='UTF-8') as input_json:
        data = json.load(input_json)
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        if isp_name:
            tags = {"isp_name": isp_name}
        else:
            tags = {}

        for k, v in data.items():
            if k == 'traffic':
                continue
            if isinstance(v, dict):
                items = v.items()
                for k, v in items:
                    if k == 'NBR_Info':
                        continue
                    if k == 'SCC_Info' and isinstance(v, list):
                        for band in v:
                            band_tags = tags | ({"band": band['Band'],
                                                "PhysicalCellID": band['PhysicalCellID'],
                                                 "RFCN": band['RFCN']})

                            parsed_data.append({"measurement": "SCC_Info",
                                                "tags": band_tags,
                                                "time": timestamp,
                                                "fields": {
                                                    "RSSI": band['RSSI'],
                                                    "RSRP": band['RSRP'],
                                                    "RSRQ": band['RSRQ'],
                                                    "SINR": band['SINR'],
                                                    "CA_STATE": band['CA_STATE']
                                                }})
                    else:
                        parsed_data.append(_get_parsed_entry(k, v, tags, timestamp))
            else:
                log.warning("Skipped$ %s", v)

    # validate
    _ = json.JSONEncoder().encode(parsed_data)
    return parsed_data


def main():
    log.info("Starting nr7101 json to Influx script")
    args = _parse_args()
    data = _parse_json(args.input_json_file, args.isp_name)
    log.debug(data)

    influx_client = InfluxDBClient(host=args.influx_db_host, port=args.influx_db_port, database=args.influx_db_database,
                                   username=args.influx_db_user, password=args.influx_db_password, timeout=3)
    if args.dry_run:
        log.info(json.dumps(data, indent=4))
    else:
        influx_client.write_points(data)


if __name__ == '__main__':
    main()
