#!/usr/bin/env python3

import numpy as np
import SimpleITK as sitk
from scipy.io import loadmat, savemat
from scipy import signal
import os
import time
import argparse

from utils import *

from rich.console import Console
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

parser = argparse.ArgumentParser()
parser.add_argument('-V', '--version', action='version',
		version='%s version : v %s %s' % (app_name, version, release_date),
		help='show version')
parser.add_argument('-f', '--filenames', nargs='+', 
		help='filenames of input the low-res images; (full path required)\
				e.g., -i a.nii.gz b.nii.gz c.nii.gz')
'''
parser.add_argument('-f', '--format', nargs='+', default='.nii.gz',
		help='formats of the low-res images, by default is .nii.gz; \
				no repeated elements included; \
				e.g., -f .nhdr .nrrd .nii .nii.gz')
'''
parser.add_argument('-s', '--size', nargs='+', type=int,
		help='size of the high-res reconstruction, optional; \
				even positive integers required if set; \
                e.g., -s 312 384 330')
parser.add_argument('-r', '--resample', action='store_true',
		help='resample the first low-res image in the high-res lattice \
				and then exit. Usually used for determining a user \
				defined size of the high-res reconstruction')
args = parser.parse_args()
flist = args.filenames
sz = args.size
resample_only = args.resample

n_imgs = len(flist)

if n_imgs == 0:
	print('No image data found!')
	exit()

if sz != None and (len(sz) != n_imgs or np.any(np.array(sz) <= 0)):
	print('SIZE =', sz)
	print('Error: SIZE should comprise positive integers')
	exit()

'''
fn_ext = args.format
if isinstance(fn_ext, str):
	fn_ext = [fn_ext]

if len(fn_ext) != len(np.unique(fn_ext)):
	print('FORMAT =', fn_ext)
	print('Error: elements of FORMAT should be unique')
	exit()

if np.any([not fmt.startswith('.') for fmt in fn_ext]):
	print('FORMAT =', fn_ext)
	print('Error: each element of FORMAT should start with .(dot)')
	exit()
'''

#path = '/opt/GGR-recon/data/'
working_path = '/opt/GGR-recon/working/'
out_path = '/opt/GGR-recon/recons/'

'''
if not os.path.isdir(path):
	print('Low-res images should be put in ./data')
	exit()
'''
if not os.path.isdir(out_path):
	os.mkdir(out_path)
if not os.path.isdir(working_path):
	os.mkdir(working_path)


img_path = []
img_fn = []
img_ext = []
'''
for e in fn_ext:
	img_fn += [f.rsplit(e, 1)[0] for f in flist if f.endswith(e)]
	img_ext += [e] * len(img_fn)
'''

for filename in flist:
	(path, fn) = os.path.split(filename)
	if not path.endswith('/'):
		path += '/'
	(fn, ext) = os.path.splitext(fn)
	
	img_path.append(path)
	img_fn.append(fn)
	img_ext.append(ext)


console = Console()
print_header(console)



# step 0: make the orientations the same for all LR images
for ii in range(0, n_imgs):
	os.system('crlOrientImage %s%s%s %s%s%s' %
			(img_path[ii], img_fn[ii], img_ext[ii],
				working_path, img_fn[ii], img_ext[ii]))
#print('completed step 0')
#print('\t- make the orientations the same for all LR images')

# step 1: resample the images
img0 = imread(working_path + img_fn[0] + img_ext[0])
if sz == None:
	img0x = resample_iso_img(img0)
	sz = img0x.GetSize()
else:
	img0x = resample_iso_img_with_size(img0, sz)

sz = img0x.GetSize() # update the variable of image size

# =========== Print summary of the execution =============
mode = 'Preprocessing'
if resample_only:
	mode = 'Resampling'
table = Table(title='Summary of %s/preprocess.py execution' % app_name,
		box=box.HORIZONTALS,
		show_header=True, header_style='bold magenta')
table.add_column('Mode', justify='center')
table.add_column('# images', justify='center')
table.add_column('Images', justify='center')
table.add_column('Image size', justify='center', no_wrap=True)
table.add_column('Resolution', justify='center')
table.add_row(mode, str(n_imgs),
		str([s1+s2 for s1, s2 in zip(img_fn, img_ext)]),
		str(sz), '%0.4f mm'%img0x.GetSpacing()[0])
console.print(table, justify='center')
console.print('\n')


if resample_only:
	imwrite(img0x, out_path + img_fn[0] + '_x' + img_ext[0])
	rainbow = RainbowHighlighter()
	console.print(rainbow('The first low-res image has been resampled in the high-res lattice'))
	console.print('\n')
	console.print('See it at: [green italic]%s' \
			% out_path + img_fn[0] + '_x' + img_ext[0])
	console.print('\n\n')
	exit()

