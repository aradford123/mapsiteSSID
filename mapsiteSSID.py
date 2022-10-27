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

#FMTSTR="{:50s}{:30s}{}"
FMTSTR="{}:{}:{}"
class TaskTimeoutError(Exception):
    pass

class TaskError(Exception):
    pass

def format_time(secs):
    fmt = "%Y-%m-%d %H:%M:%S"
    timestr = strftime(fmt,localtime(secs))
    return timestr

def print_site(sitestr, profile):
    ssid = ",".join([ssid['name'] for ssid in profile.profileDetails.ssidDetails if 'name' in ssid])
    name = profile.profileDetails.name
    for site in profile.profileDetails.sites:
        if sitestr is None or sitestr in site:
            print(FMTSTR.format(site,name,ssid))

def match_sites(sitestr, sitelist):
    if sitestr is None:
        return True
    matches = [site  for site in sitelist if sitestr in site]
    return True if matches != [] else False

def build_profile_cache(dnac):
    # this is for version 2.2.2.x where the get for wireless profile is broken.  Can only do a get for a named profile
    profiles = dnac.custom_caller.call_api(method="GET", resource_path="api/v1/siteprofile/attribute?key=wireless.ssid")
    #result = [profile['name'] for profile in profiles['response']]
    #print(profiles)
    result = [profile['siteProfileUuid'] for profile in profiles['response']]
    return result

class ProfileDetails:
    def __init__(self,name, sites, ssid):
        self.name = name
        self.sites = sites
        self.ssidDetails = ssid
class Profile:
    def __init__(self, details):
        self.profileDetails = details

def map_site_id_to_name(dnac, siteid):
    response = dnac.sites.get_site(siteId=siteid)
    return response.response.siteNameHierarchy

def get_internal_profile(dnac,profileid):
    # using this as the wireless_profile API is rate limited to 5/min
    profile = dnac.custom_caller.call_api(method="GET", resource_path="api/v1/siteprofile/{}?includeSites=true&excludeSettings=true&populated=true".format(profileid))
    p = profile.response
    ssid = [ {'name': s['value']} for s in p.profileAttributes if s['value'] is not None ]
    
    #sites = [site['name'] for site in p.sites]
    # convert site id to name to get Fully qualified site name
    if p.sites:
        sites = [map_site_id_to_name(dnac, site['uuid']) for site in p.sites]
    else:
        sites = []
    p = Profile(ProfileDetails(p.name, sites, ssid))
    return p 

def get_profiles(dnac):
    profileids = build_profile_cache(dnac)
    profiles=[]
    for profileid in profileids:
        #profile = dnac.wireless.get_wireless_profile(profileName=profilename)
        profile = get_internal_profile(dnac,profileid)
    
        profiles.append(profile)
    return profiles
        
def main(dnac,sitestr):
    try:
#         raise ValueError("as")
         profiles = dnac.wireless.get_wireless_profile()
    except ApiError:
#    except ValueError:
         profiles = get_profiles(dnac)
    print(FMTSTR.format("site","profilename","ssid"))
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

