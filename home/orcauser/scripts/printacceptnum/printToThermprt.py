import * from escpos
import sys
import datetime

WEEKDAY = ['月', '火', '水', '木', '金', '土', '日']
args = sys.argv

accept_ID = args[1]
accept_date = args[2]
accept_time = args[3]

acceptDatetime = datetime.strptime(accept_date + ' ' + accept_time, '%Y-%m-%d %H:%M:%S')
acceptDatetime_outtext = hex(acceptDatetime.year) + '944e' + hex(acceptDatetime.month) + '8c8e' + hex(acceptDatetime.day) + '93fa8169' + 
	WEEKDAY[acceptDatetime.weekday] + '816a20' + hex(acceptDatetime.hour) + '8e9e' + hex(acceptDatetime.minute) + '95aa'

Seiko = printer.Network("192.168.0.099")
Seiko._raw("0x1B 0x52 0x08")
Seiko._raw("0x1B 0x74 0x06") 	# ESC t (ひらがな・簡易漢字) 文字コードテーブルに変更
Seiko._raw("0x1C 0x43 0x01")	# FS C （Shift JISコード体系を選択する）電源offまで有効
Seiko.text("0x8ef3957493fa8e9e8146" + acceptDatetime_outtext)
Seiko.set("center")
Seiko.textln("0x8ef3957494d48d86")
Seiko.set("center", bold=TRUE, width=8, height=8)
Seiko.textln(accept_ID)
Seiko.ln(2)
Seiko.qr("http://ashiyaekimaeclinic.aaa.com/wait/" + accept_ID)
Seiko.ln(1)
Seiko.text("0x81aa8fe382cc51528352815b836882f093c782dd8d9e82de82c6908492e891d282bf8e9e8ad482aa955c8ea682b382ea82dc82b781aa")
Seiko.cut()