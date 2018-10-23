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


#******************************************************************************
def get_memory(unit='M'):
    units={'M':1024,'G':1024*1024}
    mem_values = {}

    mem_info = ""
    with open('/proc/meminfo','r') as file:
        mem_info = file.read()

    for l in mem_info.splitlines():
        if ':' in l:
            desc, value = l.split(':')
            mem_values[desc] = int(int(value.strip('kB'))/units[unit])
    return mem_values

#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        with open(os.path.join(temppath,'dial_script.xhtml'), 'r') as f:
            self.scrTemp = Template(f.read())
        with open(os.path.join(temppath,'basic_style.xhtml'), 'r') as f:
            self.style = f.read()
        self.name        ='mem'
        self.plugType    = 'dial'
        self.postalarm   = True
        self.defaultLimit= 30.0
        self.memLimit   = self.defaultLimit
        self.vsize      = vsize
        self.hsize      = hsize
        self.caption    = 'Memory'
        self.sub_caption= '% free'
        self.lowLimit   = 0
        self.upLimit    = 100
        self.limit      = 0
        self.numsuffix  = '%'
        self.unit       = self.numsuffix
        self.Rmargin    = 5
        self.lowColor   = "e44a00"
        self.upColor    = "6baa01"
        self.free       = 0
        self.total      = 0
        self.exeCmd     = exeCmd
        self.pMem       = 0
        self.threshold  = self.memLimit
        self.pullRate   = 10
        self.timechk    = 0
        self.mem_enabled = True
        self.configFile = configFile
        self.configs    = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData(self.memLimit)

    def getConfigData(self):
        res=False
        if os.path.exists(self.configFile):
            with open(self.configFile, 'r') as f:
                data = f.read()
            for l in data.splitlines():
                if not l.strip().startswith('#') and '=' in l:
                    k,v = l.split('=')
                    if k in self.configs:
                        setattr(self, k, v)
                        res=True
            self.threshold = self.memLimit
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if not self.mem_enabled:
            return
        mem_data = get_memory()
        self.total = mem_data['MemTotal']
        self.free = mem_data['MemFree']+mem_data['Buffers']+mem_data['Cached']
        self.pMem=0.0
        if self.total:
            self.pMem=round((float(self.free)/float(self.total))*100, 2)
        if threshold is not None:
            self.threshold = threshold
        else:
            self.threshold = self.pMem
        self.timechk = time.time() + self.pullRate

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
                                       refresh=self.pullRate,
                                       limit='memLimit',
                                       value='memValue',
                                       ))

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = \
        {
            'STATUS'      : ['ALARM','CLEAR'][int(self.pMem < self.threshold)],
            'THRESHOLDS'  : self.threshold,
            'VALUE_UNIT'  : self.unit,
            'VALUE'       : self.pMem,
            'DATA'        : [{'TOTAL': self.total,
                              'FREE' : self.free}],
        }
        return json.dumps(jsonMsg)

    def getHtmlDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        allData = '''
            <html><head>%s<title>Memory Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Memory Information</span><br>
            <strong>Current Usage</strong>:<br>
            <table class="main-table" border="1">
            <tr><td>Total Memory</td><td class="main-table-td-c">%s MB</td></tr>
            <tr><td>Total Free</td><td class="main-table-td-c">%s MB</td></tr>
            <tr><td>Percent Free</td><td class="main-table-td-c">%s%%</td></tr>
            </table>
            <br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>Free Memory Threshold (%s):</td><td><input name="memLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="mem_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="mem_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.style, self.total, self.free, self.pMem, self.unit, self.threshold,
                   'checked="checked"' if self.mem_enabled else '',
                   'checked="checked"' if not self.mem_enabled else '')
        return allData

    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">MEM CHART</div></a>' % (self.name,self.name)

    def getChartObject(self):
        return ""

    def getAlarm(self, threshold):
        if not self.mem_enabled:
            return False,0
        if time.time() > self.timechk:
            self.getData(threshold)
        #return Alarm (True/False), Value
        return self.pMem < threshold, self.pMem

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'Memory: Total: %s, free: %s, used: %s\n' % (self.total, self.free, 
                                                                  self.total-self.free)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.pMem < self.threshold)],
                                                                      self.pMem, self.threshold)
        return detailMsg

    def getInfo(self):
        return "Sensor represents percentage of free memory, the default threshold for fault trigger is " + str(self.defaultLimit)



