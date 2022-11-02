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
#    profiles = dnac.custom_caller.call_api(method="GET", resource_path="api/v1/siteprofile/attribute?key=wireless.ssid")
    profiles = dnac.custom_caller.call_api(method="GET", resource_path="api/v1/siteprofile?namespace=wlan")
    #result = [profile['name'] for profile in profiles['response']]
    #print(json.dumps(profiles))
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


# dont use this as it breaks with
def map_site_id_to_name(dnac, siteid):
    response = dnac.sites.get_site(siteId=siteid)
    return response.response.siteNameHierarchy

LIMIT = 500
#LIMIT = 10
class SiteCache:
    def __init__(self, dnac):
        self._cache = {}
        self.dnac = dnac
        response = dnac.sites.get_site_count()
        count = response.response
        logger.debug ("COUNT:{}".format(count))

        for start in range(1, count+1, LIMIT):
            #response = get_url("group?groupType=SITE&offset={}&limit={}".format(start,LIMIT))
            response = dnac.sites.get_site(offset=str(start),limit=str(LIMIT))

            sites = response['response']
            for s in sites:
                logger.debug("Caching {}".format(s.siteNameHierarchy))
                self._cache[s.id] = s.siteNameHierarchy

        logger.debug("cache size is {}".format(len(self._cache)))
    def lookup_by_id(self, siteid):
        logger.debug("looking up {}".format(siteid))
        if siteid in self._cache:
            return self._cache[siteid]
        else:
            raise ValueError("Cannot find site:{}".format(siteid))


def get_internal_profile(dnac,sitecache,profileid):
    # using this as the wireless_profile API is rate limited to 5/min
    profile = dnac.custom_caller.call_api(method="GET", resource_path="api/v1/siteprofile/{}?includeSites=true&excludeSettings=true&populated=true".format(profileid))
    p = profile.response
    if 'profileAttributes' in p:
        ssid = [ {'name': s['value']} for s in p.profileAttributes if s['value'] is not None ]
    else:
        ssid = []
    
    #sites = [site['name'] for site in p.sites]
    # convert site id to name to get Fully qualified site name
    if p.sites:
        #sites = [map_site_id_to_name(dnac, site['uuid']) for site in p.sites]
        sites = [sitecache.lookup_by_id(site['uuid']) for site in p.sites]
    else:
        sites = []
    p = Profile(ProfileDetails(p.name, sites, ssid))
    return p 

def get_profiles(dnac):
    sitecache = SiteCache(dnac)
    profileids = build_profile_cache(dnac)
    profiles=[]
    for profileid in profileids:
        #profile = dnac.wireless.get_wireless_profile(profileName=profilename)
        profile = get_internal_profile(dnac, sitecache, profileid)
    
        profiles.append(profile)
    return profiles
        
def collect_sites(dnac):
    try:
         #raise ValueError("as")
         profiles = dnac.wireless.get_wireless_profile()
    except ApiError:
#    except ValueError:
         profiles = get_profiles(dnac)
    return profiles

def print_profiles(profiles, sitestr):
    print(FMTSTR.format("site","profilename","ssid"))
    for profile in profiles:
        if sitestr or match_sites(sitestr, profile.profileDetails.sites):
             print_site(sitestr, profile)

def get_wlc_id(dnac, wlcip):
    try:
        response = dnac.devices.get_network_device_by_ip(ip_address=wlcip)
    except ApiError as e:
        print("Device {} not found".format(ip))
        sys.exit(1)
    return response.response.id

def get_wlc_site_list(dnac, wlcid):
    sitelist=[]
    LIMIT = 2
    # response = dnac.sites.get_site_count()
    url = "api/v1/group/count?groupType=SITE&additionalInfo.nameSpace=com.wireless.managingwlc&additionalInfo.attributes.primaryWlc={}".format(wlcid)
    response = dnac.custom_caller.call_api(method="GET", resource_path=url)
    count = response.response
    logger.debug ("COUNT:{}".format(count))

    for start in range(1, count+1, LIMIT):
    #response = dnac.sites.get_site(offset=str(start),limit=str(LIMIT))
        url="/api/v1/group?groupType=SITE&additionalInfo.nameSpace=com.wireless.managingwlc&additionalInfo.attributes.primaryWlc={}&limit={}&offset={}".format(wlcid,LIMIT,start)
        response = dnac.custom_caller.call_api(method="GET", resource_path=url)

        sites = [ site.groupNameHierarchy for site in response['response']]
        sitelist.extend(sites)
    return sitelist
def match_sites_to_profiles(profiles, sitelist):
    site_to_profile = {s: p.profileDetails.name for p in profiles for s in p.profileDetails.sites}
    #profilelist = [ site_to_profile[site] for site in sitelist]
    profilelist = []
    for site in sitelist:
        if not site in site_to_profile:
            print("Error: site {} defined on WLC but not assigned to a profile".format(site))
        else:
            profilelist.append(site_to_profile[site])
    return set(profilelist)
    
def map_wlc_to_profiles(dnac, profiles, wlcip):
    wlcid = get_wlc_id(dnac, wlcip)
    logger.debug("wlcid:{}".format(wlcid))
    sitelist = get_wlc_site_list(dnac, wlcid)
    profilelist = match_sites_to_profiles(profiles, sitelist)
    print("{}:{}".format(wlcip,profilelist))

def wlc_to_profile(dnac, wlcip):
    profiles = collect_sites(dnac)
    map_wlc_to_profiles(dnac,profiles, wlcip)
    
def sitematch(dnac, sitestr):
    profiles = collect_sites(dnac)
    print_profiles(profiles, sitestr)


if __name__ == "__main__":
    parser = ArgumentParser(description='Select options.')
    parser.add_argument('-v', action='store_true',
                        help="verbose")
    parser.add_argument('--sitestr',  type=str,
                        help='site string to match')
    parser.add_argument('--wlcip',  type=str,
                        help='show wireless profiles for WLC with this ip')
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
                                #username=DNAC_USER,password=DNAC_PASSWORD,verify=False,debug=True)
                                username=DNAC_USER,password=DNAC_PASSWORD,verify=False)
    if args.wlcip:
        wlc_to_profile(dnac, args.wlcip)
    else:
        sitematch(dnac, args.sitestr)

