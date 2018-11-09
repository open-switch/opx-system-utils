#!/usr/bin/python
#
# Copyright (c) 2017 Dell Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
# FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.
#

import cps
import cps_object
import event_log as ev
import sys_status

import time
import systemd.daemon

STATUS_KEY='system-status/current-status'
SERVICE_TAG_KEY = 'base-pas/chassis/service-tag'

GREEN = 3
RED = 1
INIT = 0

sensor_map = {
    "cpu"   : 1,
    "disk"  : 2,
    "fan"   : 3,
    "mem"   : 4,
    "power" : 5,
    "swap"  : 6,
	"temp"  : 7
}

fault_state_map = {
    "cpu"   : None,
    "disk"  : None,
    "fan"   : None,
    "mem"   : None,
    "power" : None,
    "swap"  : None,
	"temp"  : None
}   

default_time_interval = 30
overall_status = 0

def get_node_id():
    cpsData = []
    node_id = None
    if cps.get([cps.key_from_name('observed', SERVICE_TAG_KEY)], cpsData) and len(cpsData) > 0:
        node_id = cpsData[0]['data'][SERVICE_TAG_KEY]
    return node_id

def get_status_call():
    retValue = sys_status.get_overall_status()
    if retValue == True:
        return RED 
    if retValue == False:
        return GREEN
    return INIT

# Checkout if there is any fault-state change
def check_fault_state():
    global fault_state_map
    fault_state_change = False
    cur_status = get_status_call()
    if cur_status != overall_status:
        fault_state_change = True
    for i in range(len(sensor_list)):
        _retDict = sys_status.get_sensor(sensor_list[i])
        if _retDict != None:
            if _retDict['fault-state'] != None and _retDict['fault-state'] != fault_state_map[sensor_list[i]]:
                fault_state_change = True
                fault_state_map[sensor_list[i]] = _retDict['fault-state']
    return fault_state_change


# Create CPS object for overall status
def gen_cps_obj_status():
    if check_fault_state() == False:
        return
    cur_status = get_status_call()
    _obj = cps_object.CPSObject(module=STATUS_KEY, qual='observed')
    _obj.add_attr('status', cur_status)
    _obj.add_attr('node-id',get_node_id())
    for i in range(len(sensor_list)):
        _retDict = sys_status.get_sensor(sensor_list[i])
        if _retDict != None:
            _obj.add_embed_attr(['sensor', str(i), 'name'], sensor_map[sensor_list[i]])
            _obj.add_embed_attr(['sensor', str(i), 'value-type'], 2)
            if _retDict['fault-state'] != None:
                _obj.add_embed_attr(['sensor', str(i), 'fault-state'], _retDict['fault-state'])
            if _retDict['value'] != None:
                _obj.add_embed_attr(['sensor', str(i), 'value'], str(round(_retDict['value'], 2)))
            if _retDict['threshold'] != None:
                _obj.add_embed_attr(['sensor', str(i), 'threshold'], str(round(_retDict['threshold'],2)))
            if _retDict['description'] != None:
                _obj.add_embed_attr(['sensor', str(i), 'description'],_retDict['description'])
    obj = _obj.get()
    obj['operation'] = 'set'
    # publish to db
    ev.logging('SYS_STAT', ev.DEBUG, '', 'system_status_db.py', '', 0, 'Overall system status is %d' % cur_status)
    global overall_status
    if overall_status != cur_status:
        ev.logging('SYS_STAT', ev.DEBUG, '', 'system_status_db.py', '', 0, 'Overall system status change detected: %d to %d' % (overall_status, cur_status))
        overall_status = cur_status
        cps.db_commit(obj, None, True)
    else:
        cps.db_commit(obj, None, False)

systemd.daemon.notify("READY=1")
sensor_list = sys_status.get_sensor_list()

# Wait for responses
while True: 
    gen_cps_obj_status() 
    time.sleep(default_time_interval)
