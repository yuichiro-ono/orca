#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

#sys.path.insert(0, "/usr/local/lib/python2.7/dist-packages/python_escpos-3.0a5.dev1+g52719c0-py2.7.egg")
sys.path.insert(1, "/home/user1/.local/lib/python2.7/site-packages")

import time
import binascii
import struct

from escpos.printer import * 
from datetime import datetime

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
PRINTER_IP = "192.168.20.40"
HEROKU_URL = "http://wait-1210.herokuapp.com"
args = sys.argv

accept_ID = args[1]
accept_date = args[2]
accept_time = args[3]

acceptDatetime = datetime.strptime(accept_date + ' ' + accept_time, '%Y-%m-%d %H:%M:%S')
acceptDate_outtext = acceptDatetime.strftime('%Y年%m月%d日') 
acceptTime_outtext = acceptDatetime.strftime('%H時%M分')

Seiko = Network(PRINTER_IP)

jpInit(Seiko)
Seiko.set(align="center", bold=True, width=3, height=3, custom_size=True, invert=True)
jpText(Seiko, 'ご案内\n\n')
Seiko.set(align="left", bold=False, width=2, height=2, custom_size=True, invert=False)
jpText(Seiko, '受付日：' + acceptDate_outtext + '\n')
jpText(Seiko, '受付時間：' + acceptTime_outtext + '\n')
jpText(Seiko, '呼出番号：【')
Seiko.set(align="left", bold=True, double_width=True, double_height=True)
Seiko.text(accept_ID)
jpText(Seiko, '】\n')
#Seiko.text(accept_ID + '\n')
#Seiko.set(align="center", bold=True, double_width=True, double_height=True)
#Seiko.ln(2)
Seiko._raw(b'\x1b\x52\x00')
Seiko.set(align="center")
Seiko.qr(HEROKU_URL + "/wait/" + accept_ID, size=3, center=True)
Seiko.set(align="center", bold=False, double_width=True, double_height=True)
jpText(Seiko, '↑のQRコードを読み込むと待ち時間が表示されます\n\n')
Seiko.set(align="center", bold=False, double_width=False, double_height=False)
Seiko.text('-------------------------------------\n')
jpText(Seiko, '芦屋駅前小野内科クリニック')
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