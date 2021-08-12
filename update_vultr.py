#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------------------------------------------- #
"""
 Update Vultr API Settings

"""
# Library imports ---------------------------------------------------------------------------------------------------- #
from pathlib import Path
import argparse
import configparser
import json
import logging.handlers
import os
import requests
import sys

# Set some defaults -------------------------------------------------------------------------------------------------- #
CONFIG_FILE = Path(__file__).parent / 'vultr.ini'


# Functions ---------------------------------------------------------------------------------------------------------- #
def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-L', '--log-level', default='INFO', help='Set the log level (default is INFO)',
                        type=str.upper, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-c', '--config', default=CONFIG_FILE, type=argparse.FileType('r'),
                        help="Path to config file (default is {})".format(CONFIG_FILE))

    return parser.parse_args()


# -------------------------------------------------------------------------------------------------------------------- #
def setup_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(log_level))

    # Suppress less than WARNING level messages for the request module
    logging.getLogger("requests").setLevel(logging.WARNING)

    # Default logging format
    log_format = '[%(filename)s:%(funcName)s]: %(levelname)s - %(message)s'

    # Write to syslog
    syslog_address = '/dev/log'
    if sys.platform == 'darwin':
        syslog_address = '/var/run/syslog'
    sh = logging.handlers.SysLogHandler(address=syslog_address)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter(log_format))

    # Also log to the console (stderr by default)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(asctime)s ' + log_format))

    logging.basicConfig(level=numeric_level, handlers=[sh, ch])


# -------------------------------------------------------------------------------------------------------------------- #
def get_ip(endpoint):
    r = requests.get(endpoint)
    if r.status_code != 200 and r.status_code != 201:
        logging.debug('Unable to get public IP, Error {}: {}'.format(r.status_code, r.text))
        return None
    else:
        return r.text


# -------------------------------------------------------------------------------------------------------------------- #
def get_fw_groups(opts):
    endpoint = '{}/firewalls'.format(opts.get('base_url'))

    r = requests.get(endpoint, headers=json.loads(opts.get('headers')))
    if r.status_code != 200 and r.status_code != 201:
        logging.debug('Unable to list firewall groups, Error {}: {}'.format(r.status_code, r.text))
        return None
    else:
        return r.json().get('firewall_groups')


# -------------------------------------------------------------------------------------------------------------------- #
def get_fw_rules(gid, opts):
    endpoint = '{}/firewalls/{}/rules'.format(opts.get('base_url'), gid)

    r = requests.get(endpoint, headers=json.loads(opts.get('headers')))
    if r.status_code != 200 and r.status_code != 201:
        logging.debug('Unable to list firewall rules, Error {}: {}'.format(r.status_code, r.text))
        return None
    else:
        return r.json().get('firewall_rules')


# -------------------------------------------------------------------------------------------------------------------- #
def del_fw_rule(gid, rid, opts):
    endpoint = '{}/firewalls/{}/rules/{}'.format(opts.get('base_url'), gid, rid)

    r = requests.delete(endpoint, headers=json.loads(opts.get('headers')))
    if r.status_code != 200 and r.status_code != 204:
        logging.debug('Unable to delete firewall rule, Error {}: {}'.format(r.status_code, r.text))

    return None


# -------------------------------------------------------------------------------------------------------------------- #
def add_fw_rule(gid, ip, opts):
    endpoint = '{}/firewalls/{}/rules'.format(opts.get('base_url'), gid)
    data = {
        "ip_type": opts.get('ip_type'),
        "protocol": opts.get('protocol'),
        "port": opts.get('port'),
        "subnet": ip,
        "subnet_size": 32,
        "source": "",
        "notes": opts.get('tag')
    }

    r = requests.post(endpoint, json=data, headers=json.loads(opts.get('headers')))
    if r.status_code != 200 and r.status_code != 201:
        logging.debug('Unable to create firewall rule, Error {}: {}'.format(r.status_code, r.text))

    return None


# main --------------------------------------------------------------------------------------------------------------- #
def main():
    args = parse_args()
    setup_logging(args.log_level)

    if os.path.isfile(args.config):
        config = configparser.ConfigParser()
        config.read(args.config)
        opts = config['main']
        opts['headers'] = json.dumps({"Authorization": "Bearer {}".format(opts.get('api_key'))})
        opts['ip'] = get_ip(opts.get('public_ip_url'))
    else:
        logging.critical("Config file `{}` doesn't exist!".format(args.config))
        sys.exit(1)

    # list of all firewall group ids
    gids = [x.get('id') for x in get_fw_groups(opts)]

    # list of firewall rules matching tag (note)
    rules = [dict(x, **{'gid': i}) for i in gids for x in get_fw_rules(i, opts) if x.get('notes') == opts.get('tag')]

    if len(rules) == 0:
        logging.info('No existing rules found, adding one for "{}".'.format(opts.get('ip')))
        for gid in gids:
            add_fw_rule(gid, opts.get('ip'), opts)
    else:
        for rule in rules:
            fwip = rule.get('subnet')
            if rule.get('subnet') == opts.get('ip'):
                logging.info('Found existing rule for "{}", no update is required.'.format(fwip))
            else:
                logging.info('Replacing rule for "{}" w/ "{}".'.format(fwip, opts.get('ip')))
                del_fw_rule(rule.get('gid'), rule.get('id'), opts)
                add_fw_rule(rule.get('gid'), opts.get('ip'), opts)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info('Interrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

# -------------------------------------------------------------------------------------------------------------------- #
