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
import os, time
from datetime import datetime
import csv
from string import Template

RED     = '#FF3333'
BLUE    = '#6B97FC'
GREEN   = '#2AB807'
BLACK   = '#030303'

DATA_TEMPLATE='''{
                    label: '%s',
                    yAxisID: '%s',
                    data: [%s],
                    fill: false,
                    borderColor: [
                        '%s'
                    ],
                    backgroundColor: [
                        '%s'
                    ],
                    borderWidth: 1
                }'''
DATA_TEMPLATE_NO_ID='''{
                    label: '%s',
                    data: [%s],
                    fill: false,
                    borderColor: [
                        '%s'
                    ],
                    backgroundColor: [
                        '%s'
                    ],
                    borderWidth: 1
                }'''


PLUGIN_SVG='''<?xml version="1.0" encoding="iso-8859-1"?>
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%s" height="%s"
	 viewBox="0 0 505 526" style="enable-background:new 0 0 505 515;" xml:space="preserve">
<rect width="528" height="526" fill="#e2e2e2" stroke="lightgray" stroke-width="2"/>
<circle style="fill:#324A5E;" cx="252.5" cy="252.5" r="252.5"/>
<polygon style="fill:#CED5E0;" points="143,235 130.5,225.4 212.4,119.2 292.2,196.4 367.9,135.9 377.7,148.2 291.2,217.4 
	214.1,142.8 "/>
<path style="fill:#2B3B4E;" d="M43.4,394.1C88.8,461,165.5,505,252.5,505s163.7-44,209.1-110.9H43.4z"/>
<g><path style="fill:#54C0EB;" d="M394.8,385.4h-49.3c-1.2,0-2.1-0.9-2.1-2.1V204.6c0-1.2,0.9-2.1,2.1-2.1h49.3c1.2,0,2.1,0.9,2.1,2.1
		v178.7C396.9,384.4,396,385.4,394.8,385.4z"/>
<path style="fill:#54C0EB;" d="M316.4,385.4h-49.3c-1.2,0-2.1-0.9-2.1-2.1V257.1c0-1.2,0.9-2.1,2.1-2.1h49.3c1.2,0,2.1,0.9,2.1,2.1
		v126.2C318.4,384.4,317.5,385.4,316.4,385.4z"/>
<path style="fill:#54C0EB;" d="M237.9,385.4h-49.3c-1.2,0-2.1-0.9-2.1-2.1V193.2c0-1.2,0.9-2.1,2.1-2.1h49.3c1.2,0,2.1,0.9,2.1,2.1
		v190.1C240,384.4,239.1,385.4,237.9,385.4z"/>
<path style="fill:#54C0EB;" d="M159.5,385.4h-49.3c-1.2,0-2.1-0.9-2.1-2.1v-93.7c0-1.2,0.9-2.1,2.1-2.1h49.3c1.2,0,2.1,0.9,2.1,2.1
		v93.7C161.6,384.4,160.6,385.4,159.5,385.4z"/>
</g>
<rect x="73.3" y="377" style="fill:#CED5E0;" width="358.4" height="17.1"/>
<circle style="fill:#E6E9EE;" cx="372.8" cy="142.1" r="29.4"/>
<circle style="fill:#FF7058;" cx="372.8" cy="142.1" r="17.1"/>
<circle style="fill:#E6E9EE;" cx="291.7" cy="204" r="29.4"/>
<circle style="fill:#FF7058;" cx="291.7" cy="204" r="17.1"/>
<circle style="fill:#E6E9EE;" cx="213.3" cy="131" r="29.4"/>
<circle style="fill:#FF7058;" cx="213.3" cy="131" r="17.1"/>
<circle style="fill:#E6E9EE;" cx="134.8" cy="230.2" r="29.4"/>
<circle style="fill:#FF7058;" cx="134.8" cy="230.2" r="17.1"/>
</svg>'''

