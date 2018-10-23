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

