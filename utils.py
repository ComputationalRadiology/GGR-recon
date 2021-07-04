import numpy as np
import SimpleITK as sitk
from numpy.fft import fftn, ifftn
from random import randint
from rich.panel import Panel
from rich.highlighter import Highlighter

app_name = 'GGR-recon'
version = '0.9.0'
release_date = '2021-07-01'

def print_header(console):
	console.print('\n\n')
	console.print(app_name, '- version: v', version,
			release_date, '\n', justify='center')
	console.print(Panel.fit('Computational Radiology Lab ([b]CRL[/b])\nBoston Children\'s Hospital, and Harvard Medical School\n[u][i][blue]http://crl.med.harvard.edu/[/u][/i][/blue]'), justify='center')
	console.print('\n')

class RainbowHighlighter(Highlighter):
	def highlight(self, text):
		for index in range(len(text)):
			text.stylize(f"color({randint(1, 255)})", index, index + 1)

def imread(fn):
	return sitk.ReadImage(fn, sitk.sitkFloat32)

def imwrite(img, fn):
	sitk.WriteImage(sitk.Cast(img, sitk.sitkFloat32), fn)

def np_to_img(x, ref):
	img = sitk.GetImageFromArray(x)
	img.SetOrigin(ref.GetOrigin())
	img.SetSpacing(ref.GetSpacing())
	img.SetDirection(ref.GetDirection())
	return img

def resample_img(img, spacing, sz):
	r = sitk.ResampleImageFilter()
	r.SetInterpolator(sitk.sitkBSpline)
	r.SetDefaultPixelValue(0)
	r.SetOutputOrigin(img.GetOrigin())
	r.SetOutputSpacing(spacing)
	r.SetOutputDirection(img.GetDirection())
	r.SetSize(sz)
	return r.Execute(img)

def resample_iso_img(img):
	spacing = np.array(img.GetSpacing())
	new_spacing = np.array([min(spacing)] * 3)

	sz = np.array(img.GetSize())
	new_sz = np.floor(spacing / new_spacing * sz).astype(np.uint32)
	new_sz[new_sz % 2 == 1] -= 1

	return resample_img(img, new_spacing, new_sz.tolist())

def resample_iso_img_with_size(img, sz):
	spacing = np.array(img.GetSpacing())
	new_spacing = np.array([min(spacing)] * 3)

	new_sz = np.array(sz)
	new_sz[new_sz % 2 == 1] -= 1

	return resample_img(img, new_spacing, new_sz.tolist())

def resample_img_like(img, ref):
	r = sitk.ResampleImageFilter()
	r.SetInterpolator(sitk.sitkBSpline)
	r.SetDefaultPixelValue(0)
	r.SetOutputOrigin(ref.GetOrigin())
	r.SetOutputSpacing(ref.GetSpacing())
	r.SetOutputDirection(ref.GetDirection())
	r.SetSize(ref.GetSize())
	return r.Execute(img)

def dumb_update(task, advance):
	pass

def recon_tik(y, w, tv_weight=0.1, progress=None, task=None):
	advance = 65/6
	if progress != None and task!=None:
		update_progress = progress.update
	else:
		update_progress = dumb_update

	d, n, m, n_imgs_per_echo = y.shape
	dx = np.zeros([d,n,m])
	dx[0,0,0] = -1
	dx[1,0,0] = 1
	dx = fftn(dx, [d,n,m])

	update_progress(task, advance=advance)

	dy = np.zeros([d,n,m])
	dy[0,0,0] = -1
	dy[0,1,0] = 1
	dy = fftn(dy, [d,n,m])

	update_progress(task, advance=advance)

	dz = np.zeros([d,n,m])
	dz[0,0,0] = -1
	dz[0,0,1] = 1
	dz = fftn(dz, [d,n,m])

	update_progress(task, advance=advance)

	w_tik = np.conj(dx)*dx + np.conj(dy)*dy + np.conj(dz)*dz

	update_progress(task, advance=advance)

	wy, ww = 0, 0
	for jj in range(0, n_imgs_per_echo):
		wy += np.conj(w[...,jj]) * y[...,jj]
		ww += np.conj(w[...,jj]) * w[...,jj]

	update_progress(task, advance=advance)

	fft_x = wy / (ww + tv_weight * w_tik)

	update_progress(task, advance=advance)

	return fft_x.astype(np.complex64)

