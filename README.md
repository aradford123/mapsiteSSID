# mapsiteSSID
This script will display mappings between sites/wireless profiles/SSID in environments configured by Cisco DNA Center.  It also shows the mapping between a 9800 WLC and the network profiles it is using.

## Getting stated
First (optional) step, create a vitualenv. This makes it less likely to clash with other python libraries in future.
Once the virtualenv is created, need to activate it.
```buildoutcfg
python3 -m venv env3
source env3/bin/activate
```

Next clone the code.

```buildoutcfg
git clone https://github.com/aradford123/mapsiteSSID.git
```

Then install the  requirements (after upgrading pip). 
Older versions of pip may not install the requirements correctly.
```buildoutcfg
pip install -U pip
pip install -r requirements.txt
```

Edit the dnac_vars file to add your DNAC and credential.  You can also use environment variables.

## Running the program

if you run without any arguments, all sites and SSID will be displayed (including sites with a profile that has no SSID).

```
./mapsiteSSID.py   
site:profilename:ssid
Global/AUS/PER5/F4:9800:dot1x,9800,BCN
Global/AUS/PER5:9800:dot1x,9800,BCN
Global/AUS/PER6:9800:dot1x,9800,BCN
Global/AUS/PER6/f1:9800:dot1x,9800,BCN
Global/brownfield/coogee beach/f1:BrownfieldProfile_7:
Global/brownfield/coogee beach:BrownfieldProfile_7:
Global/flex_area/b1:flex profile:hk
Global/flex_area/b1/f1:flex profile:hk
Global/flex_area:flex profile:hk

```

use the --sitestr argument to provide a string to match against the site name

```
./mapsiteSSID.py  --sitestr AUS/PER
site:profilename:ssid
Global/AUS/PER5/F4:9800:dot1x,9800,BCN
Global/AUS/PER5:9800:dot1x,9800,BCN
Global/AUS/PER6:9800:dot1x,9800,BCN
Global/AUS/PER6/f1:9800:dot1x,9800,BCN
```

To find the profiles that have sites attached to a particular WLC use the --wlcip argument.

This example shows a controller that had a site mapped to it and configured, that was subsequently removed from the Network Profile

```
./mapsiteSSID.py  --wlcip 192.168.200.201
Error: site Global/AUS/Perth site defined on WLC but not assigned to a profile
Error: site Global/AUS/Perth site/floor one defined on WLC but not assigned to a profile
192.168.200.201:{'VerySecure', '9800'}

```
