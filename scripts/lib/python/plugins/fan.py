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
import os, sys, json
from string import Template
import cps, cps_utils

NAME  = 'fan-index'
SLOT  = 'slot'
TYPE  = 'entity-type' 
FAULT = 'fault-type'  
FANID = 'fan-index'
STATE = 'oper-status' 
SPEED = 'speed'
PSPEED= 'speed_pct'

CPS_KEY     ='base-pas/fan/'
CPS_NAME    =CPS_KEY+NAME
CPS_SLOT    =CPS_KEY+SLOT
CPS_TYPE    =CPS_KEY+TYPE
CPS_FAULT   =CPS_KEY+FAULT
CPS_STATE   =CPS_KEY+STATE
CPS_SPEED   =CPS_KEY+SPEED
CPS_PSPEED  =CPS_KEY+PSPEED

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
        self.scrTemp = Template(open(os.path.join(temppath,'dial_script.xhtml')).read())
        self.style      = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name       ='fan'
        self.postalarm  = True
        self.plugType   = 'dial'
        self.defaultLimit= 3000
        self.fanLimit   = self.defaultLimit
        self.vsize      = vsize
        self.hsize      = hsize
        self.caption    = 'Fan Speed'
        self.sub_caption= 'RPM'
        self.lowLimit   = 0
        self.upLimit    = 9000
        self.refresh    = 30
        self.numsuffix  = ''
        self.unit       = 'rpm'
        self.Rmargin    = 3
        self.limit      = 0
        self.lowColor   = "e44a00"
        self.upColor    = "6baa01"
        self.data       = 0
        self.exeCmd     = exeCmd
        self.pMem       = 0
        self.threshold  = self.fanLimit
        self.fan_enabled = True
        self.configFile = configFile
        self.configs    = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData(self.fanLimit)

    def getConfigData(self):
        res=False
        if os.path.exists(self.configFile):
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
            self.threshold  = self.fanLimit
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.fan_enabled == False:
            return
        cpsData=[]
        cps.get([cps.key_from_name('observed','base-pas/fan')], cpsData)
        def fanGet(fanData):
            fanUnit={}
            fanUnit[NAME]    = str(cps_utils.cps_attr_types_map.from_data(CPS_NAME, fanData[CPS_NAME]))
            fanUnit[TYPE]    = entityTypeToString(cps_utils.cps_attr_types_map.from_data(CPS_TYPE, fanData[CPS_TYPE]))
            fanUnit[SLOT]    = str(cps_utils.cps_attr_types_map.from_data(CPS_SLOT, fanData[CPS_SLOT]))
            fanUnit[STATE]   = opStatusToString(cps_utils.cps_attr_types_map.from_data(CPS_STATE, fanData[CPS_STATE]))
            fanUnit[FAULT]   = cps_utils.cps_attr_types_map.from_data(CPS_FAULT, fanData[CPS_FAULT])
            fanUnit[PSPEED]  = int(cps_utils.cps_attr_types_map.from_data(CPS_PSPEED, fanData[CPS_PSPEED]))
            fanUnit[SPEED]   = int(cps_utils.cps_attr_types_map.from_data(CPS_SPEED, fanData[CPS_SPEED])) if fanUnit[FAULT] not in [3,7] else 0
            return fanUnit
        
        localFanData = []
        for s in cpsData:
            localFanData.append(fanGet(s['data']))

        fans=[]
        for fan in localFanData:
            fans.append(fan[SPEED])

        self.cpsFanData = localFanData
        if len(fans) > 0:
            self.data = max(fans)
        else:
            self.fan_enabled=False
            return
        if threshold is not None:
            self.threshold = threshold
        else:
            self.threshold = self.data

    def getScripts(self):
        return self.scrTemp.substitute(dict(name=self.name, 
                                       vsize=self.vsize,
                                       hsize=self.hsize,
                                       caption=self.caption,
                                       sub_caption=self.sub_caption,
                                       lowLimit=self.lowLimit,
                                       upLimit=self.upLimit,
                                       lowColor=self.lowColor,
                                       upColor=self.upColor,
                                       minValue=self.lowLimit,
                                       maxValue=self.upLimit,
                                       numsuffix=self.numsuffix,
                                       Rmargin=self.Rmargin,
                                       refresh=self.refresh,
                                       limit='fanLimit',
                                       value='fanValue',
                                       ))


    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">FAN CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = {'STATUS'      : ['ALARM','CLEAR'][int(self.data < self.threshold)],
                   'THRESHOLDS'  : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : self.data,
                   'DATA'        : self.cpsFanData,
                   }
        return json.dumps(jsonMsg)

    def getHtmlDetail(self):
        self.getConfigData()
        allData = '''
            <html><head>%s<title>Disk Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">FAN Information</span><br>
            <table class="main-table" border="1">
            <tr class="main-table-hdr">
        ''' % self.style
        allData+='<td>Fan Index</td><td>Type</td><td>Slot</td><td>OpState</td><td>Fault</td><td>Speed [RPM]</td><td>% Speed</td><tr>'
        for d in self.cpsFanData:                
            allData+='<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><tr>\n' % (d.get(NAME),
                        d.get(TYPE), d.get(SLOT), d.get(STATE), d.get(FAULT), d.get(SPEED), d.get(PSPEED))
        allData+='''
            </table>
            <table class="main-table" border="1">
            <tr><td>Highest Fan Speed</td><td class="main-table-td-c">%s%s</td></tr>
            <tr><td>Threshold Fan Speed</td><td class="main-table-td-c">%s%s</td></tr>
            <tr><td>Alarm State</td><td class="main-table-td-c">%s</td></tr>
            </table><br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>FAN Threshold (%s):</td><td><input name="fanLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="fan_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="fan_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.data, self.unit, 
                   self.threshold, self.unit, self.data < self.threshold, self.unit, self.threshold,
                   'checked="checked"' if self.fan_enabled == True else '',
                   'checked="checked"' if self.fan_enabled == False else '')
        return allData

    def getAlarm(self, threshold):
        if self.fan_enabled == False:
            return False,0
        self.getData(threshold)
        #return Alarm (True/False), Value
        return self.data < threshold, self.data

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'FAN Speed: %s\n' % (self.data)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.data < self.threshold)],
                                                                             self.data, self.threshold)
        return detailMsg

    def getInfo(self):
        if self.fan_enabled == False:
            return "Fan speed data is not available in this platform."
        else:
            return "Sensor represents fan speed, the default threshold for fault trigger is " + str(self.defaultLimit)



