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
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        self.scrTemp = Template(open(os.path.join(temppath,'dial_script.xhtml')).read())
        self.style          = open(os.path.join(temppath,'basic_style.xhtml')).read()
        self.name           = 'swap'
        self.plugType       = 'dial'
        self.postalarm      = True
        self.defaultLimit   = 50.0
        self.swapLimit      = self.defaultLimit
        self.vsize          = vsize
        self.hsize          = hsize
        self.caption        = 'SWAP'
        self.sub_caption    = '% free'
        self.lowLimit       = 0
        self.upLimit        = 100
        self.numsuffix      = '%'
        self.unit           = self.numsuffix
        self.Rmargin        = 5
        self.limit          = 0
        self.lowColor       = "e44a00"
        self.upColor        = "6baa01"
        self.free           = 0
        self.total          = 0
        self.exeCmd         = exeCmd
        self.pSwap          = 0
        self.pullRate       = 10
        self.timechk        = 0
        self.threshold      = self.swapLimit
        self.swap_enabled = True
        self.configFile = configFile
        self.configs    = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()
        self.getData(self.swapLimit)

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
            self.threshold = self.swapLimit
        return res

    def getDesc(self):
        return self.name

    def getData(self, threshold=None):
        if self.swap_enabled == False:
            return
        st, raw_top_data = self.exeCmd('free -m')
        if st == 0:
            for line in raw_top_data.splitlines():

                if 'Swap' in line:
                    total = int(line.split()[1])
                    free = int(line.split()[3])
            self.total = total
            self.free = free
            self.pSwap=0.0
            if total:
                self.pSwap=round((float(free)/float(total))*100, 2)
            if threshold is not None:
                self.threshold = threshold
            else:
                self.threshold = self.pSwap
        self.timechk = time.time()

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
                                       limit='swapLimit',
                                       value='swapValue',
                                       ))

    def getCodeObject(self):
        return '<a href=\'report/%s\' title=\"click for details\"><div id="chart-%s">SWAP CHART</div></a>' % (self.name, self.name)

    def getChartObject(self):
        return ""

    def getHtmlDetail(self):
        self.getConfigData()
        data=open('/proc/swaps').read()
        allData = '''
            <html><head>%s<title>SWAP Status</title></head><body>
            <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Swap Information</span><br>
            <strong>Current Usage</strong>:<br>
            <table class="main-table" border="1">
            <tr><td>%% Free Swap</td><td class="main-table-td-c">%s%%</td></tr>
            </table>
            <table class="main-table" border="1">
            <tr class="main-table-hdr"><td class="main-table-td-c">Device</td>
            <td class="main-table-td-c">Size</td>
            <td class="main-table-td-c">Used</td></tr>
        ''' % (self.style, self.pSwap)
        for l in data.splitlines():
            if 'Filename' in l:
                continue
            dlist = l.split()
            allData +='<tr><td class="main-table-td-c">%s</td><td class="main-table-td-c">%s</td><td class="main-table-td-c">%s</td></tr>' % (
                            dlist[0], dlist[2], dlist[3])
        allData +='''
            </table>
            <br>
            <iframe name="hiddenFrame" class="hide"></iframe>
            <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
            <legend>Configurations</legend>
            <table class="main-table">
             <tbody>
            <tr><td>Free Swap Threshold (%s):</td><td><input name="swapLimit" type="input" value="%s"/></td></tr>
            </tbody>
            </table>
            <br>&nbsp;Plugin Enabled&nbsp;<input type="radio" id="enable_yes" name="swap_enabled" value="True" %s/>Yes
            <input type="radio" id="enable_no" name="swap_enabled" value="False" %s/>No<br>
            <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
            </form>
            </body></html>
            ''' % (self.unit, self.threshold,
                   'checked="checked"' if self.swap_enabled == True else '',
                   'checked="checked"' if self.swap_enabled == False else '')
        return allData

    def getJsonDetail(self):
        self.getConfigData()
        self.getData(self.threshold)
        jsonMsg = {'STATUS'      : ['ALARM','CLEAR'][int(self.pSwap < self.threshold)],
                   'THRESHOLDS'  : self.threshold,
                   'VALUE_UNIT'  : self.unit,
                   'VALUE'       : self.pSwap,
                   'DATA'        : [{'TOTAL': self.total, 
                                     'FREE' : self.free}],
                   }
        return json.dumps(jsonMsg)

    def getAlarm(self, threshold):
        if self.swap_enabled == False:
            return False,0
        if time.time() - self.timechk > self.pullRate:
            self.getData(threshold)
        #return Alarm (True/False), Value
        return self.pSwap < threshold, self.pSwap

    def getAlarmDetail(self):
        alarm = ['GREEN', 'RED']
        detailMsg =  'Swap: Total: %s, free: %s, used: %s\n' % (self.total, self.free, 
                                                                     self.total-self.free)
        detailMsg += 'Alarm State: %s, Current: %s, Threshold; %s' % (alarm[int(self.pSwap < self.threshold)],
                                                                             self.pSwap, self.threshold)
        return detailMsg

    def getInfo(self):
        return "Sensor represents the percentage of free swap, the default threshold for fault trigger is " + str(self.defaultLimit)


