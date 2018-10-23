# -*- coding: utf-8 -*-
#! /usr/bin/python
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
import os, sys, time, json
from string import Template
from random import randint
import cps, cps_utils


NAME  = 'name'
SLOT  = 'slot'
TYPE  = 'entity-type' 
FAULT = 'fault-type'  
STATE = 'oper-status' 
TEMP  = 'temperature'
CPS_KEY     ='base-pas/temperature/'
CPS_NAME    =CPS_KEY+NAME
CPS_SLOT    =CPS_KEY+SLOT
CPS_TYPE    =CPS_KEY+TYPE
CPS_FAULT   =CPS_KEY+FAULT
CPS_STATE   =CPS_KEY+STATE
CPS_TEMP    =CPS_KEY+TEMP

def entityTypeToString(eType):
    return {1: "PSU", 2: "Fan tray", 3: "Card"}.get(eType, 'Unknown')
def opStatusToString(oType):
    return {1: 'Up', 2: 'Down', 3: 'Testing', 4: 'Unknown', 5: 'Dormant', 
            6: 'Not present', 7: 'Lower layer down', 8: 'Fail'}.get(oType, 'Unknown')
#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        self.scrTemp = Template(open(os.path.join(temppath,'thermal_script.xhtml')).read())
        self.style          = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name           ='temp'
        self.postalarm      = True
        self.plugType       = 'dial'
        self.defaultLimit   = 40.0
        self.tempLimit      = 0
        self.vsize          = vsize
        self.hsize          = hsize
        self.caption        = 'Temp'
        self.sub_caption    = "[C]"
        self.lowLimit       = 0
        self.upLimit        = 60
        self.unit           ='C'
        self.fillColor      = '#008ee4'
        self.limit          = 0
        self.tempData       = 0
        self.data           = 0
        self.exeCmd         = exeCmd
        self.pMem           = 0
        self.threshold      = self.tempLimit
        self.pullRate       = 30
        self.timechk        = 0
        self.cpsTempData    = []
        self.temp_enabled = True
        self.configFile = configFile
        self.configs    = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.all_thresholds = {}
        self.all_temps = {}
        self.getConfigData()
        self.getData(self.tempLimit)

    def getConfigData(self):
        res=False
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
                    self.all_thresholds[i.get('sensor')] = max_thres
                    res = True
        elif os.path.exists(self.configFile):
            file=open(self.configFile, 'r')
            data = file.read()
            file.close()
            for l in data.splitlines():
                if not l.strip().startswith('#') and '=' in l:
                    k,v = l.split('=')
                    if k in self.configs:
                        if v.isdigit() or v in ['True','False']:
                            exec('self.%s=%s' % (k,v))
                        else:
                            exec('self.%s="%s"' % (k,v))
                        res=True
        self.threshold = self.tempLimit

        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.temp_enabled == False:
            return
        cpsData=[]
        cps.get([cps.key_from_name('observed','base-pas/temperature')], cpsData)
        def temp_sensor_print(tempData):
            tempSensor={}
            tempSensor[NAME]    = str(cps_utils.cps_attr_types_map.from_data(CPS_NAME, tempData[CPS_NAME]))
            tempSensor[TYPE]    = entityTypeToString(cps_utils.cps_attr_types_map.from_data(CPS_TYPE, tempData[CPS_TYPE]))
            tempSensor[SLOT]    = str(cps_utils.cps_attr_types_map.from_data(CPS_SLOT, tempData[CPS_SLOT]))
            tempSensor[STATE]   = opStatusToString(cps_utils.cps_attr_types_map.from_data(CPS_STATE, tempData[CPS_STATE]))
            tempSensor[FAULT]   = cps_utils.cps_attr_types_map.from_data(CPS_FAULT, tempData[CPS_FAULT])
            tempSensor[TEMP]    = int(cps_utils.cps_attr_types_map.from_data(CPS_TEMP, tempData[CPS_TEMP])) if tempSensor[FAULT] not in [3,7] else 0
            return tempSensor
        
        localTempData = []
        for s in cpsData:
            localTempData.append(temp_sensor_print(s['data']))

        temps=[]
        init_flag = False
        alarm_flag = False
        for sens in localTempData:
            temps.append(sens[TEMP])
            self.all_temps[sens[NAME]] = sens[TEMP]
            if sens[NAME] in self.all_thresholds:
                if alarm_flag:
                    continue
                if "NPU" in sens[NAME] or init_flag == False or self.all_thresholds.get(sens[NAME]) < sens[TEMP]:
                    self.threshold = self.all_thresholds.get(sens[NAME])
                    self.data = sens[TEMP]
                    init_flag = True
                if self.all_thresholds.get(sens[NAME]) < sens[TEMP]:
                    alarm_flag = True

        self.cpsTempData = localTempData
        if self.data == 0:
            if len(temps) == 0:
                self.temp_enabled=False
                return
            self.data = max(temps)
            self.threshold = self.data
        self.tempLimit = self.threshold
        self.defaultLimit = self.threshold
        self.timechk = time.time()

    def getScripts(self):
        return self.scrTemp.substitute(dict(name=self.name, 
                                       vsize=self.vsize,
                                       hsize=self.hsize,
                                       caption=self.caption,
                                       sub_caption=self.sub_caption,
                                       lowLimit=self.lowLimit,
                                       upLimit=self.upLimit,
                                       fillColor=self.fillColor,
                                       refresh=self.pullRate,
                                       limit='tempLimit',
                                       value='tempValue',
                                       ))


    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">TEMP CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getHtmlDetail(self):
        self.getConfigData()
        allData = '''
            <html><head>%s<title>Tempreture Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Tempreture Information</span><br>
            <table class="main-table" border="1">
            <tr class="main-table-hdr">
        ''' % self.style
        allData+='<td>Sensor</td><td>Type</td><td>Slot</td><td>OpState</td><td>Fault</td><td>Temp [C]</td><tr>'
        for d in self.cpsTempData:                
            allData+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><tr>\n' % (d.get(NAME),
                        d.get(TYPE), d.get(SLOT), d.get(STATE), d.get(FAULT), d.get(TEMP))
        allData+='''
            </table>
            <table class="main-table" border="1">
            <tr><td>Highest Temp</td><td class="main-table-td-c">%s%s</td></tr>
            <tr><td>Alarm State</td><td class="main-table-td-c">%s</td></tr>
            </table><br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>Tempreture Threshold (%s):</td><td><input name="powerLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="temp_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="temp_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.data, self.unit, ['OK',"ALARM"][int(self.data > self.tempLimit)], self.unit, self.tempLimit,
                   'checked="checked"' if self.temp_enabled == True else '',
                   'checked="checked"' if self.temp_enabled == False else '')
        return allData

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = {'STATUS'      : ['ALARM','CLEAR'][int(self.data > self.threshold)],
                   'THRESHOLDS'  : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : self.data,
                   'DATA'        : self.cpsTempData,
                   }
        return json.dumps(jsonMsg)

    def getAlarm(self, threshold):
        if self.temp_enabled == False:
            return False,0
        if time.time() - self.timechk > self.pullRate:
            self.getData(threshold)
        #return Alarm (True/False), Value
        return self.data > self.threshold, self.data

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'TEMP: Load: %s\n' % (self.data)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.data > self.threshold)],
                                                                             self.data, self.threshold)
        return detailMsg

    def getInfo(self):
        return "Sensor represents temperature, the default threshold for fault trigger is " + str(self.defaultLimit)


