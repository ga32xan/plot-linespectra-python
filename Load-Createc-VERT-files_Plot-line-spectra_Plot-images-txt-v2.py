#!/usr/bin/python2
# -*- coding: UTF-8 -*-
################################
### Load-Createc-VERT-files_Plot-line-spectra_Plot-images-txt-v1
### Version 2, 06/30/2017
## Edited for python2
### works for ### Python: 2.7.12 --  Matplotlib: 1.1.5  --  Numpy: 1.1.11  --  Scipy: 0.17.0
################################
### Alexander Riss	: Data loading and header parsing
### Mathias Pörtner	: Adding graph abilities and plotting spectral line 'maps'
### Domenik Zimmermann	: Documentation and dependency installation intstruction, version testing
################################
"""Check scalebar size => still need to get the actual size of a pixel!"""
################################
### For dependencies on Ubuntu 16.04
### sudo apt-get install python3 python3-matplotlib python3-numpy python3-scipy python3-pip python-gtk2-dev
### pip3 install matplotlib-scalebar
################################
# To use it, pls refer to the unwritten wiki :D
# Copy the script alongside with your spectral files *.L00*.VERT into a folder
# Edit the topographic image u want to show with gwyddion and save it as ASCII data matrix (.txt)
# Check lines tagged with comment "Adapt for each line spectra" and adapt the file names
# run with 'python3 Load-Createc-VERT-files_Plot-line-spectra_Plot-images-txt-v1'
################################
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt		
# did change to import pyplot NOT pylab since clearer namespace
# see https://stackoverflow.com/questions/11469336/what-is-the-difference-between-pylab-and-pyplot
from matplotlib.widgets import Slider, Button, RadioButtons
import numpy as np
from scipy.optimize import curve_fit as cv
import glob
from matplotlib import gridspec
import re
#from matplotlib_scalebar.scalebar import ScaleBar
import gwy

def string_simplify(str):
	"""simplifies a string (i.e. removes replaces space for "_", and makes it lowercase"""
	return str.replace(' ','_').lower()

def load_spec(data):
	"""Reads data file for spectral information"""	
	header = {}
	f = open(data)
	header_ended = False
	caption = re.compile(':*:')
	key = ''
	contents = ''
	while not header_ended:
		line = f.readline()
		if not line: break
		if line[0:4] == "    ":
			parts=line.split()
			posi=np.array([float(parts[-2]),float(parts[-1])],float)
			header_ended = True
		else:
			parts = line.split('=')
			if len(parts)!=2: continue
			key, contents = parts
			line = line.strip()
			key = string_simplify(key) 	# set new name
			header[key] = contents.strip()	# todo: add some parsing here
	f.close()
	
	dacstep=np.array([float(header['delta_x_/_delta_x_[dac]']),float(header['delta_y_/_delta_y_[dac]'])],float)
	pixelsize=np.array([float(header['num.x_/_num.x']),float(header['num.y_/_num.y'])],float)
	imagesize=np.array([float(header['length_x[a]']),float(header['length_y[a]'])],float)
	
	posi=posi/dacstep
	posi[0]=(pixelsize[0]/2.0+posi[0])*imagesize[0]/pixelsize[0]/10
	posi[1]=(pixelsize[1]-posi[1])*imagesize[1]/pixelsize[1]/10
    
	A=np.genfromtxt(data,delimiter='	',skip_header=212,skip_footer=0)
	U=A[:,3]
	dIdU=A[:,2]
	return(U,dIdU,posi)

def load_image(data):
	"""Reads data file for topographic information, returns X:"""	
	header = {}
	f = open(data)
	header_ended = False
	caption = re.compile(':*:')
	key = ''
	contents = ''
	while not header_ended:
		line = f.readline()
		if not line: break
		if line[0] != "#":
			header_ended = True
		else:
			parts = line.split(':')
			if len(parts)!=2: continue
			key, contents = parts
			line = line.strip()
			key = string_simplify(key[2:])
			header[key] = contents[:-4].strip()
	f.close()
	
	ext=np.array([float(header['width']),float(header['height'])],float)
	
	X=np.loadtxt(data)*1e10	#set height information to angströms, as data is saved in [m] by gwyddion
	
	return(X,ext)