simpleHtml='''<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
    .hide { position:absolute; top:-1px; left:-1px; width:1px; height:1px; }
    .main-table {
                border: 1px solid blue;
                width: 600px;
               }
    .main-table-hdr {
                font-family: Verdana;
                font-size: 12px;
                background-color:#$${color};
                text-align: center;
               }
    .main-table-tr {
                border: 1px solid blue;
               }
    .main-table-td-c {
                text-align: center;
               }
</style>
<!-- SCRIPT Section -->
<script type="text/javascript">
function gourl()
{
    setTimeout(function() {
        window.location.href = '../..';
    }, 300);
}
</script>
<script type="text/javascript" src="../scripts/Chart.min.js"></script>
<style>
canvas {
    -moz-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
}
</style>
</head><body>
<div style="width:60%%">
    <canvas id="%s" width="%s" height="%s"></canvas>
</div>
%s
<hr>
<div style="width:70%%">
    <canvas id="%s" width="%s" height="%s"></canvas>
</div>
%s
<hr>
<div style="width:70%%">
    <canvas id="%s" width="%s" height="%s"></canvas>
</div>
%s
<iframe name="hiddenFrame" class="hide"></iframe>
<form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
<hr>
<legend>Configurations</legend>
<hr>
<br>Show Zero values in top 5 charts:&nbsp;
<input type="radio" id="enable_yes" name="zero_enabled" value="True" %s/>Yes
<input type="radio" id="enable_no" name="zero_enabled" value="False" %s/>No<br>
<p>Set # of hours to plot: <input name="analyticsLimit" type="input" value="%s"/></p>
<p><input name="Submit"  type="submit" value="Commit Changes"/></p>
</form>
</body></html>'''


#******************************************************************************
def get_spaced_colors(n):
    max_value = 16581375 #255**3
    interval = int(max_value / n)
    colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
    
    return [(int(i[:2], 16), int(i[2:4], 16), int(i[4:], 16)) for i in colors]
#******************************************************************************

num_hours_collect=3
#******************************************************************************
def get_sec_from_now(t_str):
    t1=datetime.strptime(t_str, '%m/%d/%y %H:%M:%S')
    return (time.time()-time.mktime(t1.timetuple()))

#******************************************************************************
def get_timestamp(t_str):
    uptime = None
    boot=None
    ts=None
    with open("/proc/uptime", 'r') as f:
        uptime=float(f.readline().split()[0])
    t=get_sec_from_now(t_str)
    if t >= uptime:
        boot = 'Boot'
    if t < (num_hours_collect*3600):
        ts = t_str.split()[-1]
    return ts, boot

#******************************************************************************
def getExtraInfo():
    ver = None
    plat= None
    file = '/etc/OPX-release-version'
    if not os.path.exists(file) and os.path.exists('/etc/OS10-release-version'):
        file = '/etc/OS10-release-version'
    try:
        with open(file) as os10Info:
            for l in os10Info:
                if ver is None and 'OS_VERSION' in l:
                    ver = l.split('=')[1].replace('"','').strip()
                elif plat is None and 'PLATFORM' in l:
                    plat =  l.split('=')[1].replace('"','').strip()
                if ver is not None and plat is not None: 
                    break
    except Exception, e:
        pass
    return ver,plat

#******************************************************************************
def pct_get(val1, val2):
    val2 = float(val2)
    if val2 == 0:
        return 0.0
    return round(100*(float(val1)/val2),2)

#******************************************************************************
def getLogs():
    all_data = {'time'  :[],
                'cpu'   :[],
                'mem'   :[],
                'swap'  :[],
                'top_cpu' :[],
                'top_mem' :[]}
    with open('/var/log/sys_status.log', 'rb') as csvfile:
        try:
            csvdata = reversed(list(csv.reader((line.replace("\0","") for line in csvfile), delimiter=',', quotechar='"')))
        except Exception, e:
            print 'Failed1: %s' % e
            return None
        try:
            offset=0
            for row in csvdata:
                if len(row) == 29:
                    offset =1
                if "Date" in row[0]:
                    continue
                ts, bt = get_timestamp(row[0])
                
                if ts:
                    all_data['time'].append('"%s"' % ts)
                    all_data['cpu'].append(str(round(float(row[23-offset]),2)))
                    all_data['mem'].append(str(pct_get(row[26-offset], row[27-offset])))
                    all_data['swap'].append(str(pct_get(row[28-offset], row[29-offset])))
                    all_data['top_cpu'].append({eval(row[1])[1] : str(eval(row[1])[2]),
                                                eval(row[3])[1] : str(eval(row[3])[2]),
                                                eval(row[4])[1] : str(eval(row[4])[2]),
                                                eval(row[5])[1] : str(eval(row[5])[2]),
                                                eval(row[6])[1] : str(eval(row[6])[2]),})
                    all_data['top_mem'].append({eval(row[11])[1] : str(eval(row[11])[2]),
                                                eval(row[13])[1] : str(eval(row[13])[2]),
                                                eval(row[14])[1] : str(eval(row[14])[2]),
                                                eval(row[15])[1] : str(eval(row[15])[2]),
                                                eval(row[16])[1] : str(eval(row[16])[2]),})
                if ts is None:
                    break
        except Exception, e:
            print 'Failed2: %s' % e
            return None 
        for ent in all_data:
            all_data[ent].reverse()
    return all_data

