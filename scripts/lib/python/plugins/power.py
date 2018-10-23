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
import cps, cps_utils


SLOT    = 'slot'
TYPE    = 'entity-type' 
FAULT   = 'fault-type'  
STATE   = 'oper-status' 
PRESENT = 'present'

CPS_KEY     ='base-pas/entity'
CPS_FT_KEY  ='base-pas/fan-tray'
CPS_SLOT    =CPS_KEY+'/'+SLOT
CPS_TYPE    =CPS_KEY+'/'+TYPE
CPS_FAULT   =CPS_KEY+'/'+FAULT
CPS_STATE   =CPS_KEY+'/'+STATE
CPS_PRESENT =CPS_KEY+'/'+PRESENT
CPS_FT_SLOT =CPS_FT_KEY+'/'+SLOT

def entityTypeToString(eType):
    return {1: "PSU", 2: "Fan tray", 3: "Card"}.get(eType, 'Unknown')
def opStatusToString(oType):
    return {1: 'Up', 2: 'Down', 3: 'Testing', 4: 'Unknown', 5: 'Dormant', 
            6: 'Not present', 7: 'Lower layer down', 8: 'Fail'}.get(oType, 'Unknown')
def faultTypeToString(fType):
    return {1: 'OK', 2: 'Unknown', 3: 'Communication failure', 4: 'Configuration error', 
            5: 'Compatibility error', 6: 'Hardware failure', 7: 'No power'}.get(fType, 'Unknown')
def ftPresent(present):
    return {1: 'Yes', 0: 'No'}.get(present)

#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        self.scrTemp = Template(open(os.path.join(temppath,'bulb_script.xhtml')).read())
        self.style      = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name       ='power'
        self.postalarm  = True
        self.plugType   = 'bulb'
        self.defaultLimit = None
        self.vsize      = vsize
        self.hsize      = hsize
        self.caption    = 'Power'
        self.tooltext   = 'click for details'
        self.lowLimit     = 0
        self.upLimit      = 100
        self.unit         = ''
        self.redLabel     = 'FAILED'
        self.redLlimit    = 1
        self.redUlimit    = 100
        self.greenLabel   = 'OK'
        self.greenLlimit  = 0
        self.greenUlimit  = 0
        self.yellowLabel  = 'YELLOW'
        self.yellowLlimit = -1 #unused
        self.yellowUlimit = -1 #unused
        self.fetch        = 'data/power'
        self.psuData      = {}
        self.data         = 0
        self.alarm        = False
        self.exeCmd       = exeCmd
        self.pullRate     = 60
        self.timechk      = 0
        self.power_enabled = True
        self.configFile = configFile
        self.configs    = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData()

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
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.power_enabled == False:
            return 0,0
        def getCpsValue(eType, data):
            return cps_utils.cps_attr_types_map.from_data(eType, data[eType])
        total=0
        psuData ={}
        numFaults = 0
        cpsData=[]
        fanTrayData=[]
        cps.get([cps.key_from_name('observed', CPS_KEY)], cpsData)
        cps.get([cps.key_from_name('observed', CPS_FT_KEY)], fanTrayData)
        for e in cpsData:
            entity_data = e['data']
            eType = getCpsValue(CPS_TYPE, entity_data)
            if eType != 1:
                continue
            slot = getCpsValue( CPS_SLOT, entity_data)
            fan_tray_found = False
            for p in fanTrayData:
                fan_tray_data = p['data']
                if getCpsValue(CPS_FT_SLOT, fan_tray_data) == slot:
                    fan_tray_found = True
                    break
            if not fan_tray_found:
                continue
            present = ftPresent(getCpsValue(CPS_PRESENT, entity_data))
            state = opStatusToString(getCpsValue(CPS_STATE, entity_data))
            fault = getCpsValue(CPS_FAULT, entity_data)
            psuData[slot] = {PRESENT:present, STATE:state, FAULT:fault}
            total += 1
            if state != 'Up':
                numFaults += 1

        self.psuData = psuData
        if threshold is not None:
            self.threshold = threshold
        else:
            self.threshold = self.data
        self.timechk = time.time()

        return numFaults, total

    def getScripts(self):
        return self.scrTemp.substitute(dict(name=self.name, 
                                       vsize=self.vsize,
                                       hsize=self.hsize,
                                       caption=self.caption,
                                       tooltext=self.tooltext,
                                       lowLimit=self.lowLimit,
                                       upLimit=self.upLimit,
                                       redLabel=self.redLabel,
                                       redLlimit=self.redLlimit,
                                       redUlimit=self.redUlimit,
                                       greenLabel=self.greenLabel,
                                       greenLlimit=self.greenLlimit,
                                       greenUlimit=self.greenUlimit,
                                       yellowLabel=self.yellowLabel,
                                       yellowLlimit=self.yellowLlimit,
                                       yellowUlimit=self.yellowUlimit,
                                       fetch=self.fetch,
                                       pullRate=self.pullRate*1000,
                                       value='powerValue',
                                       ))

    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">FAN CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = {'STATUS'      : ['CLEAR','ALARM'][int(self.alarm)],
                   'THRESHOLDS'  : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : self.data,
                   'DATA'        : [self.psuData],
                   }
        return json.dumps(jsonMsg)

    def getHtmlDetail(self):
        self.getConfigData()
        allData = '''
            <html><head>%s<title>Power Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Power Supply Information</span><br>
            <table class="main-table" border="1">
            <tr class="main-table-hdr">
        ''' % self.style
        allData+='<td>Slot</td><td>Present</td><td>OpState</td><td>Fault</td><tr>'
        for d in self.psuData:
            allData+='''<tr><td class="main-table-td-c">%s</td>
                            <td class="main-table-td-c">%s</td>
                            <td class="main-table-td-c">%s</td>
                            <td class="main-table-td-c">%s</td>
                        <tr>\n''' % (d, self.psuData[d].get(PRESENT), self.psuData[d].get(STATE), 
                                     faultTypeToString(self.psuData[d].get(FAULT)))
        allData+='''
            </table>
            <table class="main-table" border="1">
            <tr><td>PSU Faults</td><td class="main-table-td-c">%s</td></tr>
            <tr><td>Alarm State</td><td class="main-table-td-c">%s</td></tr>
            </table>
            <br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="power_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="power_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.data if self.data >= 0 else 'PARTIAL', self.alarm,
                   'checked="checked"' if self.power_enabled == True else '',
                   'checked="checked"' if self.power_enabled == False else '')
        return allData

    def getAlarm(self, threshold):
        if self.power_enabled == False:
            return False,0
        if time.time() - self.timechk > self.pullRate:
            self.data, total = self.getData(threshold)
            #return Alarm (True/False), Value
            self.alarm = False
            if self.data > threshold and self.data < total:
                self.data = -1
                self.alarm = True
            elif self.data > threshold:
                self.alarm = True

        return self.alarm, self.data

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'Power Supplies: %s\n' % (self.data)
        detailMsg += 'Alarm State: %s, Current: %s' % (self.alarm, self.data)
        return detailMsg

    def getInfo(self):
        return "Sensor represents the number of power faults (1 power fault with value < 0 and 2 power faults with value > 0), the default threshold for fault trigger is " + str(self.threshold)


