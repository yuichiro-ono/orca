#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, "/usr/local/lib/python2.7/dist-packages/python_escpos-3.0a5.dev1+g52719c0-py2.7.egg")

try:
    import Image
except ImportError:
    from PIL import Image

import time
import binascii
import struct

from escpos.printer import * 
from escpos.escpos import *
from datetime import datetime

# Image format  
S_RASTER_N      = '\x1d\x76\x30\x00' # Set raster image normal size
S_RASTER_2W     = '\x1d\x76\x30\x01' # Set raster image double width
S_RASTER_2H     = '\x1d\x76\x30\x02' # Set raster image double height
S_RASTER_Q = '\x1d\x76\x30\x03' # Set raster image quadruple

def jpInit(printer):
#	printer.charcode('JIS')
	printer._raw(b'\x1b\x40')
	printer._raw(b'\x1b\x52\x08')		# International characer select
	printer._raw(b'\x1c\x43\x01')	# Kanji Code System Selection: FS 'C' 1 (Shift_JIS)

def text(printer, txt):
	""" Print alpha-numeric text """
	if txt:
		printer._raw(txt)

def jpText(printer, txt, dw=False, dh=False):

	txt = txt.decode('utf-8')
	printer._raw(b'\x1c\x26')         # Kanji mode ON
	n = 0x00
	if (dw):
		n += 0x04
	if (dh):
		n += 0x08
	if (n != 0x00):
		printer._raw(b'\x1c\x21' + struct.pack(">B", n)) # Char size ON
	text(printer, txt.encode('shift_jis', 'ignore'))
	if (n != 0x00):
		printer._raw(b'\x1c\x21\x00') # Char size OFF
	printer._raw(b'\x1c\x2e')         # Kanji mode OFF


WEEKDAY = ['月', '火', '水', '木', '金', '土', '日']
PRINTER_IP = "192.168.0.17"
args = sys.argv

accept_ID = args[1]
accept_date = args[2]
accept_time = args[3]

acceptDatetime = datetime.strptime(accept_date + ' ' + accept_time, '%Y-%m-%d %H:%M:%S')
#acceptDatetime_outtext = format(acceptDatetime.year, "x") + '944e' + format(acceptDatetime.month,"x") + '8c8e' + format(acceptDatetime.day, "x") + '93fa8169' + WEEKDAY[acceptDatetime.weekday()] + '816a20' + format(acceptDatetime.hour,"x") + '8e9e' + format(acceptDatetime.minute,"x") + '95aa'
acceptDatetime_outtext = acceptDatetime.strftime('%Y年%m月%d日') + '(' + WEEKDAY[acceptDatetime.weekday()] + ') ' + acceptDatetime.strftime('%H時%M分')


Seiko = Network(PRINTER_IP)

jpInit(Seiko)
jpText(Seiko, '受付日時：' + acceptDatetime_outtext + '\n')
jpText(Seiko, '受付番号：' + accept_ID + '\n\n')
#Seiko.text(accept_ID + '\n')
#Seiko.set(align="center", bold=True, double_width=True, double_height=True)
#Seiko.ln(2)
#Seiko._raw(b'\x1b\x52\x00')
Seiko.qr("http://ashiyaekimaeclinic.aaa.com/wait/" + accept_ID, size=4, center=True)
jpText(Seiko, '↑のQRコードを読み込むと，待ち時間が表示されます')
Seiko.cut()


#Seiko.text("8ef3957493fa8e9e8146H" + acceptDatetime_outtext)
'''
Seiko.set("center")
Seiko.text("8ef3957494d48d86H")
Seiko.set("center", text_type="bold", width=8, height=8)
Seiko.text(accept_ID)
#Seiko.ln(2)
Seiko.qr("http://ashiyaekimaeclinic.aaa.com/wait/" + accept_ID)
#Seiko.ln(1)
Seiko.text("81aa8fe382cc51528352815b836882f093c782dd8d9e82de82c6908492e891d282bf8e9e8ad482aa955c8ea682b382ea82dc82b781aaH")

'''