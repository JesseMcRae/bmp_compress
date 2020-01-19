# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import struct
from bmpRead import ReadBMPFile
from SVD import svdCompression
from HFM import *

def decomposite(inputbmp):
	# eta = input("您希望的图片最小压缩率：")
	k = round(inputbmp.biHeight * inputbmp.biWidth / 4 / (1 + inputbmp.biHeight + inputbmp.biWidth))
	for eta in range(100, 0, -10):
		ur, sigmar, vr, kr = svdCompression(inputbmp.R, eta/100)
		ug, sigmag, vg, kg = svdCompression(inputbmp.G, eta/100)
		ub, sigmab, vb, kb = svdCompression(inputbmp.B, eta/100)
		if(max(kr, kb, kg) < k):
			print('eta:',eta)
			print(k*eta,kr,kb,kg)
			break
	buff = []
	buff_extend(inputbmp.bfType, buff)
	buff_extend(inputbmp.bfSize.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.bfOffBits.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biSize.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biWidth.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biHeight.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biPlanes.to_bytes(2, 'little'), buff)
	buff_extend(inputbmp.biBitCount.to_bytes(2, 'little'), buff)
	buff_extend(inputbmp.biCompression.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biSizeImage.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biXPelsPerMeter.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biYPelsPerMeter.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biClrUsed.to_bytes(4, 'little'), buff)
	buff_extend(inputbmp.biClrImportant.to_bytes(4, 'little'), buff)

	buff_extend(kr.to_bytes(4, 'big'), buff)
	for row in ur:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	buff_extend(struct.pack('>%sf' % len(sigmar), *sigmar), buff)
	for row in vr:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	buff_extend(kg.to_bytes(4, 'big'), buff)
	for row in ug:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	buff_extend(struct.pack('>%sf' % len(sigmag), *sigmag), buff)
	for row in vg:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	buff_extend(kb.to_bytes(4, 'big'), buff)
	for row in ub:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	buff_extend(struct.pack('>%sf' % len(sigmab), *sigmab), buff)
	for row in vb:
		buff_extend(struct.pack('>%sf' % len(row), *row), buff)
	return buff

def buff_extend(bistr, buff):
	for x in bistr:
		buff.append(x.to_bytes(1,byteorder = 'big'))

def encodestr(buff, inputfile):
	#数据初始化
	node_dict = {}	#建立原始数据与编码节点的映射，便于稍后输出数据的编码
	count_dict = {}
	nodes = []	#结点列表，用于构建哈夫曼树
	print("Start encode...")
	print("size of string:",len(buff),"B")
	#计算字符频率,并将单个字符构建成单一节点
	for x in buff:
		if count_dict.get(x) is None:
			count_dict[x] = 0
		count_dict[x] += 1
	print("Read finish")
	# print(count_dict)	#输出权值字典,可注释掉
	for x in count_dict.keys():
		node_dict[x] = node(value = count_dict[x])
		nodes.append(node_dict[x])
	build_tree(nodes)	#哈夫曼树构建
	enco_dict = dict_code(node_dict)	#构建编码表
	print("Encode finish")

	#对所有根节点进行排序
	head = sorted(count_dict.items(),key = lambda x:x[1],reverse = True)
	print("head:",head[0][1])	#动态调整编码表的字节长度，优化文件头大小
	if head[0][1] < 256:
		bit_width = 1
	elif head[0][1] < 65536:
		bit_width = 2
	elif head[0][1] < 16777216:
		bit_width = 3
	else:
		bit_width = 4
	print("bit_width:",bit_width)
	o = open(inputfile.split('.')[0]+".hfm", 'wb')
	#写出原文件名
	o.write((inputfile.split('/')[-1] + '\n').encode(encoding='utf-8'))
	o.write(len(enco_dict).to_bytes(2,byteorder = 'big'))	#写出结点数量
	o.write(bit_width.to_bytes(1,byteorder = 'big'))	#写出编码表字节宽度
	for x in enco_dict.keys():	#编码文件头
		o.write(x)
		o.write(count_dict[x].to_bytes(bit_width,byteorder = 'big'))

	raw = 0b1	#数据写入相关
	last = 0	#记录压缩进度
	print("Write head finish")
	for i in range(len(buff)):	#开始压缩数据
		for x in enco_dict[buff[i]]:
			raw = raw << 1
			if x == 49:
				raw = raw | 1
			if raw.bit_length() == 9:
				raw = raw & (~(1 << 8))
				o.write(raw.to_bytes(1,byteorder = 'big'))
				# o.flush()
				raw = 0b1
		tem = round(i / len(buff) * 100)
		if tem > last:
			print("\rrate of encode:",tem,"%", end="")	#输出压缩进度
			last = tem

	if raw.bit_length() > 1:	#处理文件尾部不足一个字节的数据
		raw = raw << (8 - (raw.bit_length() - 1))
		raw = raw & (~(1 << raw.bit_length() - 1))
		o.write(raw.to_bytes(1, byteorder = 'big'))
	o.close()
	print("\nFile encode success.")

def bmp_compress():
	while True:
		# inputpath = input("请输入bmp文件：")
		inputpath = "f3.bmp"
		name = inputpath.split('.')
		if name[-1] == "bmp":
			inputbmp = ReadBMPFile(inputpath)
			buff = decomposite(inputbmp)
			encodestr(buff, inputpath)
			break
		else:
			print(inputpath, "is not a BMP file!\n")

