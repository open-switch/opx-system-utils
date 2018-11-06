# Copyright (c) 2018 Dell Inc.
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

import pytest
import sys_status
import json
import sys_status
import os

sensor = "temp"

def test_sensor_fault_state():
    retDict = sys_status.get_sensor(sensor)
    if retDict != None:
        if retDict['fault-state'] != None and retDict['value'] != None and retDict['threshold'] != None:
            return (retDict['value'] > retDict['threshold']) == retDict['fault-state']
    return False
def test_config_file():
    retDict = sys_status.get_sensor(sensor)        
    if retDict != None and retDict['threshold'] != None:
        thres = retDict['threshold']
        json_config = '/etc/opt/dell/os10/env-tmpctl/config.json'
        if os.path.exists(json_config):
            file = open(json_config, "rb")
            data = json.load(file)
            file.close()
            for i in data['faults']:
                if i.get('sensor') and i.get('thresholds'):
                    max_thres = 0
                    for j in i.get('thresholds'):
                        if j.get('hi'):
                            max_thres = max(max_thres, j.get('hi'))
                    if max_thres == thres:
                        return True
            
    return False

def test_answer():
    assert test_sensor_fault_state()
    assert test_config_file()

