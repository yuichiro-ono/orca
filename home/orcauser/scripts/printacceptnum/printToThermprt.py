#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import Image
except ImportError:
    from PIL import Image

import qrcode
import time
import binascii
import sys

from escpos.printer import * 
from datetime import datetime

def jpInit(printer):
	printer.charcode('JIS')
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
		printer._raw(b'\x1c\x21' + n.to_bytes(1, byteorder='big')) # Char size ON
	text(printer, txt.encode('shift_jis', 'ignore'))
	if (n != 0x00):
		printer._raw(b'\x1c\x21\x00') # Char size OFF
	printer._raw(b'\x1c\x2e')         # Kanji mode OFF

def qr(printer, text):
	""" Print QR Code for the provided string """
	qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
	qr_code.add_data(text)
	qr_code.make(fit=True)
	qr_img = qr_code.make_image()
	im = qr_img._img.convert("RGB")

    # Convert the RGB image in printable image
	_convert_image(printer, im)

def _print_image(printer, line, size):
	""" Print formatted image """
	i = 0
	cont = 0
	buffer = ""

	printer._raw(S_RASTER_N)
	buffer = "%02X%02X%02X%02X" % (((size[0]/size[1])/8), 0, size[1], 0)
	printer._raw(binascii.unhexlify(buffer))
	buffer = ""

	while i < len(line):
		hex_string = int(line[i:i+8],2)
		buffer += "%02X" % hex_string
		i += 8
		cont += 1
		if cont % 4 == 0:
			printer._raw(binascii.unhexlify(buffer))
			buffer = ""
	cont = 0

def _check_image_size(size):
	""" Check and fix the size of the image to 32 bits """
	if size % 32 == 0:
		return (0, 0)
	else:
		image_border = 32 - (size % 32)
		if (image_border % 2) == 0:
			return (image_border / 2, image_border / 2)
		else:
	return (image_border / 2, (image_border / 2) + 1)

def _convert_image(printer, im):
	""" Parse image and prepare it to a printable format """
	pixels   = []
	pix_line = ""
	im_left  = ""
	im_right = ""
	switch   = 0
	img_size = [ 0, 0 ]


	if im.size[0] > 512:
		print  ("WARNING: Image is wider than 512 and could be truncated at print time ")
	if im.size[1] > 255:
		raise ImageSizeError()

	im_border = _check_image_size(im.size[0])
	for i in range(int(im_border[0])):
		im_left += "0"
	for i in range(int(im_border[1])):
		im_right += "0"

	for y in range(im.size[1]):
		img_size[1] += 1
		pix_line += im_left
		img_size[0] += im_border[0]
		for x in range(im.size[0]):
			img_size[0] += 1
			RGB = im.getpixel((x, y))
			im_color = (RGB[0] + RGB[1] + RGB[2])
			im_pattern = "1X0"
			pattern_len = len(im_pattern)
			switch = (switch - 1 ) * (-1)
			for x in range(pattern_len):
				if im_color <= (255 * 3 / pattern_len * (x+1)):
					if im_pattern[x] == "X":
						pix_line += "%d" % switch
					else:
						pix_line += im_pattern[x]
					break
				elif im_color > (255 * 3 / pattern_len * pattern_len) and im_color <= (255 * 3):
					pix_line += im_pattern[-1]
					break
		pix_line += im_right
		img_size[0] += im_border[1]

	_print_image(printer, pix_line, img_size)

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
Seiko.set("center")
jpText(Seiko, '受付番号\n\n')
Seiko.set("center", text_type="bold", width=8, height=8)
Seiko.text(accept_ID + '\n')
Seiko.set("center", width=1, height=1)
#Seiko.ln(2)
qr(Seiko, "http://ashiyaekimaeclinic.aaa.com/wait/" + accept_ID)
jpText(Seiko, 'おしまい')
Seiko._raw(b'\x1b\x64\x05')
Seiko._raw(b'\x1B \x69')

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