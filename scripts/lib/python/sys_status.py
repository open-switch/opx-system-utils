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

import sys, shutil, atexit, re
from string import Template
import multiprocessing
import os
import time, socket, fcntl, struct
import signal
import csv
import operator
import threading
import ssl
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import json, cgi
try:
    import requests
except:
    print "please install python-requests. sudo apt-get install python-requests"
    sys.exit(1)
import traceback


#******************************************************************************
# CONSTANTS
#******************************************************************************
VER_MAJOR = 3
VER_MINOR = 1
VER_DEV   = 0
SERVICE_VERSION = '%s.%s.%s' % (VER_MAJOR, VER_MINOR, VER_DEV)

COLS_PER_ROW = 4
TABLE_CELL_W = 143
CHART_WIDTH  = 139
CPU_DEF_VAL  = 90
MEM_DEF_VAL  = 30
DISK_DEF_VAL = 80
SWAP_DEF_VAL = 50
HOSTNAME    = '127.0.0.1'
PORT        = 8788
PIDFILE     = '/tmp/sys_status.pidfile'
STDOUT      = '/tmp/sys_status.stdout'
STDERR      = '/tmp/sys_status.stderr'
FMT_GREEN   = '\x1b[0;32;3m'
FMT_RED     = '\x1b[0;31;3m'
FMT_BLUE    = '\x1b[0;34;3m'
FMT_NORMAL  = '\x1b[0m'
logfile     = None
working_dir = os.path.dirname(os.path.realpath(__file__))
config_file = '/etc/sys_status.conf'
logfilename = '/var/log/sys_status.log'
logrotate = '''%s
{
	rotate 5
	daily
        size 1M
	missingok
	notifempty
	copytruncate
	delaycompress
	compress
	postrotate
	    invoke-rc.d sys_status rotate > /dev/null
	endscript
}
''' % logfilename
default_config = {'HOST':           HOSTNAME,
                  'PORT':           PORT,
                  'pluginPerRow':   COLS_PER_ROW,
                  'cert'        :   '%s/server.pem' % working_dir,
                 }
API_VER     = 1
ROOT_URL    = '/api/v%s' % API_VER
SET_URL     = '%s/set' % ROOT_URL
GET_URL     = '%s/get' % ROOT_URL
STATUS_URL  = '%s/status' % ROOT_URL
FETCH_URL   = '%s/fetch' % ROOT_URL #used by bulb_script to get alarms to bulb widgets
PULLDATA_URL= '%s/data' % ROOT_URL  #used by dial_script to get data to dial widgets
SCRIPT_URL  = '%s/script' % ROOT_URL
HTML_URL    = '%s/html' % ROOT_URL
REPORT_URL  = '%s/report' % ROOT_URL
JSON_URL    = '%s/json' % ROOT_URL
HELP_URL    = '%s/help' % ROOT_URL
DNLD_URL    = '/var/log/sys_status'

URL_TYPE    = 'https'

#******************************************************************************
# IMAGES and Attributes for the header for Dell
#******************************************************************************
DELL_COLOR  = '0485cb'
DELL_ADJ    = 45
DELL_ICO    = 'dell.ico'
DELL_SVG    = '''
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
x="0px" y="0px" width="60px" height="60px" viewBox="0 0 60 60" enable-background="new 0 0 60 60" xml:space="preserve">  
<image id="image0" width="60" height="60" x="0" y="0" xlink:href="data:image/png;base64,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
NDItMDc6MDB89ptCAAAAAElFTkSuQmCC" />
</svg>'''

#******************************************************************************
# IMAGES and Attributes for the header for OPX
#******************************************************************************
OPX_COLOR  = 'ff6f3e'
OPX_ADJ    = 70
OPX_ICO    = 'opx.ico'
OPX_SVG ='''<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="70" height="70" viewBox="0 0 300.000000 300.000000"
 preserveAspectRatio="xMidYMid meet">
<metadata>
Created by potrace 1.10, written by Peter Selinger 2001-2011
</metadata>
<g transform="translate(0.000000,300.000000) scale(0.100000,-0.100000)"
fill="#000000" stroke="none">
<path d="M455 2369 c-159 -93 -327 -191 -372 -217 l-83 -48 193 -111 c105 -61 273 -158 372 -215 l180 -104 -3 148 -4 148 53 0 54 0 152 -152 153 -153 92 93
93 92 -195 195 -195 196 -100 -2 -100 -2 0 152 c0 83 0 151 0 150 0 -1 -130 -77 -290 -170z m277 -149 c16 -18 29 -20 114 -19 l97 1 -122 22 -138z" />
<path d="M2252 2388 l3 -154 -99 4 -99 4 -606 -605 -606 -605 -50 -4 -50 -5 3 155 3 155 -28 -18 c-24 -16 -67 -41 -258 -150 -22 -13 -80 -47 -130 -75 -49
-29 -145 -84 -213 -123 -68 -38 -122 -71 -120 -72 6 -5 160 -95 163 -95 2 0 32 -17 66 -38 35 -22 167 -98 292 -170 l228 -132 -3 153 -3 152 99 -3 99 -4
606 605 606 605 50 4 50 5 -3 -155 -3 -154 33 20 c18 11 132 77 253 147 233 135 230 133 373 215 82 47 91 54 75 65 -10 7 -139 82 -288 167 -274 158 -354
204 -413 240 l-33 20 3 -154z m161 28 c43 -25 81 -46 85 -46 4 0 30 -15 57 -33 44 -29 145 -88 330 -192 29 -17 56 105 -60z" fill="#ff6f3e"/>
<path d="M1755 1240 l-90 -90 195 -195 195 -196 100 2 100 2 0 -149 0 -149 370 213 c204 118 371 215 372 216 1 1 -147 88 -330 194 -183 106 -350 203
-372 216 l-40 24 3 -149 4 -149 -54 0 -53 0 -150 150 c-82 83 -152 150 -155 150 -3 0 -46 -41 -95 -90z m250 -100 c149 -147 152 -150 195 -150 72 0 80 14
80 144 0 61 4 156 -150z" fill="black"/>
</g>
</svg>
'''

LOGO_IMG = '''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="200.000000pt" height="200.000000pt" viewBox="0 0 200.000000 200.000000"
 preserveAspectRatio="xMidYMid meet">
<metadata>
Created by potrace 1.15, written by Peter Selinger 2001-2017
</metadata>
<g transform="translate(0.000000,200.000000) scale(0.100000,-0.100000)"
fill="#000000" stroke="none">
<path d="M1045 1980 c-135 -35 -237 -92 -338 -189 -221 -210 -293 -529 -187
-823 183 -504 842 -662 1236 -295 166 155 243 335 244 568 0 350 -232 654
-566 739 -103 27 -289 27 -389 0z m345 -206 c133 -37 273 -150 337 -269 114
-216 82 -466 -82 -643 -99 -107 -223 -168 -366 -179 -305 -23 -574 212 -595
522 -20 279 186 535 469 584 64 12 164 5 237 -15z"/>
<path d="M277 442 c-152 -152 -277 -281 -277 -287 0 -13 142 -155 155 -155 5
0 136 126 290 280 l280 280 -80 80 c-44 44 -82 80 -85 80 -3 0 -130 -125 -283
-278z"/>
</g>
</svg>
'''
#******************************************************************************
# Generic settings for images/atrributes
#******************************************************************************
SVG    = DELL_SVG
COLOR  = DELL_COLOR
ADJUST = DELL_ADJ
ICO    = DELL_ICO
COMPANY= "DellEMC"