def contrast(X,col):
	mini=100.0
	maxi=0.0
	for i in X:
		if max(i)>maxi:
			maxi=max(i)
		if min(i)<mini:
			mini=min(i)
	mean=np.mean([mini,maxi])

	global fig
	
	fig, ax = plt.subplots()
	plt.subplots_adjust(left=0.25, bottom=0.25)
	
	global unten
	global oben
	
	unten=mini
	oben=maxi

	global l
	
	l = plt.imshow(X, cmap=col, aspect='auto', vmin=mini, vmax=maxi)

	axcolor = 'lightgoldenrodyellow'
	axunten = plt.axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)		#facecolor=axcolor
	axoben = plt.axes([0.25, 0.15, 0.65, 0.03], axisbg=axcolor)
	
	global sunten
	global soben
	
	sunten = Slider(axunten, 'Unten', mini-(mean-mini), maxi, valinit=mini)
	soben = Slider(axoben, 'Oben', mini, maxi+(maxi-mean), valinit=maxi)
	sunten.on_changed(update)
	soben.on_changed(update)

	global buttonres
	
	resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
	buttonres = Button(resetax, 'Reset', color=axcolor, hovercolor='0.975')

	global buttonsav
	
	saveax = plt.axes([0.65, 0.025, 0.1, 0.04])
	buttonsav = Button(saveax, 'Save', color=axcolor, hovercolor='0.975')
	
	buttonres.on_clicked(reset)
	buttonsav.on_clicked(save)
	buttonsav.on_clicked(change_color)

	plt.show()

	return(unten,oben)

def update(val):
	global sunten
	global soben
	global l
	global fig
	vunten = sunten.val
	voben = soben.val
	l.set_clim(vmin=vunten, vmax=voben)
	fig.canvas.draw_idle()

def reset(event):
	global sunten
	global soben
	sunten.reset()
	soben.reset()

def change_color(event):
	global buttonsav
	global fig
	buttonsav.color = 'red'
	buttonsav.hovercolor = buttonsav.color
	fig.canvas.draw()
    
def save(val):
	global unten
	global oben
	global sunten
	global soben
	unten = sunten.val
	oben = soben.val

def f(x,a,b,c):
	return(a*(x-b)**2+c)
	
#Load data
#Adapt for each line spectra series
spec=glob.glob('F160627.153149.L*.VERT')
spec.sort()
#This is the gwyddion text matrix export of the topography file where the position of single spectra is marked
#Adapt for each line spectra
data_name='F160627.152758.txt'
ima,imagesize=load_image(data_name)
#Adapt for each line spectra
#comment if not needed
#didv,didvsize=load_image('F170509.113636-didv.txt') #optional dI/dV channel

ext=[]
matrixx=[]
matrixy=[]
spec_posi=[]
for i in spec:
	x,y,posi=load_spec(i)
	matrixy.append(y)
	matrixx.append(x)
	spec_posi.append(posi)
	if i==spec[0] or i==spec[-1]:
		ext.append(posi)
matrixx=np.array(matrixx,float)
matrixy=np.array(matrixy,float)

line_length=np.sqrt((ext[0][0]-ext[1][0])**2+(ext[0][1]-ext[1][1])**2)


#normalize specs
#change for range where max is found => -700 , 0
maxi=[]
globmaxy=0
for n,i in enumerate(matrixy):
	maxi.append(0)
	for m,j in enumerate(i):
	#Adapt for each line spectra
		if matrixx[n][m]>-700 and matrixx[n][m]<0 and matrixy[n][m]>maxi[n]:
			maxi[n]=matrixy[n][m]
	if max(i)>globmaxy:
		globmaxy=max(i)

#average specs, floating average for 5pt  so if m%5==4: should be m%(x)==(x-1):     and    [m-(x-1):m])/x
matrixyneu=[]
for n,i in enumerate(matrixy):
	matrixyneu.append([])
	for m,j in enumerate(i):
		if m%5==4:
			matrixyneu[-1].append(sum(matrixy[n][m-4:m])/5)
matrixyneu=np.array(matrixyneu,float)

# New or old contrast
#### contrast values are saved in .csv
cons=[]
ans='-'
while ans!='o' or ans!='n':
	ans=raw_input('Use (o)ld or (n)ew values for contrast? (o/n) ')
	if ans=='o':
		cons=np.loadtxt(data_name[:-4]+'.csv',delimiter=',')
		break
	elif ans=='n':
		#find out clim topo
		topounten,topooben=contrast(ima,'viridis')
		cons.append(topounten)
		cons.append(topooben)
		#find out clim didv

		#comment 3 following line if no dI/dV
