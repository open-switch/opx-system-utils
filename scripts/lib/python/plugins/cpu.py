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
try:
    import multiprocessing
except:
    pass


#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        self.scrTemp = Template(open(os.path.join(temppath,'dial_script.xhtml')).read())
        self.style = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name       ='cpu'
        self.postalarm  = True
        self.plugType   = 'dial'
        self.defaultLimit = 80.0
        self.cpuLimit    = self.defaultLimit
        self.unit       ='%'
        self.vsize      = vsize
        self.hsize      = hsize
        self.caption    = 'CPU'
        self.sub_caption= '% load [15min]'
        self.lowLimit   = 0
        self.upLimit    = 300
        self.limit      = 0
        self.pullRate   = 10
        self.timechk    = 0
        self.lowColor   = "6baa01"
        self.upColor    = "e44a00"
        self.numsuffix  = '%'
        self.Rmargin    = 5
        self.data       = 0
        self.exeCmd     = exeCmd
        self.pMem       = 0
        self.threshold  = self.cpuLimit
        try:
            self.num_cores= multiprocessing.cpu_count()
        except:
            self.num_cores = 1
        self.cpu_enabled    = True
        self.configFile     = configFile
        self.configs        = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData(self.cpuLimit)

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
            self.threshold  = self.cpuLimit
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.cpu_enabled == False:
            return
        load = {'1MIN':0, '5MIN':1, '15MIN':2}
        #/proc/loadavg: 1min 5min 15min count pid
        raw_data = open('/proc/loadavg').read().split()
        self.data = 100*(float(raw_data[load['15MIN']])/self.num_cores)
        if threshold is not None:
            self.threshold = threshold
        else:
            self.threshold = self.data
        self.timechk = time.time()


    def getScripts(self):
        return self.scrTemp.substitute(dict(name=self.name, 
                                       vsize=self.vsize,
                                       hsize=self.hsize,
                                       caption=self.caption,
                                       sub_caption=self.sub_caption,
                                       lowLimit=self.lowLimit,
                                       upLimit=self.upLimit/self.num_cores if self.upLimit/self.num_cores > 100 else 100,
                                       minValue=self.lowLimit,
                                       maxValue=self.upLimit/self.num_cores if self.upLimit/self.num_cores > 100 else 100,
                                       lowColor=self.lowColor,
                                       upColor=self.upColor,
                                       numsuffix=self.numsuffix,
                                       Rmargin=self.Rmargin,
                                       refresh=self.pullRate,
                                       limit='cpuLimit',
                                       value='cpuValue',
                                       ))

    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">CPU CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getJsonDetail(self):
        self.getConfigData()
        load ={'1MIN':0, '5MIN':1, '15MIN':2}
        raw_data = open('/proc/loadavg').read().split()
        jsonMsg = {'STATUS'     : ['ALARM','CLEAR'][int(self.data > self.threshold)],
                   'THRESHOLDS' : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : round(self.data, 2),
                   'DATA'        : [{'1MIN':  round(100*(float(raw_data[load['1MIN']])/self.num_cores), 2),
                                     '5MIN':  round(100*(float(raw_data[load['5MIN']])/self.num_cores), 2),
                                     '15MIN': round(100*(float(raw_data[load['15MIN']])/self.num_cores),2),
                                     }
                                    ],
                   }
        
        return json.dumps(jsonMsg)


    def getHtmlDetail(self):
        self.getConfigData()
        load ={'1MIN':0, '5MIN':1, '15MIN':2}
        #/proc/loadavg: 1min 5min 15min count pid
        raw_data = open('/proc/loadavg').read().split()
        allData = '''
            <html><head>%s<title>CPU Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">CPU Information (Cores: %s)</span><br>
            <strong>Current Usage</strong>:<br>
            <table class="main-table" border="1">
        ''' % (self.style, self.num_cores)
        allData +='<tr><td>1 MIN Load</td><td class="main-table-td-c">%s%%</td></tr>' % (100*(float(raw_data[load['1MIN']])/self.num_cores))
        allData +='<tr><td>5 MIN Load</td><td class="main-table-td-c">%s%%</td></tr>' % (100*(float(raw_data[load['5MIN']])/self.num_cores))
        allData +='<tr><td>15 MIN Load</td><td class="main-table-td-c">%s%%</td></tr>' % (100*(float(raw_data[load['15MIN']])/self.num_cores))
        allData += '''</table>
            <br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>CPU Load Threshold (%s):</td><td><input name="cpuLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="cpu_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="cpu_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.unit, self.threshold,
                   'checked="checked"' if self.cpu_enabled == True else '',
                   'checked="checked"' if self.cpu_enabled == False else '')
        return allData

    def getAlarm(self, threshold):
        if self.cpu_enabled == False:
            return False,0
        if time.time() - self.timechk > self.pullRate:
            self.getData(threshold)
        #return Alarm (True/False), Value
        return self.data > threshold, self.data

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'CPU: Load: %s\n' % (self.data)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.data > self.threshold)],
                                                                             self.data, self.threshold)
        return detailMsg

    def getInfo(self):
        return "Sensor represents CPU load, the default threshold for fault trigger is " + str(self.defaultLimit)