#******************************************************************************
# Methodes and Classes
#******************************************************************************

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
def _set_value(obj, key, value, expected_type, new=True):
    if expected_type is bool:
        if value not in ['True','False']:
            return False
    if expected_type is int:
        if not value.isdigit():
            return False
    if not new:
        if not hasattr(obj, key):
            return False
    setattr(obj, key, value)
    return True

#******************************************************************************
def change_ascii(s):
    newString = ''
    for c in s:
        if ord(c) >= 128:
            c = '?'
        newString += c
    return newString

#******************************************************************************
def green(s, cr=True, w=80, c=None):
    if c:
        s = '{s:{c}<{n}}'.format(s=s,n=w,c=c)
    try:
        sys.stdout.writelines(u'%s%s%s%s' % (FMT_GREEN, change_ascii(s), FMT_NORMAL, '\n' if cr else ''))
        sys.stdout.flush()
    except:
        print(u'%s'% (change_ascii(s)))

#******************************************************************************
def red(s, cr=True):
    try:
        sys.stdout.writelines(u'%s%s%s%s' % (FMT_RED, change_ascii(s), FMT_NORMAL, '\n' if cr else ''))
        sys.stdout.flush()
    except:
        print(u'%s'% (change_ascii(s)))

#******************************************************************************
def blue(s, cr=True, w=80, c=None):
    if c:
        s = '{s:{c}<{n}}'.format(s=s,n=w,c=c)
    try:
        sys.stdout.writelines(u'%s%s%s%s' % (FMT_BLUE, change_ascii(s), FMT_NORMAL, '\n' if cr else ''))
        sys.stdout.flush()
    except:
        print(u'%s'% (change_ascii(s)))

#******************************************************************************
def _terminate(msg):
    red(msg)
    runUninstall(False)
    if logfile:
        logfile.close()
    sys.exit(1)

#******************************************************************************
def _spCommand(cmd, supressError=False):
    import subprocess as sp
    if supressError:
        process = sp.Popen(cmd, shell = True, stdout = sp.PIPE, stderr = sp.PIPE)
    else:
        process = sp.Popen(cmd, shell = True, stdout = sp.PIPE, stderr = sp.STDOUT)
    out = process.communicate()[0]
    return process.returncode, out

#******************************************************************************
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
        )[20:24])

#******************************************************************************
def getAlarmState(value):
    alarmState = ['ALARM','CLEAR']
    try:
        return alarmState[int(((value-1)/(value+1))*-1)]
    except:
        return 'WARNING'

#******************************************************************************
def getAlarmColor(value):
    alarmColor = ['ff0000','008000']
    try:
        return alarmColor[int(((value-1)/(value+1))*-1)]
    except:
        return 'FFCE33'

###############################################################################
def checkLinuxIfs():
    data = open('/proc/net/dev','r').read()
    faultList = {}
    datastarted = False
    indices = [3,4,11,12]
    for entry in data.splitlines():
        values=entry.split()
        if 'drop' in entry:
            datastarted = True
            continue
        if datastarted == False:
            continue
        total=0
        for i in indices:
            total+=int(values[i])
        if total:
            faultList[values[0].strip(':')]='%s %s %s %s' % (values[indices[0]], values[indices[1]],
                                                             values[indices[2]], values[indices[3]])
    return faultList

###############################################################################
def showDetailProc(pid):
    facilities = {'stack':'Current Stack Trace',
                  'status':'Process Status',
                  'limits':'Process limits',
                  'environ':'Process Environment',
                  }
    data = ''
    if not os.path.exists('/proc/%s' % pid):
        return '<br>PID %s does not exit' % pid
    for f in facilities:
        detail = '<br>'.join(open('/proc/%s/%s' % (pid,f)).read().splitlines())
        data += '<hr><h4 "font-family:Verdana; color: #2e6c80;">%s:</h4><hr><span style="font-family:Courier New;">%s</span>' % (facilities[f], detail)
    return data


###############################################################################
def collect_sys_data(num_high_cpu_users=10, ver=False):
    loadAvrg = ['1min', '5min', '15min'] 
    try:
        num_cores= multiprocessing.cpu_count()
    except:
        num_cores = 1
    perf_data = {}
    ansi_escape = re.compile(r'\x1b[^m]*[m|K]')
    st, raw_top_data = _spCommand('COLUMNS=9999 top -b -c -n 1')
    if st:
        print 'ERRROR: %s: %s' % (st, raw_top_data)
    top_users_count = None
    for line in raw_top_data.splitlines():
        if 'load average:' in line:
            cpu_info = ansi_escape.sub('', line.split('load average:')[1]).split(',')
            for counter, entry in enumerate(cpu_info):
                perf_data['loadAvg_%s' % loadAvrg[counter]] = 100*(float(entry)/num_cores)
        elif 'COMMAND' in line:
            top_users_count = 1
        elif top_users_count and top_users_count <= num_high_cpu_users:
            proc_data = ansi_escape.sub('', line).split()
            if len(proc_data) > 12:
                proc_data[11] += ' %s' % ' '.join(proc_data[12:])
            if 'top' not in proc_data:
                perf_data['TOP(pid,cmd,cpu)_%s' % top_users_count] = (int(proc_data[0]), ' '.join(proc_data[11:]), float(proc_data[8]))
                top_users_count += 1
    st, raw_top_data = _spCommand('COLUMNS=9999 top -b -c -o %MEM -n 1')
    if st:
        print 'ERRROR: %s: %s' % (st, raw_top_data)
    top_users_count = None
    memMap = {}
    for line in raw_top_data.splitlines():
        if 'COMMAND' in line:
            top_users_count = 1
        elif top_users_count and top_users_count <= num_high_cpu_users:
            proc_data = ansi_escape.sub('', line).split()
            if len(proc_data) > 12:
                proc_data[11] += ' %s' % ' '.join(proc_data[12:])
            if 'top' not in proc_data:
                if 'g' in proc_data[5]:
                    proc_data[5] = str(float(proc_data[5].strip('g'))*1024)
                perf_data['TOP_By_MEM(pid,cmd,res)_%s' % top_users_count] = (int(proc_data[0]), ' '.join(proc_data[11:]), float(proc_data[5]))
                top_users_count += 1
                memMap[(int(proc_data[0]), proc_data[11])]=float(proc_data[5])
    st, raw_top_data = _spCommand('iostat -cdtm sda')
    if st == 0:
        for line in raw_top_data.splitlines():
            if 'sda' in line:
                perf_data['iops (tps)'] = line.split()[1]
    mem_data = get_memory()
    perf_data['mem_total']  = mem_data['MemTotal']
    perf_data['mem_free']   = mem_data['MemFree']+mem_data['Buffers']+mem_data['Cached']
    perf_data['swap_total'] = mem_data['SwapTotal']
    perf_data['swap_free']  = mem_data['SwapFree']
    st, raw_top_data = _spCommand('df -m /')
    if st == 0:
        for line in raw_top_data.splitlines():
            if line.startswith('/dev'):
                perf_data['disk_used'] = line.split()[4].strip('%')
    if ver:
        for ent in perf_data:
            print '%-20s\t= %s' % ent
    return perf_data, memMap