#		didvunten,didvoben=contrast(didv,'afmhot')
#		cons.append(didvunten)
#		cons.append(didvoben)

		#find out clim specs along line
		specunten,specoben=contrast(matrixyneu.T,'afmhot')
		cons.append(specunten)
		cons.append(specoben)
		np.savetxt(data_name[:-4]+'.csv',cons,delimiter=',')
		break
######################### Plot section #########################
## Font setup # Total image size # Plots to show
fontna=16
fontnu=12
####plt.figure(figsize=(x,y) determines size of graphic in x,y direction, values given in inches
##	without dI/dV => figsize=(10,5)		with dI/dV => figsize=(15,5)		
plt.figure(figsize=(10,5),dpi=300,tight_layout=True)    # tight_layout=False may be required for tweeking
##	without dI/dV => .GridSpec(1, 2)	with dI/dV => .GridSpec(1, 3)
gs = gridspec.GridSpec(1, 2)

######## Plots topography image
plt.subplot(gs[0])
plt.title('Topography',fontsize=fontna)
plt.imshow(ima,cmap='viridis',extent=[0,imagesize[0],0,imagesize[1]],vmin=cons[0],vmax=cons[1])

## draw without ticks, if ticks wanted => comment following two lines
plt.xticks([])
plt.yticks([])
##

# plots points of spectra in topography
# ms controlls size of dots for spectral positions, o is for circles, . for dots
for pos in spec_posi:
	plt.plot(pos[0],pos[1],'o',color='white',ms=3)

"""
scalebar = ScaleBar(1e-10) # 1 pixel = x meter
plt.gca().add_artist(scalebar)
"""

#plots scalebar on starting position, (0,0) is lower left corner
for x in np.linspace(1,6,1000):		#creates an array with 1000 points in the closed interval between [1,6]
	plt.plot(x,5,color='black')
## Needs some work to be done - doesn't work!

#inserts color bar for topography image
#plt.colorbar()

######## Plots dI/dV image
"""
#plt.subplot(gs[1])
#plt.title('dI/dV',fontsize=fontna)
#plt.imshow(didv,cmap='afmhot',extent=[0,11.05,0,11.05*230/512],vmin=cons[2],vmax=cons[3])

## draw without ticks, if ticks wanted => comment following two lines
#plt.xticks([])
#plt.yticks([])
##

##sets scalebar (0,0) unten links referenz
#for x in np.linspace(1,6,1000):
#	plt.plot(x,1,color='white')
"""

######## Plots spectral map
## set new position of spectral map if no dI/dV is present
## without dI/dV => plt.subplot(gs[1])		with dI/dV => plt.subplot(gs[2])
plt.subplot(gs[1])
plt.title('Line spectra',fontsize=fontna)
# configures line spectra 'map'
# with dI/dV 	=> 
# plt.imshow(matrixy.T,cmap='afmhot',extent=[0,line_length,min(matrixx[0]),max(matrixx[0])],aspect='auto',vmin=cons[4],vmax=cons[5])
# without dI/dV => 
# plt.imshow(matrixy.T,cmap='afmhot',extent=[0,line_length,min(matrixx[0]),max(matrixx[0])],aspect='auto',vmin=cons[2],vmax=cons[3])
plt.imshow(matrixy.T,cmap='afmhot',extent=[0,line_length,min(matrixx[0]),max(matrixx[0])],aspect='auto',vmin=cons[2],vmax=cons[3])

#sets xlabel
plt.xlabel('Distance x [nm]',fontsize=fontna)
plt.xticks(fontsize=fontnu)
#sets y-label
plt.ylabel('Bias voltage [mV]',fontsize=fontna)

## use plt.yticks(fontsize=fontnu) for automatic values or give fixed values like plt.yticks([-1000,0,1000],fontsize=fontnu)
plt.yticks(fontsize=fontnu)

#inserts color bar for spectral map
# plt.colorbar()

# add some free space at corners
plt.subplots_adjust(top=0.95,right=1,left=0,bottom=0)

######### Save to pdf and display 
#saves figure in pdf file, png, jpg
plt.savefig(data_name[:-4]+'.pdf')
#display
#plt.show()