def recon_ggr(y, w, grad_ref, ggr_weight=0.1,
		tau_percent=0.8, p=2, alpha=0.6, progress=None, task=None):
	# y: interpolated low-res images in Fourier domain
	# w: convolutional filters
	# grad_ref: spatial gradient images
	# ggr_weight: regularization weight
	# tau_percent: edge-enhanced function
	# p: scale of gradients
	# alpha: bilateral TV

	advance = 25/3
	if progress != None and task != None:
		update_progress = progress.update
	else:
		update_progress = dumb_udpate

	# created gradient operators
	d, n, m, n_imgs_per_echo = y.shape
	d1_m1 = fftn(np.array([[[-1]],[[1]]], dtype=np.float32), [d,n,m])
	d1_p1 = fftn(np.array([[[1]],[[-1]]], dtype=np.float32), [d,n,m])
	d2_m1 = fftn(np.array([[[-1],[1]]], dtype=np.float32), [d,n,m])
	d2_p1 = fftn(np.array([[[1],[-1]]], dtype=np.float32), [d,n,m])
	d3_m1 = fftn(np.array([[[-1,1]]], dtype=np.float32), [d,n,m])
	d3_p1 = fftn(np.array([[[1,-1]]], dtype=np.float32), [d,n,m])

	d1_m2 = fftn(np.array([[[-1]],[[0]],[[1]]], dtype=np.float32), [d,n,m])
	d1_p2 = fftn(np.array([[[1]],[[0]],[[-1]]], dtype=np.float32), [d,n,m])
	d2_m2 = fftn(np.array([[[-1],[0],[1]]], dtype=np.float32), [d,n,m])
	d2_p2 = fftn(np.array([[[1],[0],[-1]]], dtype=np.float32), [d,n,m])
	d3_m2 = fftn(np.array([[[-1,0,1]]], dtype=np.float32), [d,n,m])
	d3_p2 = fftn(np.array([[[1,0,-1]]], dtype=np.float32), [d,n,m])

	d1 = [d1_m2, d1_m1, 1, d1_p1, d1_p2]
	d2 = [d2_m2, d2_m1, 1, d2_p1, d2_p2]
	d3 = [d3_m2, d3_m1, 1, d3_p1, d3_p2]

	update_progress(task, advance=advance)

	# deconvolution
	DG, DD = 0, 0
	for ll in range(-p, p+1):
		for pp in range(0, p+1):
			for qq in range(0, p+1):
				if ll+pp+qq < 0 or (ll==0 and pp==0 and qq==0):
					continue

				a = alpha**(abs(ll)+abs(pp)+abs(qq))
				D = d1[ll+p] * d2[pp+p] * d3[qq+p]
				g = ifftn(D * grad_ref).real.astype(np.float32)

				sg = np.sort(np.abs(g)).flatten()
				tau = sg[int(sg.size * tau_percent)]

				G = fftn(g / (1 + (tau / g)**4), [d,n,m])

				DG += a * np.conj(D) * G
				DD += a * np.conj(D) * D

				update_progress(task, advance=1)

	WY, WW = 0, 0
	for jj in range(0, n_imgs_per_echo):
		WY += np.conj(w[...,jj]) * y[...,jj]
		WW += np.conj(w[...,jj]) * w[...,jj]

	update_progress(task, advance=advance)

	fft_x = (WY + ggr_weight * DG) / (WW + ggr_weight * DD)

	update_progress(task, advance=advance)

	return fft_x.astype(np.complex64)