def decodestring(inputfile):

	#数据初始化
	node_dict = {}	#建立原始数据与编码节点的映射，便于稍后输出数据的编码
	count_dict = {}
	nodes = []	#结点列表，用于构建哈夫曼树

	print("Start decode...")
	f = open(inputfile,'rb')
	f.seek(0,2)
	eof = f.tell()
	f.seek(0)

	outputfile = inputfile.replace(inputfile.split('/')[-1], \
		f.readline().decode(encoding='utf-8').replace('\n',''))
	
	count = int.from_bytes(f.read(2), byteorder = 'big')	#取出结点数量
	bit_width = int.from_bytes(f.read(1), byteorder = 'big')	#取出编码表字宽
	for i in range(count):	#解析文件头
		key = f.read(1)
		count_dict[key] = int.from_bytes(f.read(bit_width), byteorder = 'big')
	for x in count_dict.keys():
		node_dict[x] = node(value = count_dict[x])
		nodes.append(node_dict[x])
	build_tree(nodes)	#重建哈夫曼树
	enco_dict = dict_code(node_dict)	#建立编码表
	inverse_dict = {val: key for key, val in enco_dict.items()}	#反向字典构建
	i = f.tell()
	print("huffmam file:",eof,"B")
	last = 0
	data = b''
	buff = bytearray()

	while i < eof:	#开始解压数据
		raw = int.from_bytes(f.read(1), byteorder = 'big')
		i += 1
		for j in range(8,0,-1):
			if (raw >> (j - 1)) & 1 == 1:
				data += b'1'
				raw = raw & (~(1 << (j - 1)))
			else:
				data += b'0'
				raw = raw & (~(1 << (j - 1)))
			if inverse_dict.get(data) is not None:
				buff.extend(inverse_dict[data])
				# print("decode",data,":",inverse_dict[data])
				data = b''
		tem = round(i / eof * 100)
		if tem > last:							
			print("\rrate of decode:",tem,"%", end = '')	#输出解压进度
			last = tem
	f.close()
	print("\nFile decode success.")

	imgdecompress(buff, outputfile)

def buff_pop(num, buff):
	s = buff[:num]
	del buff[:num]
	return s

def imgdecompress(buff, outputfile):

	o = open(outputfile,'wb')
	for i in range(6):
		o.write(buff.pop(0).to_bytes(1,byteorder = 'little'))
	o.write(b'\x00\x00\x00\x00')
	for i in range(8):
		o.write(buff.pop(0).to_bytes(1,byteorder = 'little'))
	Width = int.from_bytes(buff[:4], byteorder='little')
	Height = int.from_bytes(buff[4:8], byteorder='little')
	for i in range(36):
		o.write(buff.pop(0).to_bytes(1,byteorder = 'little'))

	kr = int.from_bytes(buff_pop(4,buff),byteorder = 'big')
	ur = np.zeros((Height,kr))
	for i in range(Height):
		for j in range(kr):
			ur[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	sigmar = np.zeros(kr)
	for i in range(kr):
		sigmar[i] = struct.unpack('>f', buff_pop(4, buff))[0]
	vr = np.zeros((kr,Width))
	for i in range(kr):
		for j in range(Width):
			vr[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	R = np.rint(ur.dot(np.diag(sigmar)).dot(vr).clip(0,255)).astype('uint8')

	kg = int.from_bytes(buff_pop(4,buff),byteorder = 'big')
	ug = np.zeros((Height,kg))
	for i in range(Height):
		for j in range(kg):
			ug[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	sigmag = np.zeros(kg)
	for i in range(kg):
		sigmag[i] = struct.unpack('>f', buff_pop(4, buff))[0]
	vg = np.zeros((kg,Width))
	for i in range(kg):
		for j in range(Width):
			vg[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	G = np.rint(ug.dot(np.diag(sigmag)).dot(vg).clip(0,255)).astype('uint8')

	kb = int.from_bytes(buff_pop(4,buff),byteorder = 'big')
	ub = np.zeros((Height,kb))
	for i in range(Height):
		for j in range(kb):
			ub[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	sigmab = np.zeros(kb)
	for i in range(kb):
		sigmab[i] = struct.unpack('>f', buff_pop(4, buff))[0]
	vb = np.zeros((kb,Width))
	for i in range(kb):
		for j in range(Width):
			vb[i, j] = struct.unpack('>f', buff_pop(4, buff))[0]
	B = np.rint(ub.dot(np.diag(sigmab)).dot(vb).clip(0,255)).astype('uint8')

	I = np.flipud(np.stack((B, G, R), axis = 2))
	for row in I:
		count = 0
		for column in row:
			o.write(struct.pack('<%sB' % len(column), *column))
			count += 3
		while count % 4 != 0:
			o.write(b'\x00')
			count += 1
	o.close()

def decompress():
	# inputpath = input("请要解压的文件：")
	inputpath = "c7.hfm"
	decodestring(inputpath)

if __name__ == "__main__":
	# if input("1：压缩图片\t2：解压图片\n请输入你要执行的操作：") == '1':
		bmp_compress()
	# else:
		# decompress()