###############################################################################
def importPlugins(moduleList, moduleInst, log, directory='plugins'):
    import copy, imp
    """ Imports the .py files in the plugin directory,
    returns a list of the plugins.
    Pass in dir to scan, or default looks for services """
    fileDict = {}
    if moduleList is not None:
        for module in moduleList:
            fileDict[module.__name__]=module
    else:
        moduleList=[]
        moduleInst={}
    allFiles = os.listdir(directory)
    missingModules = copy.copy(moduleList)
    for file in allFiles:
        moduleName, ext = os.path.splitext(file)
        # Important, ignore .pyc and __init__.py files.
        if ext == '.py' and moduleName != '__init__' and moduleName.startswith('.') == False:
            s,o=_spCommand('python -m compileall %s' % (os.path.join(directory,file)))
            if s == 0:
                os.unlink(os.path.join(directory,file))
                os.rename(os.path.join(directory, '%s.pyc' % moduleName), os.path.join(directory, '%s.plg' % moduleName))
                ext = '.plg'
        if ext == '.plg':
            moduleToBeLoaded = os.path.join(directory, moduleName)
            #log('processing to load module: %s' % (moduleToBeLoaded))
            module = fileDict.get(moduleToBeLoaded)
            if module:
                try:
                    missingModules.remove(module)
                except:
                    pass
                #log('Module %s exists already' % (module.__name__))
            else:
                try:
                    module = imp.load_compiled(moduleToBeLoaded, '%s.plg' % moduleToBeLoaded)
                    #reload(module)
                    moduleList.append(module)
                except Exception,e:
                    log('import failed for %s. Error %s\n%s' % (moduleToBeLoaded,e,traceback.format_exc()), 1)
                    if module in moduleList:
                        moduleList.remove(module)
                    continue
                try:
                    moduleInst[module.__name__] = module.SystemStatusPlugin(exeCmd=_spCommand, configFile=config_file)
                except Exception,e:
                    log('instantiate failed for %s. Error %s\n%s' % (moduleToBeLoaded, e, traceback.format_exc()), 1)
                    moduleList.remove(module)
                    continue
                try:
                    #log('Calling %s.getDesc()' % (module.__name__))
                    val = moduleInst[module.__name__].getDesc()
                    #log('Initialized %s: %s' % (module.__name__, val))
                except Exception,e:
                    log('getDesc() faield for %s. Error %s\n%s' % (moduleToBeLoaded, e,traceback.format_exc()), 1)
                    del moduleInst[module.__name__]
                    moduleList.remove(module)
                    continue
    #remove any file that is not in the directory
    for module in missingModules:
        log('Removing %s' % (module.__name__))
        del moduleInst[module.__name__]
        moduleList.remove(module)

    return moduleList, moduleInst