imwrite(img0x, working_path + img_fn[0] + '_x' + img_ext[0])

origin = img0x.GetOrigin()
spacing = img0x.GetSpacing()
direction = img0x.GetDirection()

lr_size = np.zeros([3, n_imgs])
lr_spacing = np.zeros([3, n_imgs])
lr_size[:,0] = np.array(img0.GetSize(), dtype=np.int64)
lr_size[lr_size[:,0]%2!=0,0] -= 1
lr_spacing[:,0] = np.array(img0.GetSpacing())
for ii in track(range(1, n_imgs), '[yellow]Resampling images...'):
	img = imread(working_path + img_fn[ii] + img_ext[ii])
	lr_spacing[:,ii] = np.array(img.GetSpacing())
	lr_size[:,ii] = np.array(img.GetSize())

	lr_size[:,ii] = np.minimum(lr_size[:,ii],
			np.around(spacing / lr_spacing[:,ii] * sz)).astype(np.int64)
	lr_size[lr_size[:,ii]%2!=0,ii] -= 1

	I = resample_img_like(img, img0x)
	imwrite(I, working_path + img_fn[ii] + '_x' + img_ext[ii])

savemat(working_path + 'geo_property.mat', {'sz': sz, 'origin': origin, \
		'spacing': spacing, 'direction': direction})

prefix = [''] + ['reg_'] * (n_imgs - 1)
sufix = ['_x'] * n_imgs
txt = [''.join(s) for s in zip(*[prefix, img_fn, sufix, img_ext])]
with open(working_path + 'data_fn.txt', 'w') as f:
	for ii, fn in enumerate(txt):
		f.write('%s,%s\n' % (fn, 'h_'+img_fn[ii]+'.mat'))

#print('completed step 1')
#print('\t- resample the images')

# step 2: align up all resampled images
for ii in track(range(1, n_imgs), '[magenta]Aligning images...'):
	cmd = 'crlRigidRegistration -t 2 %s%s_x%s %s%s_x%s \
			%sreg_%s_x%s %stfm2_%s.tfm > /dev/null 2>&1' % \
			(working_path, img_fn[0], img_ext[0], \
			working_path, img_fn[ii], img_ext[ii], \
			working_path, img_fn[ii], img_ext[ii], \
			working_path, img_fn[ii])
	os.system(cmd)
#print('completed step 2')
#print('\t- align up all resampled images')

# step 3: create filters for deconvolution
for ii in track(range(0, n_imgs), '[cyan]Creating filters...'):
	fft_win = 1
	max_factor = -np.inf
	for jj in range(0, 3):
		factor = lr_spacing[jj,ii] / spacing[jj]
		if factor > 1:
			# FWHM in the unit of number of pixel and convert it to sigma
			sigma = factor / 2.355
			filter_len = sz[jj]
			gw = signal.gaussian(filter_len, std=sigma)
			gw /= np.sum(gw)
			# put it onto 3D space
			shape = np.ones(3, dtype=np.int64)
			shape[jj] = filter_len
			gw = np.reshape(gw, shape)
			gw = np.roll(gw, -filter_len//2, axis=jj)
			# move it to Fourier domain
			GW = np.abs(fftn(gw, sz))

			w1_sz = np.array(sz, dtype=np.int64)
			w1_sz[jj] = lr_size[jj,ii] // 2
			w0_sz = np.array(sz, dtype=np.int64)
			w0_sz[jj] -= lr_size[jj,ii]
			w = np.concatenate([np.ones(w1_sz), \
					np.zeros(w0_sz), np.ones(w1_sz)], axis=jj)
			#fft_win *= np.transpose(w * GW + 1j * w * GW, axes=[2,1,0])
			if max_factor < factor:
				fft_win = np.transpose(w * GW + 1j * w * GW, axes=[2,1,0])
				max_factor = factor

	savemat(working_path+'h_'+img_fn[ii]+'.mat', {'fft_win': fft_win})

#print('completed step 3')
#print('\t- create filters for deconvolution')

# step 4: volume fusion
z = sitk.GetArrayFromImage(img0x)
L = np.ones_like(z)
for ii in track(range(1, n_imgs), '[medium_purple]Fusing images...'):
	img = imread(working_path + 'reg_' + img_fn[ii] + '_x' + img_ext[ii])
	a = sitk.GetArrayFromImage(img)
	z += a
	L += (a != 0).astype(np.float32)

z[L!=0] = z[L!=0] / L[L!=0]

img_z = np_to_img(z, img0x)
imwrite(img_z, out_path + 'img_mean' + img_ext[0])

#print('completd step 4')
#print('\t- volume fusion')

# rainbow = RainbowHighlighter()
console.print('\n')
console.print('THE PRE-PROCESSING HAS BEEN COMPLETED.')
console.print('\n')
