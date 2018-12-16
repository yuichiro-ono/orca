#!/usr/bin/python
# -*- coding: utf-8 -*-

from escpos.printer import * 
import sys
from datetime import datetime

WEEKDAY = ["8c8e", "89CE", "9085", "96D8", "8BE0", "9379", "93FA"]	# ['月', '火', '水', '木', '金', '土', '日']
PRINTER_IP = "192.168.0.17"
args = sys.argv

accept_ID = args[1]
accept_date = args[2]
accept_time = args[3]

acceptDatetime = datetime.strptime(accept_date + ' ' + accept_time, '%Y-%m-%d %H:%M:%S')
acceptDatetime_outtext = format(acceptDatetime.year, "x") + '944e' + format(acceptDatetime.month,"x") + '8c8e' + format(acceptDatetime.day, "x") + '93fa8169' + WEEKDAY[acceptDatetime.weekday()] + '816a20' + format(acceptDatetime.hour,"x") + '8e9e' + format(acceptDatetime.minute,"x") + '95aa'
print acceptDatetime_outtext

Seiko = Network(PRINTER_IP)

Seiko._raw("1BH 52H 8")		# International characer select
Seiko._raw("1CH 43H 1")	    # FS C （Shift JISコード体系を選択する）電源offまで有効
Seiko.text("8ef3957493fa8e9e8146H" + acceptDatetime_outtext)
Seiko.set("center")
Seiko.text("8ef3957494d48d86H")
Seiko.set("center", text_type="bold", width=8, height=8)
Seiko.text(accept_ID)
Seiko.ln(2)
Seiko.qr("http://ashiyaekimaeclinic.aaa.com/wait/" + accept_ID)
Seiko.ln(1)
Seiko.text("81aa8fe382cc51528352815b836882f093c782dd8d9e82de82c6908492e891d282bf8e9e8ad482aa955c8ea682b382ea82dc82b781aaH")
Seiko.cut()