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
VER_MINOR = 0
VER_DEV   = 1
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
<svg version="1.0" xmlns="http://www.w3.org/2000/svg" width="90pt" height="25pt" viewBox="0 0 1300.000000 399.000000" preserveAspectRatio="xMidYMid meet">
<g transform="translate(0.000000,399.000000) scale(0.100000,-0.100000)" fill="#0485cb" stroke="none">
<path d="M1810 3975 c-207 -23 -359 -60 -543 -131 -166 -64 -414 -204 -401 -226 4 -7 2 -8 -5 -4 -14 9 -84 -41 -76 -55 3 -5 0 -6 -8 -4 -7 3 -59 -36 -123 -93 -105 -94 -151 -147 -146 -165 1 -5 -2 -6 -7 -3 -11 7 -117 -126 -186 -234 -27 -41 -77 -133 -111 -205 -237 -490 -263 -1039 -74 -1550 63 -170 192 -411 213 -398 6 3 7 1 3 -6 -19 -29 327 -423 355 -405 7 4 9 3 6 -3 -9 -15 138 -127 154 -117 7 4 10 3 6 -3 -8 -13 70 -66 84 -58 5 4 8 1 7 -6 -4 -17 200 -122 338 -173 283 -105 577 -149 843 -126 246 21 463 74 670 165 136 59 283 144 275 157 -4 7 -2 8 4 4 20 -12 264 173 259 197 -1 6 5 12 13 12 8 0 14 7 12 14 -1 7 1 10 6 7 12 -7 54 38 45 49 -5 4 -3 5 3 2 14 -8 106 88 179 188 276 373 405 785 392 1245 -12 396 -116 726 -334 1052 -36 54 -69 96 -73 93 -4 -3 -14 3 -21 12 -10 12 -10 14 -1 9 24 -14 11 7 -39 65 -28 32 -56 56 -62 52 -5 -3 -7 -1 -4 4 8 13 -17 36 -28 25 -5 -4 -5 -2 -2 4 7 12 -45 67 -56 59 -4 -3 -5 -2 -2 2 6 8 -64 83 -78 83 -4 0 -5 -6 -1 -12 4 -8 3 -10 -2 -5 -5 5 -9 14 -9 20 -1 7 -7 11 -14 9 -7 -1 -10 1 -7 6 7 12 -126 111 -243 180 -263 155 -562 247 -885 272 -153 12 -176 12 -326 -5z m470 -230 c169 -26 318 -72 489 -151 51 -24 98 -41 104 -37 5 3 7 1 4 -5 -9 -13 79 -65 95 -56 6 4 8 3 5 -3 -3 -5 27 -33 67 -61 88 -62 192 -155 288 -260 39 -42 75 -76 80 -74 5 1 7 -2 3 -8 -4 -6 7 -27 24 -48 16 -21 52 -74 79 -118 134 -216 210 -425 248 -684 22 -157 15 -452 -15 -593 -45 -206 -125 -407 -229 -575 -29 -46 -49 -89 -46 -94 4 -7 2 -8 -4 -4 -13 8 -75 -78 -64 -89 4 -3 2 -5 -4 -3 -16 5 -117 -109 -108 -123 4 -7 3 -9 -3 -6 -5 3 -27 -10 -49 -30 -65 -59 -147 -128 -182 -152 -18 -12 -29 -27 -26 -33 4 -6 2 -8 -4 -5 -12 8 -158 -80 -155 -92 1 -5 -3 -8 -10 -7 -22 2 -206 -87 -200 -97 3 -6 1 -7 -5 -3 -7 4 -60 -9 -119 -28 -205 -66 -472 -96 -683 -76 -224 20 -455 82 -621 166 -39 19 -75 32 -81 28 -7 -4 -8 -3 -4 4 4 7 3 12 -2 12 -5 0 -37 18 -71 40 -34 22 -67 37 -73 34 -6 -4 -8 -3 -5 3 7 12 -70 68 -93 68 -8 0 -15 5 -15 12 0 6 -36 42 -80 81 -73 63 -177 178 -249 274 -16 21 -33 35 -39 31 -5 -3 -7 -1 -3 5 3 6 -18 51 -48 100 -359 589 -331 1350 69 1922 30 42 51 80 47 84 -4 4 -2 6 4 4 14 -4 114 113 107 126 -3 5 -1 6 4 3 12 -7 36 16 28 26 -3 4 -2 5 1 3 4 -3 47 30 98 72 50 43 119 97 153 121 35 24 60 47 58 51 -3 4 1 7 8 6 6 0 73 30 147 67 342 172 702 229 1080 172z"/>
<path d="M1565 2344 c-137 -89 -254 -163 -260 -163 -5 0 -21 24 -33 53 -29 67 -89 139 -109 132 -8 -3 -11 -2 -8 4 9 15 -75 58 -145 74 -69 17 -470 23 -470 9 0 -21 0 -800 0 -810 0 -16 328 -18 425 -4 169 25 261 99 331 269 9 22 14 19 172 -88 89 -61 167 -108 173 -105 5 4 8 2 7 -4 -4 -13 171 -133 183 -125 6 3 5 13 -3 22 -11 15 -11 15 4 4 13 -11 22 -10 50 7 18 12 33 26 33 33 1 7 7 12 14 10 19 -4 162 88 154 101 -3 6 -1 7 5 3 15 -9 174 93 165 107 -3 6 -1 7 5 3 7 -4 22 0 34 8 12 9 26 16 30 16 5 0 8 -61 8 -135 l0 -135 280 0 280 0 0 130 0 130 -135 0 -135 0 0 285 0 285 -145 0 -145 0 0 -145 0 -144 -30 -16 c-17 -9 -28 -20 -25 -25 4 -6 -1 -7 -11 -3 -13 5 -15 3 -9 -7 5 -8 4 -11 -2 -7 -13 8 -169 -91 -165 -104 1 -6 -2 -8 -7 -4 -6 3 -42 -15 -81 -40 -38 -25 -75 -45 -81 -45 -13 0 -69 32 -69 40 0 3 27 22 60 44 33 21 57 43 53 49 -3 6 -1 7 5 3 6 -3 70 33 143 81 l132 87 -23 18 c-13 11 -30 16 -37 14 -8 -3 -11 -1 -8 4 8 13 -73 63 -87 54 -7 -4 -8 -3 -4 4 16 26 -24 9 -117 -51 -54 -35 -94 -67 -90 -72 4 -4 3 -5 -4 -1 -6 3 -54 -21 -106 -54 l-95 -61 -36 22 c-20 11 -36 22 -36 24 0 2 22 17 50 35 28 18 47 37 43 43 -3 6 -1 7 5 3 6 -4 76 35 156 86 144 92 145 93 123 110 -12 10 -28 16 -35 13 -7 -3 -10 0 -7 5 8 13 -73 63 -87 54 -7 -4 -8 -3 -4 4 3 6 -1 15 -11 20 -14 7 -72 -26 -268 -154z m-586 -161 c65 -49 88 -162 45 -220 -39 -53 -81 -73 -150 -73 l-64 0 0 153 c0 85 3 157 8 161 14 15 133 -1 161 -21z"/>
<path d="M2980 2045 l0 -415 275 0 275 0 0 130 0 130 -130 0 -130 0 0 285 0 285 -145 0 -145 0 0 -415z"/>
<path d="M5325 3964 c-234 -23 -389 -57 -546 -119 -114 -45 -255 -125 -239 -135 8 -5 7 -9 -5 -13 -9 -4 -13 -3 -10 3 19 31 -24 0 -104 -76 -58 -55 -90 -92 -87 -101 3 -8 2 -12 -3 -8 -13 8 -54 -52 -45 -66 4 -7 3 -9 -4 -5 -13 8 -61 -74 -100 -174 -99 -251 -90 -522 25 -756 40 -82 105 -170 122 -166 7 1 9 -2 6 -9 -10 -14 76 -101 93 -94 7 2 11 1 7 -4 -9 -15 123 -107 231 -161 147 -73 378 -146 812 -255 210 -53 433 -112 495 -132 368 -116 540 -285 554 -548 10 -165 -42 -300 -161 -419 -67 -68 -128 -122 -133 -119 -1 1 -40 -16 -86 -37 -160 -75 -343 -110 -575 -110 -204 0 -354 25 -523 86 -38 14 -75 22 -82 18 -6 -4 -9 -4 -5 1 4 4 -33 31 -82 59 -243 137 -371 323 -426 620 -10 53 -23 96 -29 96 -5 0 -107 -9 -225 -20 -118 -11 -218 -20 -222 -20 -19 0 0 -179 32 -304 10 -39 32 -107 49 -151 35 -93 124 -251 139 -248 5 1 9 -5 8 -15 0 -9 5 -16 12 -14 8 1 11 -2 8 -7 -13 -20 144 -188 163 -176 7 4 10 1 9 -7 -2 -7 3 -12 10 -10 8 1 11 -2 7 -7 -8 -14 133 -111 242 -165 247 -124 533 -180 918 -180 300 -1 465 28 700 120 103 41 271 135 268 151 -1 6 4 10 11 9 20 -2 126 87 121 101 -2 7 2 10 9 7 16 -6 99 92 90 108 -4 6 -3 8 4 4 6 -4 27 17 50 51 118 174 182 381 182 586 0 168 -33 314 -102 450 -38 76 -96 157 -111 154 -7 -1 -11 4 -9 12 2 7 -5 22 -14 32 -14 16 -20 17 -33 6 -14 -10 -14 -10 -4 4 11 13 10 19 -5 33 -10 9 -22 13 -27 9 -4 -5 -5 -3 -2 3 7 13 -58 66 -163 134 -168 108 -376 182 -800 286 -146 36 -329 81 -408 100 -233 57 -480 146 -538 195 -7 6 -19 7 -25 3 -7 -4 -10 -3 -6 2 3 5 -16 31 -43 58 -146 147 -167 393 -50 576 17 26 60 76 97 111 37 35 67 67 66 70 -1 4 5 6 15 5 9 0 16 4 15 10 -1 7 3 11 10 10 7 0 50 14 97 32 117 47 249 71 425 78 258 11 458 -22 624 -102 76 -37 110 -61 170 -122 42 -41 79 -75 82 -74 3 0 6 -5 6 -11 0 -7 12 -32 28 -57 45 -71 90 -206 109 -330 l6 -35 223 17 c122 9 230 17 239 17 15 1 16 9 11 54 -11 108 -42 245 -72 322 -40 103 -116 241 -131 237 -6 -1 -9 2 -6 7 8 13 -78 117 -93 113 -7 -1 -10 2 -7 7 6 9 -10 26 -29 33 -5 1 -9 6 -8 10 4 12 -86 80 -97 73 -6 -4 -9 -1 -8 6 4 20 -142 103 -260 150 -204 80 -397 116 -657 123 -88 2 -178 2 -200 0z"/>
<path d="M8960 3863 c-18 -32 -50 -82 -72 -111 -21 -29 -36 -57 -32 -64 4 -6 3 -8 -3 -5 -14 9 -47 -29 -37 -44 4 -7 3 -10 -4 -5 -12 7 -129 -120 -124 -136 1 -5 -1 -7 -6 -4 -13 8 -143 -114 -136 -126 4 -7 2 -8 -4 -4 -13 8 -104 -63 -96 -75 2 -4 -1 -11 -7 -15 -8 -4 -9 -3 -5 4 4 7 5 12 2 12 -11 0 -101 -73 -99 -80 1 -4 -3 -7 -10 -7 -7 0 -43 -20 -82 -45 -38 -25 -85 -53 -103 -62 -18 -9 -30 -21 -27 -25 2 -5 -1 -8 -8 -7 -6 0 -60 -24 -119 -54 l-108 -55 0 -224 c0 -174 3 -222 13 -218 167 66 514 248 509 267 -1 6 2 9 8 5 14 -9 171 95 163 108 -3 6 -1 7 5 3 19 -11 197 128 186 145 -3 5 1 6 9 3 8 -3 20 2 27 11 7 8 16 15 21 15 5 0 9 -644 9 -1495 l0 -1495 230 0 230 0 0 1920 0 1920 -149 0 -149 0 -32 -57z"/>
<path d="M11625 3914 c-16 -2 -63 -9 -103 -15 -121 -18 -339 -100 -325 -122 4 -6 1 -7 -6 -3 -15 10 -94 -41 -86 -54 3 -5 0 -7 -8 -4 -21 8 -202 -169 -192 -186 5 -8 4 -11 -3 -6 -16 10 -106 -122 -168 -249 -66 -137 -125 -311 -158 -475 -98 -481 -93 -1245 10 -1710 50 -223 144 -463 234 -596 53 -79 101 -135 110 -129 5 3 12 0 16 -6 4 -8 3 -9 -4 -5 -7 4 -12 3 -12 -3 0 -15 150 -141 214 -180 254 -154 608 -200 926 -120 99 25 262 97 253 112 -3 6 -1 7 6 3 14 -9 74 32 66 45 -4 5 0 6 8 3 21 -8 202 169 192 186 -5 8 -4 11 2 7 14 -9 37 19 27 34 -4 7 -3 9 4 5 16 -10 86 99 147 228 156 329 219 711 218 1311 -1 517 -41 802 -155 1115 -40 111 -117 266 -176 355 -47 70 -197 235 -214 235 -5 0 -6 -5 -2 -12 4 -7 3 -8 -5 -4 -6 4 -9 12 -6 17 8 12 -145 111 -162 104 -8 -2 -12 -1 -8 4 7 13 -141 69 -244 92 -83 19 -327 33 -396 23z m240 -389 c98 -18 202 -69 286 -139 37 -30 70 -52 74 -48 4 4 5 2 3 -4 -1 -6 22 -45 53 -87 113 -151 183 -390 219 -747 18 -174 24 -718 11 -917 -27 -390 -92 -685 -182 -828 -16 -25 -27 -51 -23 -56 3 -5 1 -8 -3 -7 -11 4 -114 -117 -107 -126 2 -3 1 -4 -2 -1 -4 2 -33 -16 -65 -41 -194 -149 -436 -174 -653 -68 -124 61 -263 207 -331 348 -69 145 -119 368 -147 651 -17 173 -17 850 0 1005 40 367 99 592 197 755 19 31 32 62 28 68 -3 5 -1 7 4 4 15 -9 47 29 37 45 -4 7 -3 10 1 5 11 -9 46 23 39 35 -3 4 -2 7 3 6 14 -5 103 64 96 75 -3 6 -1 7 5 3 6 -3 37 7 69 23 32 16 83 34 113 40 30 6 64 13 75 15 45 9 128 5 200 -9z"/>
</g></svg>'''

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
        finalDic['statusValue'] = self.context.overallStatus
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

