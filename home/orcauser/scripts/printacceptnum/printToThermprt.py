#!/usr/bin/python
# -*- coding: utf-8 -*-

from escpos.printer import * 
import sys
from datetime import datetime

def jpInit(printer):
    printer.charcode('JIS')
    printer._raw(b'\x1c\x43\x01')	# Kanji Code System Selection: FS 'C'

def jpText(printer, txt, dw=False, dh=False):

	txt = txt.decode('utf-8')
	printer._raw(b'\x1c\x26')         # Kanji mode ON
	n = 0x00
	if (dw):
		n += 0x04
	if (dh):
		n += 0x08
	if (n != 0x00):
		printer._raw(b'\x1c\x21' + n.to_bytes(1, byteorder='big')) # Char size ON
	printer.text(txt.encode('shift_jis', 'ignore'))
	if (n != 0x00):
		printer._raw(b'\x1c\x21\x00') # Char size OFF
	printer._raw(b'\x1c\x2e')         # Kanji mode OFF

WEEKDAY = ["8c8e", "89CE", "9085", "96D8", "8BE0", "9379", "93FA"]	# ['月', '火', '水', '木', '金', '土', '日']
PRINTER_IP = "192.168.0.17"
args = sys.argv

accept_ID = args[1]
accept_date = args[2]
accept_time = args[3]

acceptDatetime = datetime.strptime(accept_date + ' ' + accept_time, '%Y-%m-%d %H:%M:%S')
acceptDatetime_outtext = format(acceptDatetime.year, "x") + '944e' + format(acceptDatetime.month,"x") + '8c8e' + format(acceptDatetime.day, "x") + '93fa8169' + WEEKDAY[acceptDatetime.weekday()] + '816a20' + format(acceptDatetime.hour,"x") + '8e9e' + format(acceptDatetime.minute,"x") + '95aa'

Seiko = Network(PRINTER_IP)

Seiko._raw(b'\x1b\x40')
Seiko._raw(b'\x1b\x52\x08')		# International characer select

jpInit(Seiko)

#Seiko._raw(b'\x1C\x43\x01)	    # FS C （Shift JISコード体系を選択する）電源offまで有効
#Seiko._raw(b'\x1c\x26')			# Kanji code ON	

jpText(Seiko, '領収書')

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
Seiko.cut()
'''