#******************************************************************************
# Required Class
#******************************************************************************
class SystemStatusPlugin():
    def __init__ (self, exeCmd, vsize=135, hsize=140, temppath='./templates',
                  configFile='/etc/sys_status.conf'):
        with open(os.path.join(temppath,'chart.xhtml')) as file:
            self.max_template = Template(file.read())
        self.name           = 'analytics'
        self.plugType       = 'dial'
        self.postalarm      = False
        self.defaultLimit   = None
        self.vsize          = vsize
        self.hsize          = hsize
        self.exeCmd         = exeCmd
        self.numPrefix      = ""
        self.analyticsLimit = num_hours_collect
        self.configFile     = configFile
        self.zero_enabled   = True
        self.configs        = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.getConfigData()

    def getConfigData(self):
        global num_hours_collect
        res=False
        if os.path.exists(self.configFile):
            data = ""
            with open(self.configFile, 'r') as file:
                data = file.read()
            for l in data.splitlines():
                if not l.strip().startswith('#') and '=' in l:
                    k,v = l.split('=')
                    if k in self.configs:
                        if v.isdigit() or v in ['True','False']:
                            setattr(self, k, eval(v))
                        else:
                            setattr(self, k, v)
                        res=True
        num_hours_collect = self.analyticsLimit
        return res

    def getDesc(self):
        return self.name

    def getHtmlDetail(self, pid=None):
        self.getConfigData()
        local_data = getLogs()
        ts      = ",".join(local_data['time'])
        yAx1    = ",".join(local_data['cpu'])
        yAx2    = ",".join(local_data['mem'])
        yAx3    = ",".join(local_data['swap'])

        # Top 5 cpu users
        list_cpu_procs = {p: te[p] for te in local_data['top_cpu'] for p in te if te[p]}
        #process for cpu users
        cpu_dataset = [{"seriesname": str(proc), "data" : None} for proc in list_cpu_procs]

        for ser in cpu_dataset:
            top_cpu_data = []
            for ser_data in local_data['top_cpu']:
                if ser_data.get(ser['seriesname']) is not None:
                    if self.zero_enabled or ser_data.get(ser['seriesname']) > 0:
                        top_cpu_data.append(ser_data.get(ser['seriesname']))
                    else:
                        top_cpu_data.append('')
                else:
                    top_cpu_data.append('')
            ser['data'] = top_cpu_data

        # Top 5 mem users
        list_mem_procs = {p: te[p] for te in local_data['top_mem'] for p in te if te[p]}
        #process for mem users
        mem_dataset = [{"seriesname": str(proc), "data" : None} for proc in list_mem_procs]
        for ser in mem_dataset:
            top_mem_data = []
            for ser_data in local_data['top_mem']:
                if ser_data.get(ser['seriesname']) is not None:
                    if self.zero_enabled or ser_data.get(ser['seriesname']) > 0:
                        top_mem_data.append(ser_data.get(ser['seriesname']))
                    else:
                        top_mem_data.append('')
                else:
                    top_mem_data.append('')
            ser['data'] = top_mem_data

        ver, platform = getExtraInfo()
        cpu_mem_swap_data = '%s,%s,%s' % (
            DATA_TEMPLATE % ("% CPU Load", "cpu", yAx1, RED, RED),
            DATA_TEMPLATE % ("% Memory Free", 'mem', yAx2, BLUE, BLUE),
            DATA_TEMPLATE_NO_ID % ("% SWAP Free", yAx3, GREEN, GREEN))
        
        colors=get_spaced_colors(len(cpu_dataset))
        cpu_top5 = ",".join([DATA_TEMPLATE_NO_ID % (cpu_user['seriesname'], 
                                                    ",".join(cpu_user['data']), 
                                                    colors[c] , 
                                                    colors[c]) for c, cpu_user in enumerate(cpu_dataset) ])
        colors=get_spaced_colors(len(mem_dataset))
        cpu_mem5 = ",".join([DATA_TEMPLATE_NO_ID % (mem_user['seriesname'], 
                                                    ",".join(mem_user['data']), 
                                                    colors[c] , 
                                                    colors[c]) for c, mem_user in enumerate(mem_dataset) ])

        if self.zero_enabled:
            yes_val = 'checked="checked"'
            no_val  = ''
            print "yes enabled"
        else:
            no_val = 'checked="checked"'
            yes_val= ''
            print "no enabled"
        return (simpleHtml % (
            self.name, 1200, 800,
            self.max_template.substitute(dict(name=self.name, 
                                       caption="CPU, Memory, and SWAP Chart [%s]" % platform,
                                       sub_caption="Data Based on %s Hour @ %s" % (num_hours_collect, time.strftime('%H:%M:%S %m/%d/%y', time.gmtime())),
                                       xAxis="Time",
                                       timestamps=ts,
                                       dataset=cpu_mem_swap_data,
                                       yAxis1Title="cpu",
                                       yAxis1Min=0,
                                       yAxis1Max=100,
                                       yAxis1Prefix="%",
                                       yAxis2Title="mem",
                                       yAxis2Min=0,
                                       yAxis2Max=100,
                                       yAxis2Prefix="%",
                                       l_color=RED,
                                       position='top',
                                       width='30'
                                       )),
            self.name+'topcpu', 800, 500,
            self.max_template.substitute(dict(name=self.name+'topcpu', 
                                       caption="Top 5 CPU Users [%s]" % platform,
                                       sub_caption="Data Based on %s Hour @ %s" % (num_hours_collect, time.strftime('%H:%M:%S %m/%d/%y', time.gmtime())),
                                       xAxis="Time",
                                       timestamps=ts,
                                       dataset=cpu_top5,
                                       yAxis1Title="cpu",
                                       yAxis1Min=0,
                                       yAxis1Max=100,
                                       yAxis1Prefix="%",
                                       yAxis2Title="mem",
                                       yAxis2Min=0,
                                       yAxis2Max=100,
                                       yAxis2Prefix="%",
                                       l_color=BLACK,
                                       position='bottom',
                                       width='5'
                                       )),
            self.name+'topmem', 800, 500,
            self.max_template.substitute(dict(name=self.name+'topmem', 
                                       caption="Top 5 Memory Users [%s]" % platform,
                                       sub_caption="Data Based on %s Hour @ %s" % (num_hours_collect, time.strftime('%H:%M:%S %m/%d/%y', time.gmtime())),
                                       xAxis="Time",
                                       timestamps=ts,
                                       dataset=cpu_mem5,
                                       yAxis1Title="mem",
                                       yAxis1Min=0,
                                       yAxis1Max=100,
                                       yAxis1Prefix="Kb",
                                       yAxis2Title="mem",
                                       yAxis2Min=0,
                                       yAxis2Max=100,
                                       yAxis2Prefix="Kb",
                                       l_color=BLACK,
                                       position='bottom',
                                       width='5'
                                       )),
            yes_val,
            no_val,
            self.analyticsLimit
                            )
                )

    def getScripts(self):
        return ''

    def getCodeObject(self):
        return "<a href=\"report/%s\" title=\"click for details\">%s<a>" % (self.name, PLUGIN_SVG % (self.hsize, self.vsize))

    def getChartObject(self):
        return ""

    def getAlarm(self, threshold):
        return False, 0

    def getAlarmDetail(self):
        return 'ANALYTICS MODULE'

    
    def getInfo(self):
        return "Sensor is an output tool to plot cpu and memory usage. Graphics ONLY!"



