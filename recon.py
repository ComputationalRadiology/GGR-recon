#!/usr/bin/env python3

import numpy as np
import SimpleITK as sitk
from numpy.fft import fftn, ifftn
from scipy.io import loadmat, savemat
from scipy import signal
import glob
import os
import time
import argparse

import warnings
warnings.filterwarnings("ignore")

from utils import *

from rich.console import Console
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TextColumn, \
		BarColumn, TimeElapsedColumn, TimeRemainingColumn

parser = argparse.ArgumentParser()
parser.add_argument('-V', '--version', action='version',
		version='%s version : v %s %s' % (app_name, version, release_date),
		help='show version')
group = parser.add_mutually_exclusive_group()
group.add_argument('--ggr', action='store_true',
		help='use GGR regularization, default')
group.add_argument('--tik', action='store_true',
		help='use Tikhonov regularization')
parser.add_argument('-w', '--reg-weight',
		help='weight of the regularization, by default is 0.1',
		type=float, default=0.1)
parser.add_argument('--keep-negative-values', action='store_true',
		help='keep negative voxel values in the reconstructed image, by default is false',
		default=False)
args = parser.parse_args()

reg_weight = args.reg_weight
reg = 1 # ggr: 1, tik: 0
reg_desc = 'GGR'
if args.tik:
	reg = 0 # 'tik'
	reg_desc = 'Tikhonov'
keep_negative_values = args.keep_negative_values

path = '/opt/GGR-recon/data/'
working_path = '/opt/GGR-recon/working/'
out_path = '/opt/GGR-recon/recons/'

if not os.path.isdir(out_path):
	os.mkdir(out_path)
if not os.path.isdir(working_path):
	print('No working data provided')
	print('Run preprocess.py to generate the data')
	exit()

geo = loadmat(working_path + 'geo_property.mat')
sz = geo['sz'][0]

img_fn, h_fn = [], []
with open(working_path + 'data_fn.txt', 'r') as f:
	for line in f:
		fn = line[:-1].split(',')
		img_fn.append(fn[0])
		h_fn.append(fn[1])

n_imgs = len(img_fn)

if n_imgs == 0:
	print('No image data found!')
	exit()

console = Console()
# =========== Print summary of the execution =============
print_header(console)

table = Table(title='Summary of %s execution' % app_name,
		box=box.HORIZONTALS,
		show_header=True, header_style='bold magenta')
table.add_column('Reg. method', justify='center')
table.add_column('Reg. weight', justify='center')
table.add_column('Image size', justify='center', no_wrap=True)
table.add_column('# images', justify='center')
table.add_column('Resolution (mm)', justify='center', no_wrap=True)
table.add_row(reg_desc, str(reg_weight), str(sz),
		str(n_imgs), str(geo['spacing'][0][0]))
console.print(table, justify='center')
console.print('\n')

progress = Progress(TextColumn("[progress.description]{task.description}"),
		"[progress.percentage]({task.percentage:>3.1f}%)",
		BarColumn(bar_width=None), TimeElapsedColumn(),
		console=console, refresh_per_second=2)

def update_progress(task, desc, advance=1):
	if not progress.finished:
		progress.update(task, description=desc, advance=advance)
	else:
		console.print('[red bold]progress finished')

with progress:
	task = progress.add_task('[blue]Starting...', total=100)#, start=False)
	
	m, n, d = sz
	fft_img = np.empty([d, n, m, n_imgs], dtype=np.complex64)
	w = np.empty_like(fft_img)
	for ii in range(0, n_imgs):
		img = imread(working_path + img_fn[ii])
		fft_img[...,ii] = fftn(sitk.GetArrayFromImage(img))
		w[...,ii] = loadmat(working_path + h_fn[ii])['fft_win']
		
		update_progress(task, '[green]Loading images...', advance=20/n_imgs)
	
	mean_fns = glob.glob(out_path + 'img_mean.*')
	if len(mean_fns) > 1:
		console.print('[red bold]Error: Please check you "recons" folder to make sure there is only [i][u]ONE[/u][/i] file named "img_mean", and then run [i]recon.py[/i] again.')
		exit()

	mean_fn = mean_fns[0]
	ext = mean_fn[len(out_path + 'img_mean'):]
	
	mean_img = imread(mean_fn)
	mean_arr = sitk.GetArrayFromImage(mean_img)
	
	update_progress(task, '[cyan]Reconstructing...', advance=5)
	
	if reg == 1: # ggr: 1, tik: 0
		fft_x = recon_ggr(fft_img, w, mean_arr,
				ggr_weight=reg_weight, progress=progress, task=task)
		out_fn = out_path + 'recon_ggr-w' + str(reg_weight) + ext
	else:
		fft_x = recon_tik(fft_img, w,
				tv_weight=reg_weight, progress=progress, task=task)
		out_fn = out_path + 'recon_tik-w' + str(reg_weight) + ext
	
	#x = np.clip(ifftn(fft_x).real.astype(np.float32), 0, None)
	#x = np.abs(ifftn(fft_x)).astype(np.float32)
	if keep_negative_values:
		x = ifftn(fft_x).real.astype(np.float32)
	else:
		x = np.clip(ifftn(fft_x).real.astype(np.float32), 0, None)
	
	update_progress(task, '[yellow]Saving image...', advance=5)
	
	img_x = np_to_img(x, mean_img)
	imwrite(img_x, out_fn)
	
	update_progress(task, '[green bold]Completed! :ok_hand:', advance=5)

rainbow = RainbowHighlighter()
console.print('\n')
console.print(rainbow('High-res reconstruction has been generated'))
console.print('See the image at: [cyan italic]%s\n' % out_fn)
