# -*- coding: utf-8 -*-
import sys
import time
sys.setrecursionlimit(10000)	#压缩大文件实时会出现超出递归深度，故修改限制
#定义哈夫曼树的节点类
class node:

	def __init__(self,value = None,left = None,right = None,father = None):
		self.value = value
		self.left = left
		self.right = right
		self.father = father

	def build_father(self,left,right):
		self.value = left.value + right.value
		self.left = left
		self.right = right
		left.father = right.father = self

	def encode(self):
		if self.father is None:
			return b''
		elif self is self.father.left:
			return self.father.encode() + b'0'	#左节点编号'0'
		else:
			return self.father.encode() + b'1'	#右节点编号'1'

#哈夫曼树构建
def build_tree(sortl):

	if len(sortl) > 1:
		sortl.sort(key = lambda x:x.value,reverse = False)
		n = node()
		n.build_father(sortl.pop(0),sortl.pop(0))
		sortl.append(n)
		build_tree(sortl)

def dict_code(node_dict):

	enco_dict = {}
	for x in node_dict.keys():
		enco_dict[x] = node_dict[x].encode()
		# print(x,":",enco_dict[x])	#输出编码表（用于调试）
	return enco_dict

def encodefile(inputfile):

	#数据初始化
	node_dict = {}	#建立原始数据与编码节点的映射，便于稍后输出数据的编码
	count_dict = {}
	nodes = []	#结点列表，用于构建哈夫曼树
	
	print("Start encode...")
	f = open(inputfile,'rb')
	bytes_width = 1	#每次读取的字节宽度

	f.seek(0,2)
	count = int(f.tell() / bytes_width)
	print("size of file:",count,"B")
	buff = [b''] * count
	f.seek(0)

	#计算字符频率,并将单个字符构建成单一节点
	for i in range(count):
		buff[i] = f.read(bytes_width)
		if count_dict.get(buff[i]) is None:
			count_dict[buff[i]] = 0
		count_dict[buff[i]] += 1
	print("Read finish")
	# print(count_dict)	#输出权值字典,可注释掉
	for x in count_dict.keys():
		node_dict[x] = node(value = count_dict[x])
		nodes.append(node_dict[x])
	
	f.close()
	build_tree(nodes)	#哈夫曼树构建
	enco_dict = dict_code(node_dict)	#构建编码表
	print("Encode finish")

	head = sorted(count_dict.items(),key = lambda x:x[1],reverse = True)	#对所有根节点进行排序
	bit_width = 1
	print("head:",head[0][1])	#动态调整编码表的字节长度，优化文件头大小
	if head[0][1] > 255:
		bit_width = 2
		if head[0][1] > 65535:
			bit_width = 3
			if head[0][1] > 16777215:
				bit_width = 4
	print("bit_width:",bit_width)
	name = inputfile.split('.')
	o = open(name[0]+".hm", 'wb')
	name = inputfile.split('/')
	o.write((name[len(name)-1] + '\n').encode(encoding='utf-8'))	#写出原文件名
	o.write(len(enco_dict).to_bytes(2,byteorder = 'big'))	#写出结点数量
	o.write(bit_width.to_bytes(1,byteorder = 'big'))	#写出编码表字节宽度
	for x in enco_dict.keys():	#编码文件头
		o.write(x)
		o.write(count_dict[x].to_bytes(bit_width,byteorder = 'big'))

	raw = 0b1	#数据写入相关
	last = 0	#记录压缩进度
	print("Write head finish")
	for i in range(count):	#开始压缩数据
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

def decodefile(inputfile):

	#数据初始化
	node_dict = {}	#建立原始数据与编码节点的映射，便于稍后输出数据的编码
	count_dict = {}
	nodes = []	#结点列表，用于构建哈夫曼树

	print("Start decode...")
	f = open(inputfile,'rb')
	f.seek(0,2)
	eof = f.tell()
	f.seek(0)
	name = inputfile.split('/')
	outputfile = inputfile.replace(name[len(name)-1], f.readline().decode(encoding='utf-8'))
	o = open(outputfile.replace('\n',''),'wb')
	count = int.from_bytes(f.read(2), byteorder = 'big')			#取出结点数量
	bit_width = int.from_bytes(f.read(1), byteorder = 'big')		#取出编码表字宽
	for i in range(count):	#解析文件头
		key = f.read(1)
		count_dict[key] = int.from_bytes(f.read(bit_width), byteorder = 'big')
	for x in count_dict.keys():
		node_dict[x] = node(value = count_dict[x])
		nodes.append(node_dict[x])
	build_tree(nodes)	#重建哈夫曼树
	enco_dict = dict_code(node_dict)	#建立编码表
	inverse_dict = {val: key for key, val in enco_dict.items()}	#反向字典构建
	last = 0
	i = f.tell()
	data = b''
	print("huffmam file:",eof,"B")
	while i < eof:	#开始解压数据
		raw = int.from_bytes(f.read(1), byteorder = 'big')
		# print("raw:",raw)
		i += 1
		for j in range(8,0,-1):
			if (raw >> (j - 1)) & 1 == 1:
				data += b'1'
				raw = raw & (~(1 << (j - 1)))
			else:
				data += b'0'
				raw = raw & (~(1 << (j - 1)))
			if inverse_dict.get(data) is not None:
				o.write(inverse_dict[data])
				# o.flush()
				# print("decode",data,":",inverse_dict[data])
				data = b''
		tem = round(i / eof * 100)
		if tem > last:							
			print("\rrate of decode:",tem,"%", end = '')	#输出解压进度
			last = tem

	f.close()
	o.close()
	print("\nFile decode success.")

if __name__ == '__main__':

	time_start=time.time()
	encodefile("f3.bmp")
	time_end=time.time()
	print('totally cost',round(time_end - time_start, 2),'secs')
#	if input("1：压缩文件\t2：解压文件\n请输入你要执行的操作：") == '1':
#		encodefile(input("请输入要压缩的文件："))
#	else:
#		decodefile(input("请输入要解压的文件："))
