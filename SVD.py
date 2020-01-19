# -*- coding: utf-8 -*-
'''
author@sunqixin
date:2019/11/8
'''
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
#转为u8类型
def svdCompression(A, eta = 1):
	# eta为压缩阈值（保留下来的奇异值在所有奇异值总和中的占比，默认为1）
	u, sigma, v = np.linalg.svd(A)
	m = len(u)
	n = len(v)
	a = np.zeros((m, n))
	curSum = 0
	count = eta * sum(sigma)
	for k in range(min(m,n)):
		if curSum > count:
			break
		else:
			curSum += sigma[k]
	k += 1
	uk = u[:, :k]
	sigmak = sigma[:k]
	vk = v[:k]
	return uk, sigmak, vk, k

def imgSVD(a,eta = 1):
	#a的最内层数组为三个数，分别表示RGB，用来表示一个像素
	ur, sigmar, vr, kr = svdCompression(a[:, :, 0], eta)
	#按照最近距离取整数，并设置参数类型为uint8
	R = np.rint(ur.dot(np.diag(sigmar)).dot(vr).clip(0,255)).astype('uint8')
	ug, sigmag, vg, kg = svdCompression(a[:, :, 1], eta)
	G = np.rint(ug.dot(np.diag(sigmag)).dot(vg).clip(0,255)).astype('uint8')
	ub, sigmab, vb, kb = svdCompression(a[:, :, 2], eta)
	B = np.rint(ub.dot(np.diag(sigmab)).dot(vb).clip(0,255)).astype('uint8')
	I = np.stack((R, G, B), axis = 2)
	return I

if __name__ == "__main__":
	#设置字体为SimHei显示中文
	mpl.rcParams['font.sans-serif'] = [u'simHei']
	#设置正常显示字符，用来显示负号
	mpl.rcParams['axes.unicode_minus'] = False
	name = 'f3'
	frame = plt.imread(name+'.bmp')
	a = np.array(frame)
	I = imgSVD(a,0.7)
	plt.imshow(I)
	plt.axis("off")
	plt.gca().xaxis.set_major_locator(plt.NullLocator())
	plt.gca().yaxis.set_major_locator(plt.NullLocator())
	plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
	plt.margins(0,0)
	plt.gcf().savefig(name+'.png', transparent=True, pad_inches = 0)
	plt.show()