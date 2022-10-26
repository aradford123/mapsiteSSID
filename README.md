# mapsiteSSID
maps sites to SSID defined in Wireless Network profiles on Cisco DNA Center

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
Global/AUS/PER5/F4:dot1x,9800,BCN
Global/AUS/PER5:dot1x,9800,BCN
Global/AUS/PER6:dot1x,9800,BCN
Global/AUS/PER6/f1:dot1x,9800,BCN
Global/brownfield/coogee beach/f1:
Global/brownfield/coogee beach:
Global/AUS/Perth site:9800
Global/AUS/Perth site/floor one:9800
Global/flex_area/b1:hk
Global/flex_area/b1/f1:hk

```

use the --sitestr argument to provide a string to match against the site name

```
$ ./mapsiteSSID.py --sitestr AUS/PER
Global/AUS/PER5/F4:dot1x,9800,BCN
Global/AUS/PER5:dot1x,9800,BCN
Global/AUS/PER6:dot1x,9800,BCN
Global/AUS/PER6/f1:dot1x,9800,BCN
```
