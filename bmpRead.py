# -*- coding: UTF-8 -*-
import matplotlib.pyplot as plt
import numpy as np

# 读取并存储 bmp 文件
class ReadBMPFile :
	def __init__(self, filePath) :
		file = open(filePath, "rb")
		# 读取 bmp 文件的文件头 14 字节
		self.bfType = file.read(2)									# BM 表示这是Windows支持的位图格式
		self.bfSize = int.from_bytes(file.read(4), 'little')		# 位图文件大小
		self.bfReserved1 = int.from_bytes(file.read(2), 'little')	# 保留字段 必须设为 0
		self.bfReserved2 = int.from_bytes(file.read(2), 'little')	# 保留字段 必须设为 0
		self.bfOffBits = int.from_bytes(file.read(4), 'little')		# 偏移量 从文件头到位图数据需偏移多少字节
		# 读取 bmp 文件的位图信息头 40 字节
		self.biSize = int.from_bytes(file.read(4), 'little')			# 所需要的字节数
		self.biWidth = int.from_bytes(file.read(4), 'little')			# 图像的宽度 单位 像素
		self.biHeight = int.from_bytes(file.read(4), 'little')			# 图像的高度 单位 像素
		self.biPlanes = int.from_bytes(file.read(2), 'little')			# 说明颜色平面数 总设为 1
		self.biBitCount = int.from_bytes(file.read(2), 'little')		# 说明比特数
		self.biCompression = int.from_bytes(file.read(4), 'little')		# 图像压缩的数据类型
		self.biSizeImage = int.from_bytes(file.read(4), 'little')		# 图像大小
		self.biXPelsPerMeter = int.from_bytes(file.read(4), 'little')	# 水平分辨率
		self.biYPelsPerMeter = int.from_bytes(file.read(4), 'little')	# 垂直分辨率
		self.biClrUsed = int.from_bytes(file.read(4), 'little')			# 实际使用的彩色表中的颜色索引数
		self.biClrImportant = int.from_bytes(file.read(4), 'little')	# 对图像显示有重要影响的颜色索引的数目
		if self.biBitCount != 24 :
			print("输入的图片比特值为：" + str(self.biBitCount) + "\t 与程序不匹配")

		# R, G, B 三个通道
		self.R = []
		self.G = []
		self.B = []
		for _height in range(self.biHeight) :
			R_row = []
			G_row = []
			B_row = []
			# 四字节填充位检测
			count = 0
			for _width in range(self.biWidth) :
				B_row.append(int.from_bytes(file.read(1), 'little'))
				G_row.append(int.from_bytes(file.read(1), 'little'))
				R_row.append(int.from_bytes(file.read(1), 'little'))
				count += 3
			# bmp 四字节对齐原则
			while count % 4 != 0 :
				file.read(1)
				count += 1
			self.B.append(B_row)
			self.G.append(G_row)
			self.R.append(R_row)
		self.B.reverse()
		self.G.reverse()
		self.R.reverse()
		file.close()

if __name__ == "__main__":
	# 命令行传入的文件路径
	# filePath = input("请输入文件：")
	filePath = "f3.bmp"
	# 读取 BMP 文件
	bmpFile = ReadBMPFile(filePath)
	# 显示图像
	pic = np.stack((bmpFile.R, bmpFile.G, bmpFile.B), axis = 2)
	plt.imshow(pic)
	plt.axis("off")
	plt.show()