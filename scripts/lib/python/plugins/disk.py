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


#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        self.scrTemp        = Template(open(os.path.join(temppath,'dial_script.xhtml')).read())
        self.style          = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name           ='disk'
        self.plugType       = 'dial'
        self.postalarm      = True
        self.defaultLimit   = 30.0
        self.diskLimit       = self.defaultLimit
        self.vsize          = vsize
        self.hsize          = hsize
        self.caption        = 'DISK'
        self.sub_caption    = '% free'
        self.lowLimit       = 0
        self.upLimit        = 100
        self.numsuffix      = '%'
        self.unit           = self.numsuffix
        self.Rmargin        = 5
        self.refresh        = 10
        self.limit          = 0
        self.lowColor       = "e44a00"
        self.upColor        = "6baa01"
        self.data           = 0
        self.exeCmd         = exeCmd
        self.threshold      = self.diskLimit
        self.disk_enabled    = True
        self.configFile     = configFile
        self.configs        = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData(self.diskLimit)

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
            self.threshold = self.diskLimit
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.disk_enabled == False:
            return
        st, raw_data = self.exeCmd('df -m /')
        if st == 0:
            for line in raw_data.splitlines():
                if line.startswith('/dev'):
                    self.data = 100-int(line.split()[4].strip('%'))
        if threshold is not None:
            self.threshold = threshold
        else:
            self.threshold = self.data
        return

    def getScripts(self):
        return self.scrTemp.substitute(dict(name=self.name, 
                                       vsize=self.vsize,
                                       hsize=self.hsize,
                                       caption=self.caption,
                                       sub_caption=self.sub_caption,
                                       lowLimit=self.lowLimit,
                                       upLimit=self.upLimit,
                                       minValue=self.lowLimit,
                                       maxValue=self.upLimit,
                                       lowColor=self.lowColor,
                                       upColor=self.upColor,
                                       numsuffix=self.numsuffix,
                                       Rmargin=self.Rmargin,
                                       refresh=self.refresh,
                                       limit='diskLimit',
                                       value='diskValue',
                                       ))

    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">DISK CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = {'STATUS'      : ['ALARM','CLEAR'][int(self.data < self.threshold)],
                   'THRESHOLDS'  : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : {self.name: self.data},
                   'DATA'        : [],
                   }
        return json.dumps(jsonMsg)

    def getHtmlDetail(self):
        self.getConfigData()
        st, raw_data = self.exeCmd('df -m /')
        total=0
        used=0
        if st == 0:
            for line in raw_data.splitlines():
                    if line.startswith('/dev'):
                        total = int(line.split()[1])
                        used = int(line.split()[2])
        allData = '''
            <html><head>%s<title>Disk Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Disk (Root Partition) Information</span><br>
            <strong>Current Usage</strong>:<br>
            <table class="main-table" border="1">
            <tr><td>Total Disk</td><td class="main-table-td-c">%s MB</td></tr>
            <tr><td>Total Used</td><td class="main-table-td-c">%s MB</td></tr>
            <tr><td>Percent Free</td><td class="main-table-td-c">%s%%</td></tr>
            </table>
            <br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>Free Disk Threshold (%s):</td><td><input name="diskLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="disk_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="disk_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.style,total, used, self.data, self.unit, self.threshold,
                   'checked="checked"' if self.disk_enabled == True else '',
                   'checked="checked"' if self.disk_enabled == False else '')
        return allData

    def getAlarm(self, threshold):
        if self.disk_enabled == False:
            return False,0
        self.getData(threshold)
        #return Alarm (True/False), Value
        return self.data < threshold, self.data

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'DISK Free: %s\n' % (self.data)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.data < self.threshold)],
                                                                             self.data, self.threshold)
        return detailMsg

    def getInfo(self):
        return "Sensor represents percentage of free disk, the default threshold for fault trigger is " + str(self.defaultLimit)