###############################################################################
# Class to communicate through via URLs
###############################################################################
class WebHookHandler(BaseHTTPRequestHandler):
    server_version = "HookHandler/0.1"
    def logPrint(self):
        csvTohtml = ''
        with open(DNLD_URL+'.log', 'rb') as csvfile:
            csvTohtml = '''
            <!doctype html>
            <html><head><title>LOGS</title>
            </head><body>
            <table border="1">
             <thead><tr>
            '''
            try:
                csvdata = csv.reader(csvfile, delimiter=',', quotechar='"')
            except Exception, e:
                csvTohtml += 'Reader: %s</tbody></table></body></html>' % e
                return csvTohtml
            header=True
            try:
                for row in csvdata:
                    if header:
                        for c in row:
                            csvTohtml += '<td>%s</td>' % c
                        csvTohtml += '</tr></thead><tbody>'
                        header=False
                        continue
                    csvTohtml += '<tr>'
                    for c in row:
                        csvTohtml += '<td>%s</td>' % c
                    csvTohtml += '</tr>'
            except Exception, e:
                csvTohtml += '<tr><td>Entry ERROR: %s</td></tr>' %e 
            csvTohtml += '</tbody></table></body></html>'
        return csvTohtml

    def getExtraInfo(self):
        htmData = ''
        if os.path.exists('/etc/OS10-release-version'):
            try:
                with open('/etc/OS10-release-version') as os10Info:
                    for l in os10Info:
                        if 'OS_VERSION' in l:
                            htmData += '<strong>Version</strong>:<span class="right">%s</span><br>' % (l.split('=')[1].replace('"',''))
                        if 'PLATFORM' in l:
                            htmData += '<strong>Platform</strong>:<span class="right">%s</span><br>' % (l.split('=')[1].replace('"',''))
            except Exception, e:
                htmData = '<strong>Version</strong>:<span class="right">Unknown</span><br><strong>Platform</strong>:<span class="right">Unknown</span>'
                self.context.debugLog('EXCEPTION: accessing version/platform: %s\n%s\n' % (
                                        e, traceback.format_exc()), 2)
        return htmData

    def getConfigDics(self, widgetCount, chartCount):
        try:
            num_cores= multiprocessing.cpu_count()
        except:
            num_cores = 1

        configDic={}
        finalDic = {}
        #reset for maximum size to avoid undefined holders in the template
        for c in range(max(widgetCount, chartCount)):
            configDic['GageObj%s' % c]  =''
            finalDic['code%s' % c]      =''
            configDic['chart%s' % c]    =''

        #process for all plugins and create and fill widgets
        wCnt    = 0
        cCnt    = 0
        chCntp  = 0 
        
        #populate non-charts first to avoid blank spaces on rows of COLS_PER_ROW's
        for m in self.context.modList:
            desc = self.context.modIns[m.__name__].getDesc()
            if (len(self.context.modIns[m.__name__].getCodeObject()) > 1 or 
                len(self.context.modIns[m.__name__].getScripts()) > 1 or
                len(self.context.modIns[m.__name__].getChartObject()) > 1):
                if self.context.modIns[m.__name__].plugType == 'chart':
                    self.context.modIns[m.__name__].hsize = CHART_WIDTH*int(self.context.pluginPerRow)
                configDic['GageObj%s' % wCnt] =  self.context.modIns[m.__name__].getScripts()
                if len(self.context.modIns[m.__name__].getCodeObject()) > 1:
                    finalDic['code%s' % cCnt]     =  self.context.modIns[m.__name__].getCodeObject()
                    cCnt += 1
                wCnt += 1
            if self.context.modIns[m.__name__].plugType is 'chart':
                configDic['chart%s' % chCntp]   =  self.context.modIns[m.__name__].getChartObject()
                chCntp += 1
            finalDic['%sValue'%desc]     =  eval('self.context.%sValue' % desc)
            finalDic['%sLimit'%desc]     =  eval('self.context.%sLimit' % desc)
        #finish of the final dictionary for template.
        finalDic['color']       = COLOR
        finalDic['logo']        = SVG
        finalDic['height']      = ADJUST
        finalDic['icon']        = ICO
        finalDic['title']       = 'System Status'
        finalDic['host']        = socket.gethostname() 
        finalDic['ip']          = get_ip_address('eth0')
        finalDic['cores']       = num_cores
        finalDic['blank_cells'] = '<td></td>'*(int(self.context.pluginPerRow)-2) # Overallstatus and Info box
        finalDic['width']       = CHART_WIDTH * int(self.context.pluginPerRow)
        finalDic['page_width']  = TABLE_CELL_W * int(self.context.pluginPerRow)
        finalDic['extras']      = self.getExtraInfo()
        finalDic['url']         = SET_URL
        finalDic['refreshRate'] = self.context.args.frequency
        finalDic['company']     = COMPANY
        finalDic['version']     = SERVICE_VERSION
        finalDic['credit']      = ''

        return configDic, finalDic

    def htmlStatus(self, detail=False):
        global working_dir

        with open(os.path.join(working_dir, 'templates/main.xhtml')) as main_temp:
            tmpData = main_temp.read()
 
        widgetCount = 0
        chartCount = 0
        #figure out the largest number of either charts or dials/bubls
        for m in self.context.modList:
            if self.context.modIns[m.__name__].plugType == 'chart':
                chartCount += 1
            if (len(self.context.modIns[m.__name__].getCodeObject()) > 1 or
                len(self.context.modIns[m.__name__].getChartObject()) > 1):
                widgetCount += 1

        #round up to a multiple of COLS_PER_ROW (COLS_PER_ROW widgets per row in the HTML page)
        cols=int(self.context.pluginPerRow)
        widgetCount = widgetCount+(cols-widgetCount%cols if widgetCount%cols else 0)

        #based on # of plugins, build and modify the main template
        codes=''
        charts=''
        gageObjs=''
        for i in range(max(widgetCount, chartCount)):
            if i < chartCount:
                charts+='${chart%s}' % i
            if i < widgetCount:
                gageObjs+='${GageObj%s}' % i
                if i % int(self.context.pluginPerRow) == 0:
                    codes+='</tr><tr>'
                codes+='<td>$${code%s}</td>' % i

        localTmpData = tmpData.replace('${charts}',charts).replace('${codes}',codes).replace('${GageObjs}',gageObjs)

        #create the template based on the modification to the template feeder
        mainTemplate = Template(localTmpData)

        configDic, finalDic = self.getConfigDics(widgetCount, chartCount)

        #now create the main page based on the template - two level templates to create plugin holders, and 
        #then add the necessary config params.
        tempTplt = Template(mainTemplate.substitute(configDic))
        self.wfile.write(tempTplt.substitute(finalDic))

    def buildOverallPage(self):
        global working_dir

        with open(os.path.join(working_dir, 'templates/basic_style.xhtml')) as basic_temp:
            basic_style = basic_temp.read()

        #provide data on overall state
        status ='<strong>%-13s</strong>:<br><table class="main-table" border="1">' % 'Thresholds'
        for m in self.context.modList:
            name = self.context.modIns[m.__name__].getDesc()
            if self.context.modIns[m.__name__].postalarm:
                status += '<tr><td>%sLimit</td><td class="main-table-td-c">%5s%s</td></tr>' % (name, 
                                                                       round(float(eval('self.context.%sLimit' % name)),2),
                                                                       self.context.modIns[m.__name__].unit)
        status += '</table><br><br><strong>%-13s</strong>:<br><table class="main-table" border="1">' % 'Current' 
        for m in self.context.modList:
            name = self.context.modIns[m.__name__].getDesc()
            if self.context.modIns[m.__name__].postalarm:
                status += '<tr><td>%s</td><td class="main-table-td-c">%5s%s</td></tr>' % (name, 
                                                                                          round(float(eval('self.context.%sValue' % name)),2),
                                                                                          self.context.modIns[m.__name__].unit)
        status += '</table><br>%-13s' % '<br><strong>Alarms</strong>:<br><table class="main-table" border="1">' 
        for m in self.context.modList:
            name = self.context.modIns[m.__name__].getDesc()
            if self.context.modIns[m.__name__].postalarm:
                self.context.modIns[m.__name__].getConfigData()
                try:
                    enabled = eval('self.context.modIns[m.__name__].%s_enabled' % name)
                except:
                    enabled = True
                status += '<tr><td>%s</td><td class="main-table-td-c">%5s</td></tr>' % (name, 
                                "DISABLED" if enabled == False else ['OK',"ALARM"][int(eval('self.context.%s_alarm' % name))])
        html='''
        <html><head>%s<title>Overall Status</title></head><body>
        <span style="font-family:Calibri; font-size: 34px; color: #0485cb;">Overall Status:</span>
        <span style="font-family:Calibri; font-size: 34px; color: #%s;">%s</span><br>
        <span style="font-family:Verdana; font-size: 12px;">%s
        </span>
        %s
        </table>
        <br>
        <iframe name="hiddenFrame" class="hide"></iframe>
        <form method="post" action="/api/v1/set" enctype="application/json" target="hiddenFrame" onsubmit="gourl()">
        <legend>Configurations</legend>
        <table class="main-table"><tbody>
        <tr><td>Number of plugins per row:</td><td><input name="pluginPerRow" type="input" value="%s"/></td></tr>
        </tbody></table>
        <p><input name="Submit"  type="submit" value="Commit Changes"/></p>
        </form>
        </body></html>
        ''' % (basic_style, getAlarmColor(self.context.overallStatus),
               getAlarmState(self.context.overallStatus), status,
               self.context.reportLeak(), self.context.pluginPerRow)
        return html

    def sendPageReply(self, code=200, ctype='application/json'):
        self.context.debugLog('STATUS: %s, Content-Type: %s\n' % (code, ctype))
        if code is 400:
            self.send_response(code, 'Bad Request: record does not exist')
        else:
            self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.end_headers()

    def do_GET(self):    ### HANDLE GET OPERATIONS
        global working_dir
        try:
            self.context.debugLog('GET path: %s' % self.path)
            if ROOT_URL in self.path and os.path.exists(self.path.split(ROOT_URL+'/')[-1].split('?')[0]):
                self.sendPageReply(ctype = 'text/html')
                self.context.debugLog('Sending file')
                self.wfile.write(open(self.path.split(ROOT_URL+'/')[-1].split('?')[0]).read())
            elif  None != re.search(HELP_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                html='''
                    <!doctype html>
                    <html><head>
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    </head><body>
                    <a href="html">...%s</a><br>
                    <a href="json">...%s</a><br>
                    <a href="status">...%s</a><br>
                    <a href="get">...%s</a><br>
                    <a href="report">...%s</a><br>
                    </body></html>
                ''' % (HTML_URL, JSON_URL, STATUS_URL, GET_URL, REPORT_URL)
                self.wfile.write(html)
            elif None != re.search(STATUS_URL+'*', self.path):
                self.sendPageReply()
                self.wfile.write(self.context.currentStatus)
            elif None != re.search(JSON_URL+'*', self.path):
                self.sendPageReply()
                modName = os.path.basename(self.path)
                if modName == 'json':
                    self.wfile.write(self.context.getJsonStatus())
                else:
                    for m in self.context.modList:
                        name = self.context.modIns[m.__name__].getDesc()
                        if modName in name:
                            self.wfile.write(self.context.modIns[m.__name__].getJsonDetail())
            elif None != re.search(HTML_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                self.htmlStatus()
            elif None != re.search(DNLD_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                if os.path.exists(DNLD_URL+'.log'):
                    self.context.debugLog('Log File exists')
                    self.wfile.write(self.logPrint())
            elif None != re.search(GET_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                html='Please install CPS_DEBUG plugin for this feature!'
                try:
                    pid = self.path.split('%s/' % GET_URL)[1]
                except:
                    pid=None
                for m in self.context.modList:
                    name = self.context.modIns[m.__name__].getDesc()
                    if 'cpsDebug' in name:
                        if pid and ('/' in pid or pid.isdigit() == False):
                            fileters = []
                            try:
                                pid,filter_string=pid.split('?')
                                fileters = filter_string.split(',')
                            except:
                                pass
                            html = self.context.modIns[m.__name__].getCPS(pid, fileters)
                        else:
                            html = self.context.modIns[m.__name__].getHtmlDetail(pid)
                self.wfile.write(html)
            elif None != re.search(FETCH_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                val = None
                label = ''
                if 'overall' in self.path:
                    label = 'overall'
                    val = self.context.overallStatus
                else:
                    var = self.path.split(FETCH_URL)[1].strip()
                    for m in self.context.modList:
                        name = self.context.modIns[m.__name__].getDesc()
                        if var in name:
                            label = var
                            val = eval('self.context.%s_alarm' % var)
                self.context.debugLog('Reporting to fetch: %s=%s\n' % (label,val),2)
                self.wfile.write(val)
            elif None != re.search(REPORT_URL+'*', self.path):
                self.sendPageReply(ctype = 'text/html')
                try:
                    modName = os.path.basename(self.path)
                except:
                    modName = 'overall'
                html = 'Installed plugins do not provide any data!'
                if modName in 'overall':
                    html = self.buildOverallPage()
                else:
                    for m in self.context.modList:
                        if modName in self.context.modIns[m.__name__].getDesc():
                            html = self.context.modIns[m.__name__].getHtmlDetail()
                            break
                self.wfile.write(html)
            elif None != re.search(PULLDATA_URL+'*', self.path):
                data = None
                label=self.path
                limit = False
                var = os.path.basename(self.path).split('?num=')[0].strip()
                if var.endswith('??'):
                    var = var.strip('??')
                    limit=True
                for m in self.context.modList:
                    name = self.context.modIns[m.__name__].getDesc()
                    if var in name:
                        label = var
                        if limit:
                            data = eval('self.context.%sLimit' % var)
                        else:
                            data = eval('self.context.%sValue' % var)
                self.sendPageReply(ctype = 'text/html')
                self.context.debugLog('Reporting to data pull: %s=%s\n' % (label, data),2)
                self.wfile.write('&value=%s' % data)
            elif None != re.search('.ico*', self.path):
                filename = os.path.basename(self.path)
                if os.path.exists('%s/images/%s' % (working_dir, filename)):
                    self.sendPageReply(ctype = 'image/x-icon')
                    self.wfile.write(open('%s/images/%s' % (working_dir, filename), "rb").read())
            else:
                self.sendPageReply(ctype = 'text/html')
                htm='''
                <meta http-equiv="refresh" content="0; %s" />
                <meta http-equiv="pragma" content="no-cache">
                <script type="text/javascript">
                window.location.replace('%s')
                </script>
                ''' % (HTML_URL, HTML_URL)
                self.wfile.write(htm)
                #self.wfile.write('<meta http-equiv="refresh" content="0; URL=\'%s\'" />' % HTML_URL)
        except Exception,e:
            self.wfile.write('Failed [%s]: %s\n%s\n' % (self.localPath, e, '<br>'.join(traceback.format_exc().splitlines())))
            self.context.debugLog('Failed: %s\n%s' % (e, traceback.format_exc()), 1)


    def do_POST(self):   ### HANDLE POST OPERATIONS
        if None != re.search(SET_URL+'*', self.path):
            self.context.debugLog('POST path: %s' % self.path)
            try:
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                self.context.debugLog('POST=PATH: %s, CTYPE: %s\n' % (self.path, ctype))
                if ctype == 'application/x-www-form-urlencoded':
                    length = int(self.headers.getheader('content-length'))
                    self.context.debugLog('Length: %s\n' % (length))
                    data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
                    self.context.debugLog('data: %s\n' % (data))
                    userConfData={}
                    for e in data:
                        if 'Submit' in e:
                            continue
                        self.context.debugLog('SET DATA: %s=%s\n' % (e,data[e][0]), 2)
                        #exec('self.context.%s = "%s"' % (e,data[e][0]))
                        _set_value(self.context, e,data[e][0], str)
                        userConfData[e]=eval('self.context.%s' % e)
                    setConfigData(userConfData)
                if ctype == 'application/json': #SET operation through browser
                    length = int(self.headers.getheader('content-length'))
                    data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
                    payload = eval(data.keys()[0])
                    self.context.debugLog('Data: %s\n' % (payload), 2)
                    if payload.get('SET'):
                        var_set = payload.get('SET')
                        for e in var_set:
                            if 'Limit' in e:
                                self.context.debugLog('SET JSON DATA: %s=%s\n' % (e,var_set[e]))
                                #exec('self.context.%s = %s' % (e,var_set[e]))
                                _set_value(self.context, e,var_set[e], str)
                            else:
                                try:
                                    eval('self.context.%s' % e)
                                    self.context.debugLog('self.context.%s = %s' % (e,var_set[e]), 2)
                                    #exec('self.context.%s = %s' % (e,var_set[e]))
                                    _set_value(self.context, e,var_set[e], str)
                                except:
                                    pass
            except Exception, e:
                self.context.debugLog('ERROR: %s\n' % e, 1)
            self.sendPageReply()
        else:
            self.context.debugLog('URL: %s\n' % (self.path))
            self.sendPageReply(code=403)
 

###############################################################################
# Class to implement shutdwn
###############################################################################
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  allow_reuse_address = True
 
  def shutdown(self):
    self.socket.close()
    HTTPServer.shutdown(self)

###############################################################################
# Class to run webserver as a Thread
###############################################################################
class HttpServer():
  def __init__(self, ip, port, context):
    self.handle = WebHookHandler
    self.handle.context = context
    self.handle.localPath = context.args.path
    os.chdir(self.handle.localPath)
    self.server = ThreadedHTTPServer((ip,port), self.handle)
    if context.secureUrl:
        self.server.socket = ssl.wrap_socket (self.server.socket, 
                                              certfile=context.args.cert, server_side=True)
 
  def start(self):
    self.server_thread = threading.Thread(target=self.server.serve_forever)
    self.server_thread.daemon = True
    self.server_thread.start()
 
  def waitForThread(self):
    self.server_thread.join()
 
 
  def stop(self):
    self.server.shutdown()
    self.waitForThread()

###############################################################################
###############################################################################
class ServiceDaemon(object):
    """
    A generic daemon class.
    Usage: subclass the ServiceDaemon class and override the run() method
    """
    def __init__(self, name, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', ver=False):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.name = name
        self.ver = ver

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
        import datetime
        blue(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "{}: already running?, pidfile {} already exists.\n".format(self.name, self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)

        # Start the daemon
        if self.ver:
            blue('{}: starting.'.format(self.name))                
        sys.stdout.flush()
        self.daemonize()
        self.run()

    def stop(self):
        global URL_TYPE
        """
        Stop the daemon
        """
        try:
            data={'SET': {'stop_requested' : 'True'}}
            r = requests.post(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, SET_URL), 
                              data=json.dumps(data), 
                              headers={'Content-Type': 'application/json'}, verify=False)
            green('Stopping Service [%s]' % (r.status_code))
            time.sleep(2)
        except:
            red('Service is not running')
            pass
        try:
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
        except:
            pass
        if self.ver:
            green('{}: stopped.'.format(self.name))                

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        green('Waiting for service to stop...')
        while self.running():
            time.sleep(1)
        self.start()

    def running(self):
        global URL_TYPE
        """
        Check for the daemon
        """
        try:
            r = requests.get(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, STATUS_URL), verify=False)
            if r.status_code == 200:
                return True
        except:
            pass
        return False

    def status(self):
        """
        Report status of the daemon
        """
        if not self.running():
            red('{}: is NOT running'.format(self.name))
        else:
            green('{}: is running'.format(self.name))
        return 0

    def run(self):
        """
        You should override this method when you subclass ServiceDaemon. It will be called after the process has been
        daemonized by start() or restart().
        """
###############################################################################
###############################################################################
class SysStatusDaemon(ServiceDaemon):
    def __init__(self, name, pidfile, io_parms, args):
        global URL_TYPE
        self.args = args
        super(SysStatusDaemon, self).__init__(name, pidfile, stdin='/dev/null', 
                                              stdout=io_parms['stdout'],
                                              stderr=io_parms['stderr'], 
                                              ver=args.verbose)
        self.secureUrl = True
        if not os.path.exists(args.cert):
            self.debugLog('Change to non-secure', 3)
            URL_TYPE = 'http'
            self.secureUrl = False
        else:
            import urllib3
            urllib3.disable_warnings()
        self.stop_requested = False
        self.pluginPerRow = int(args.col)
        self.logfile = None
        self.ifFaults = 0
        self.collected_data = []
        self.currentData = {}
        self.memUsageStats = {}
        self.leakCandidate = []
        self.currentStatus = ''
        def signal_handler(*args):
            self.stop_requested = True
            if self.logfile:
                self.logfile.close()
                self.logfile = None
        signal.signal(signal.SIGINT, signal_handler)
        self.soackedOverallStatus = 0
        self.overallStatus = 0
        self.modList, self.modIns = importPlugins(None, None, self.debugLog)
        self.httpServer = None
        

    def getDefaults(self, configData):
        for m in self.modList:
            name = self.modIns[m.__name__].getDesc()
            if configData.get('%sLimit' % name) is None:
                if self.modIns[m.__name__].defaultLimit is not None:
                    configData['%sLimit' % name] = self.modIns[m.__name__].defaultLimit
            if configData.get('%sLimit' % name) is not None:
                #exec('self.%sLimit=%s' % (name, configData['%sLimit' % name]))
                _set_value(self, '%sLimit' % name, configData['%sLimit' % name], str)
        return configData

    def get(self, param):  
        global URL_TYPE
        """
        Get System Status
        """      
        if param and param.endswith('??'):
            r = requests.get(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, PULLDATA_URL + '/' + param), verify=False)
        elif param and param.endswith('?'):
            r = requests.get(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, PULLDATA_URL + '/' + param.strip('?')), verify=False)
        elif param:
            r = requests.get(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, FETCH_URL+param), verify=False)
        else:
            r = requests.get(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, STATUS_URL), verify=False)
        if r.status_code == 200:
            print(r.text)
        else:
            red('ERROR[%s]' % r.status_code)
        return 0

    def set(self, data):       
        global URL_TYPE 
        data={'SET': data}
        r = requests.post(URL_TYPE+'://%s:%s%s' % (self.args.host, self.args.port, SET_URL), 
                          data=json.dumps(data), 
                          headers={'Content-Type': 'application/json'}, verify=False)
        if r.status_code == 200:
            green('OK')
        else:
            red('FAILED: %s' % (r.status_code))
        return 0

    def debugLog(self, msg, level=3):
        if self.args.verbose >= level:
            sys.stdout.write('%s\n' % (msg))
            sys.stdout.flush()

    def getJsonStatus(self):
        jsonMsg = {'STATUS':
                        {'SYSTEM':getAlarmState(self.overallStatus-1),
                         'SUB_SYSTEMS':{},
                         'THRESHOLDS':{},
                         'THRESHOLDS':{},
                         'CURRENT':{},
                         }
                  }
        for m in self.modList:
            name = self.modIns[m.__name__].getDesc()
            jsonMsg['STATUS']['SUB_SYSTEMS'][name]  = getAlarmState(eval('self.%s_alarm' %name))
            jsonMsg['STATUS']['THRESHOLDS'][name]   = round(float(eval('self.%sLimit' %name)))
            jsonMsg['STATUS']['CURRENT'][name]      = round(float(eval('self.%sValue' %name)))
        
        return json.dumps(jsonMsg)

    #text based reporting method
    def getStatus(self):
        status  = '==============================================================================================\n'
        status += '%-13s' % 'Thresholds:\n' 
        for m in self.modList:
            name = self.modIns[m.__name__].getDesc()
            if self.modIns[m.__name__].defaultLimit is not None:
                status += '%sLimit=%5s%s ' % (name, round(float(eval('self.%sLimit' % name)),2),
                                               self.modIns[m.__name__].unit)
        status += '\n%-13s' % 'Current:\n' 
        for m in self.modList:
            name = self.modIns[m.__name__].getDesc()
            if self.modIns[m.__name__].defaultLimit is not None:
                status += '%s=%5s%s ' % (name, round(float(eval('self.%sValue' % name)),2), 
                                          self.modIns[m.__name__].unit)
        status += '\n=============================================================================================='
        status += '\n%-15s        %s\n' % ('Overall Status:', getAlarmState(self.overallStatus))
        status += '\n=========================================================\nALARMS:\n'
        for m in self.modList:
            name = self.modIns[m.__name__].getDesc()
            if self.modIns[m.__name__].postalarm:
                status += '=====================+===================================\n'
                status += '%-20s |        %s\n' % (name, getAlarmState(eval('self.%s_alarm' %name)))
        if len(self.leakCandidate):
            status += '=========================================================\n'
            for e in self.leakCandidate:
                status += 'Possible leak in [PID:%s, CMD:%s]\n' % (e[0], e[1])
        status += '=========================================================\n'
        return status

    def reportLeak(self):
        htmlData = ''
        if len(self.leakCandidate):
            htmlData = '<h2 style="font-family:Verdana; color: #2e6c80;">Possible Memory Leak In Progress:</h2>'
            for e in self.leakCandidate:
                htmlData += '\nPID:<a href="%s/%s"><span style="font-family:Verdana; color: #2e6c80;">%s</span></a>, CMD:<span style="font-family:Verdana; font-size: 10px;">%s</span><br>' % (
                            GET_URL, e[0], e[0], e[1])
        return htmlData

    def evalMemInfo(self, memMap):
        leakCandidate=[]
        for ent in memMap:
            if self.memUsageStats.get(ent):
                if memMap[ent] > self.memUsageStats[ent]['data']:
                    self.memUsageStats[ent]['cnt'] += 1.0
                elif memMap[ent] < self.memUsageStats[ent]['data']:
                    self.memUsageStats[ent]['cnt'] -= 1.0
                else:
                    if self.memUsageStats[ent]['cnt'] > 0.0:
                        self.memUsageStats[ent]['cnt'] -= 0.1
            else:
                self.memUsageStats[ent]={'cnt':0.0,'data':memMap[ent]}
            self.memUsageStats[ent]['data'] = memMap[ent]
        deletedList = []
        for e in self.memUsageStats:
            if memMap.get(e) is None:
                deletedList.append(e)
        for e in deletedList:
            del self.memUsageStats[e]
        if self.args.verbose:
            self.debugLog('Leak RAW Data:\n')
        for e in self.memUsageStats:
            if self.args.verbose:
                self.debugLog('ID:[%s,%s], USAGE:%s, COUNT:%s\n' % (e[0],e[1],self.memUsageStats[e]['data'],
                                                                    self.memUsageStats[e]['cnt']),2)
            if self.memUsageStats[e]['cnt'] > 10.0:
                leakCandidate.append(e)
        return leakCandidate

    def log_csv(self, collect, collect_data):
        header=None
        if self.logfile is None:
            with os.fdopen(os.open('/etc/logrotate.d/sys_status', os.O_WRONLY | os.O_CREAT, 0o644), 'w') as logf:
                logf.write(logrotate)

            if not os.path.exists(self.args.log):
                header=['Date'] #allow header only once in a file
            self.logfile = open(self.args.log, 'a+')
            
        #capture in CSV format
        writer = csv.writer(self.logfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data=[time.strftime('%m/%d/%y %H:%M:%S', time.gmtime(collect))]
        for e in collect_data:
            if header:
                header.append(e[0])
            data.append(e[1])
        if header:
            writer.writerow(header)
        writer.writerow(data)
        self.logfile.flush()

    def check(self):
        localOverallStatus = 0
        self.modList, self.modIns = importPlugins(self.modList, self.modIns, self.debugLog)
        yellowalarm=0
        for m in self.modList:
            modName = self.modIns[m.__name__].getDesc()
            try:
                eval('self.%s_alarm' % (modName))
            except:
                self.debugLog('%s' % (self.modIns[m.__name__].getAlarmDetail()))
            try:
                threshold = eval('self.%sLimit' % modName)
            except Exception, e:
                self.debugLog('EXCEPTION: access %s: %s' % (modName, e), 1)
                threshold = 0
            try:
                a,v = self.modIns[m.__name__].getAlarm(threshold)
                #exec('self.%s_alarm=%s' % (modName, a))
                _set_value(self, '%s_alarm' % modName, a, str)
                #exec('self.%sValue=%s' % (modName, v))
                _set_value(self, '%sValue' % modName, v, str)
                #exec('self.%sLimit=%s' % (modName, threshold))
                _set_value(self, '%sLimit' % modName, threshold, str)
                if self.modIns[m.__name__].postalarm:
                    currentAlarm = eval('self.%s_alarm' % modName)
                    currentValue = eval('self.%sValue' % modName)
                    if currentValue < 0:
                        yellowalarm += 1 
                    localOverallStatus += currentAlarm
            except Exception, e:
                self.debugLog('EXCEPTION: in %s: %s: %s' % (modName, e, traceback.format_exc()),1)
        if localOverallStatus == 0:
            #adjust value based on a leaks detected
            localOverallStatus -= int(len(self.leakCandidate)>0)
            localOverallStatus -= yellowalarm
        if self.soackedOverallStatus == localOverallStatus:
            self.overallStatus = self.soackedOverallStatus
        self.soackedOverallStatus = localOverallStatus
        for m in self.modList:
            if self.modIns[m.__name__].plugType == 'report':
                ret = self.modIns[m.__name__].getData({'overall': getAlarmState(self.overallStatus)})

        #the follow call is just to make things prepared for the query.
        #It can be easily removed, if GET operation will not happen at the Linux shell.
        self.currentStatus = self.getStatus()
        
    def run(self):
        global logfile
        super(SysStatusDaemon, self).run()
        #setup a HTTP server to use as a communication method
        self.httpServer = HttpServer(self.args.host, self.args.port, self)
        #start the server as a thread to interact with the users
        self.httpServer.start()
        #register for CPS notifications for:
        #Interface counters, FAN, Temp, and other NPU related faults

        self.debugLog('Service Daemon Started: PID %s\n' % (os.getpid()))
        #Force check on first iteration
        checkTime = time.time()-self.args.frequency+1
        logTime   = time.time()-self.args.frequency+1
        #the self.stop_request is accessed and set by the thread
        minAppDelay = 5
        while(self.stop_requested == False):
            if time.time()-checkTime > minAppDelay:
                checkTime = time.time()
                #run a check on the latest data from plugins to determine overall status
                self.check()
            #only log and check for leaks at the given frequency
            if time.time()-logTime > self.args.frequency:
                logTime = time.time()
                #collect resource data
                self.currentData, memMap = collect_sys_data()
                #process top 10 memory users for possible leak
                self.leakCandidate = self.evalMemInfo(memMap)
                #sort the data, for proper pushing to the log
                perf_data = sorted(self.currentData.items(), key=operator.itemgetter(0))
                #log the data to the disk
                self.log_csv(time.time(), perf_data)
            time.sleep(1)
        
        #stop the commiunication thread.
        self.httpServer.stop()
        #close the log file.
        if self.logfile:
            self.logfile.close()
            self.logfile = None


###############################################################################
def getConfigData():
    global default_config
    diskData = {}
    if os.path.exists(config_file):
        file=open(config_file, 'r')
        data = file.read()
        file.close()
        for l in data.splitlines():
            if not l.strip().startswith('#') and '=' in l:
                k,v = l.split('=')
                diskData[k] = v
        for e in diskData:
            default_config[e] = diskData.get(e)
    setConfigData(default_config)
    return default_config

###############################################################################
def setConfigData(newdata):
    global default_config
    for e in newdata:
        default_config[e] = newdata[e]
    file=open(config_file,'w')
    for e in default_config:
        file.write('%s=%s\n' % (e, default_config[e]))
    file.close()
    return default_config

###############################################################################
def start(srvcD, opts, args):
    if opts.verbose:
        blue('Status Service daemon starting')
    srvcD.start()
    if opts.verbose:
        blue('Status Service daemon ended')
    return 0

###############################################################################
def stop(srvcD, opts, args):
    if opts.verbose:
        blue('Status Service daemon stopping')
    srvcD.stop()
    if opts.verbose:
        blue('Status Service daemon stopped')
    return 0

###############################################################################
def restart(srvcD, opts, args):
    if opts.verbose:
        blue('Status Service daemon restarting')
    srvcD.restart()
    if opts.verbose:
        blue('Status Service daemon ended')
    return 0

###############################################################################
def status(srvcD, opts, args):
    srvcD.status()
    return 0

###############################################################################
def get(srvcD, opts, args):
    srvcD.get(args[1] if len(args)>1 else None)
    return 0

###############################################################################
def set(srvcD, opts, args):
    global default_config
    srvcD.set(default_config)
    return 0

###########################################################################
def get_sensor(sensor=None, stype=None, host='http://127.0.0.1', port=PORT):
    """
    @sensor - sensor name. 
    @stype - threshold, value, or fault-state of a sensor. If no stype provided, 
             return all the three attributes.
    @return - dict of attribute name and value. Return none if service is not available.
    """
    import requests
    os.chdir(working_dir)
    global API_VER
    retDict = {'threshold':None, 'value':None, 'fault-state':None, 'description':None}
#    ROOT_URL    = '/api/v%s' % API_VER
#    STATUS_URL  = '%s/status' % ROOT_URL
#    FETCH_URL   = '%s/fetch' % ROOT_URL #used by bulb_script to get alarms to bulb widgets
#    PULLDATA_URL= '%s/data' % ROOT_URL  #used by dial_script to get data to dial widgets

    modList, modInst = importPlugins(None, None, blue)
    try:
        for m in modList:
            if sensor == modInst[m.__name__].getDesc():
                retDict['threshold'] = modInst[m.__name__].defaultLimit
                retDict['description'] = modInst[m.__name__].getInfo()
                a, v = modInst[m.__name__].getAlarm(retDict['threshold'])
                retDict['value'] = v
                retDict['fault-state'] =  a
                break
        return retDict
    except:
        return None
##############################################################################
# Provide a list of all sensor names
def get_sensor_list(directory='plugins'):
    os.chdir(working_dir)
    ret = []
    import requests
    global API_VER
    modList, modInst = importPlugins(None, None, blue)
    try:
        for m in modList:
            if modInst[m.__name__].postalarm:
                ret.append(modInst[m.__name__].getDesc())
    except:
        return None
    return ret

###############################################################################
def get_overall_status():
    """
    @return - overall system status (True/False) based on sensor fault states.
              Return None if service is not available.
    """
    os.chdir(working_dir)
    sensor_list = get_sensor_list()
    for i in range(len(sensor_list)):
        retDict = get_sensor(sensor_list[i])
        if retDict != None and retDict['fault-state'] == True:
            return True
        if retDict is None:
            return None
    return False

###############################################################################
###############################################################################
###############################################################################
if __name__ == '__main__':
    commands = ['start', 'stop', 'restart', 'status', 'get', 'set']

    if os.getuid() != 0:
       red("You must have root permissions, please use sudo!")
       sys.exit(1)

    os.chdir(working_dir)
    confData = getConfigData()
    from optparse import OptionParser
    
    # Define options
    parser = OptionParser(usage='''
Sys Status Service [%s]

%%prog [start|stop|restart|status|get|set] [options]
        ''' % SERVICE_VERSION)

    parser.add_option("--host", dest="host", default=confData.get('HOST'), 
                      action  = 'store', metavar='HOSTNAME',
                      help="Hostname for local REST server. default:%default")
    parser.add_option("--port", dest="port", default=int(confData.get('PORT')), 
                      action  = 'store', metavar='HOSTNAME', type=int,
                      help="Port for local REST server. default:%default")
    parser.add_option("--verbose", dest="verbose",  type=int,
                      default=0,  action  = 'store',
                      help="Verbose mode [0=Off, 1=critical, 2=trace data, 3=all. Default: %default")
    parser.add_option('-f', dest= 'frequency', action = 'store', 
                      type=int, metavar='TIME_SEC', default=60, 
                      help='Frequency to run checks in seconds. Default: %default sec')
    parser.add_option('--log', dest= 'log', action = 'store', metavar='LOGNAME',        
                      default=logfilename, help='Logfile to be used. Default: %default')
    parser.add_option('--col', dest= 'col', action = 'store', metavar='COLUMNS_PER_ROW', type=int,       
                      default=int(confData.get('pluginPerRow')), help='# of plugins per row. Default: %default')
    parser.add_option('--opx', dest= 'opx', action = 'store_true',        
                      default=False, help='Change to OPX. Default: %default')
    parser.add_option('--path', dest= 'path', action = 'store',        
                      default=os.getcwd(), help='Default base path. Default: %default')
    parser.add_option('--cert', dest= 'cert', action = 'store',        
                      default=confData.get('cert'), help='Certification PEM File. Default: %default')

    (opts, args) = parser.parse_args()

    action = sys.argv[1]
    if action not in commands:
        parser.print_usage()
        sys.exit(1)

    if opts.opx:
        COLOR   = OPX_COLOR
        SVG     = OPX_SVG
        ADJUST  = OPX_ADJ
        ICO     = OPX_ICO
        COMPANY = "OPX"

    #compre confData with what user has specified, and persist config.
    if action in ['start', 'set', 'restart']:
        confData['HOST']            = opts.host
        confData['PORT']            = opts.port
        confData['pluginPerRow']    = opts.col
        confData['cert']            = opts.cert
        if action == 'set' and len(args) > 1 and '=' in args[1]:
            a, v = args[1].split('=')
            confData[a]=v
        setConfigData(confData)

    #instance of status class
    srvcD = SysStatusDaemon('SS_Daemon', PIDFILE, {'stdout': STDOUT, 'stderr': STDERR if opts.verbose else '/dev/null'}, opts)

    # get missing default values from plugins
    setConfigData(srvcD.getDefaults(confData))

    # Invoke the command
    if eval(action)(srvcD, opts, args) != 0:
        parser.print_usage()
        sys.exit(1)
    sys.exit(0)

