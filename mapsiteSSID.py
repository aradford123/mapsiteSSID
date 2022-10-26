#!/usr/bin/env python
import requests
from argparse import ArgumentParser
from dnacentersdk import api
from dnacentersdk.exceptions import ApiError
import logging
import csv
import json
from  time import sleep, time, strftime, localtime
from dnac_config import DNAC, DNAC_USER, DNAC_PASSWORD
logger = logging.getLogger(__name__)

class TaskTimeoutError(Exception):
    pass

class TaskError(Exception):
    pass

def format_time(secs):
    fmt = "%Y-%m-%d %H:%M:%S"
    timestr = strftime(fmt,localtime(secs))
    return timestr

def print_site(sitestr, profile):
    #print(profile)
    ssid = ",".join([ssid.name for ssid in profile.profileDetails.ssidDetails if 'name' in ssid])
    for site in profile.profileDetails.sites:
        if sitestr is None or sitestr in site:
            print("{}:{}".format(site,ssid))

def match_sites(sitestr, sitelist):
    if sitestr is None:
        return True
    matches = [site  for site in sitelist if sitestr in site]
    return True if matches != [] else False

def main(dnac,sitestr):
    profiles = dnac.wireless.get_wireless_profile()
    for profile in profiles:
        if sitestr or match_sites(sitestr, profile.profileDetails.sites):
             print_site(sitestr, profile)

if __name__ == "__main__":
    parser = ArgumentParser(description='Select options.')
    parser.add_argument('-v', action='store_true',
                        help="verbose")
    parser.add_argument('--sitestr',  type=str,
                        help='site string to match')
    args = parser.parse_args()

    if args.v:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.debug("logging enabled")
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    dnac = api.DNACenterAPI(base_url='https://{}:443'.format(DNAC),
                                username=DNAC_USER,password=DNAC_PASSWORD,verify=False,debug=True)

    main(dnac, args.sitestr)

