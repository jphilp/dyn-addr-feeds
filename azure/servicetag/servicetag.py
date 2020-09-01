#!/usr/bin/python3

import os
import sys
import json

from jnpr.junos import Device
from jnpr.junos.utils.config import Config

test_srx = '172.16.100.225'
test_user = 'jphilp'
test_password = 'Juniper123'

locations = ["NorthCentralUS","SouthCentralUS" ]
feedname = 'ServiceTags_Public_20200810.json'
feed_server = 'AZURE'
feed_url = 'raw.githubusercontent.com/jphilp/dyn-addr-feeds/master/azure/servicetag'
feed_update_interval = 1800
feed_hold_interval = 864000
feed_names = []
feed_addresses = []


with open(os.path.join(sys.path[0], feedname), "r") as read_file:
    feed = json.load(read_file)


for servicetag in feed['values'] :
    if any((loc in servicetag['name'] or '.' not in servicetag['name']) for loc in locations):
        service = servicetag['name'].split(".")
        if len( service ) == 1 : service.append( "Global" )
        feed_names.append({ 'name' : service[1] + "-" + service[0]+"-ipv4", 'path' : service[1] + "/" + service[0] + "/ipv4", 'update-interval' : feed_update_interval, 'hold-interval' : feed_hold_interval })
        feed_addresses.append({ 'name' : "DYN-" + feed_server + "-" + service[1] + "-" + service[0]+"-ipv4", 'profile' : { 'feed-name' : [ { 'name' : service[1] + "-" + service[0]+"-ipv4"} ] } })
        os.makedirs(os.path.join(sys.path[0], service[1], service[0]), exist_ok=True)
        with open(os.path.join(sys.path[0], service[1], service[0] + "\ipv4"), "w+") as f:
            for ipaddress in servicetag['properties']['addressPrefixes'] :
                f.writelines(ipaddress + "\n")

config_candidate = { 'configuration' : { 'security' : { 'dynamic-address' : { 'feed-server' : [ { 'name' : feed_server, 'url' : feed_url, 'feed-name' : feed_names } ], 'address-name': feed_addresses } } } }

# print(json.dumps(config_candidate, indent=4))

dev = Device(test_srx, user=test_user, password=test_password).open()
with Config(dev, mode='exclusive') as cu:  
    cu.load(json.dumps(config_candidate), format='json')
    cu.pdiff()
    cu.commit()
dev.close()
