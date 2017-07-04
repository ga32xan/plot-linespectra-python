#!/usr/bin/python3
# -*- coding: UTF-8 -*-
################################
### Load-Createc-VERT-files_Plot-line-spectra_Plot-images-txt-v4
### Version 3, 06/30/2017
### works for ### Python: 3.5.2 --  Matplotlib: 1.1.5  --  Numpy: 1.1.11  --  Scipy: 0.17.0
################################
### Alexander Riss	: Data loading and header parsing
### Mathias Pörtner	: Adding graph abilities and plotting spectral line 'maps'
### Domenik Zimmermann	: Documentation and dependency checks, GUI, debug modes 
################################
"""Check scalebar size => still need to get the actual size of a pixel!"""
""" Disable / Enable in line 369 (Topography) / line 394 (dI/dV)"""
################################
### For dependencies on Ubuntu 16.04
### sudo apt-get install python3 python3-matplotlib python3-numpy python3-scipy python3-pip python-gtk2-dev
### pip3 install matplotlib-scalebar
################################
# Copy the script alongside with your spectral files *.L00*.VERT into a folder
# Edit the topographic image u want to show with gwyddion and save it as ASCII data matrix (.txt) in the same folder
# Optional: Edit the dI/dV image u want and save it as ASCII data matrix (.txt) in the same folder
#################### EDIT HERE ####################
#This is where the series of line spectra can be found
#spectrum_files = 'F160627.153149.L*.VERT'
contrast_spec = 'afmhot'
#This is the gwyddion text matrix export of the topography file, level beforehand
#Important: Do not trim images, and record them in the same size as u did the spectra on
#!Otherwise the positions will not match! => see non-square.txt and non-sqaure.pdf
#data_name='F160627.152758.txt'
contrast_topo = 'afmhot'
#This is the gwyddion text matrix export of the topography file
#didv_name='didv.txt'
contrast_didv = 'afmhot'
#with_didv = 0
###################################################
# run with 'python3 Load-Createc-VERT-files_Plot-line-spectra_Plot-images-txt-v4'
################################
#
## color maps. Please refer to https://matplotlib.org/examples/color/colormaps_reference.html
## and change lines 25,28,31
#
#### DEBUG mode ####
debug = 1
debug2= 1	#adds some return values of functions ... gets a little messy
################################
## Terminal Color ANSI escape sequences
class bcolors:
    HEADER 		= '\033[95m'
    OKBLUE 		= '\033[94m'
    WARNING 	= '\033[93m'
    OKGREEN 	= '\033[92m'
    FAIL 		= '\033[91m'
    ENDC 		= '\033[0m'
    BOLD 		= '\033[1m'
    UNDERLINE 	= '\033[4m'
################################

import matplotlib
matplotlib.use('TkAgg') 		#uses tkinter as backend for displaying graphs
import matplotlib.pyplot as plt		
#import matplotlib.ticker as ticker		#Play-around with tick spacings etc. NOT implemented
# did change to import pyplot NOT pylab since clearer namespace
# see https://stackoverflow.com/questions/11469336/what-is-the-difference-between-pylab-and-pyplot
from matplotlib.widgets import Slider, Button, RadioButtons
import numpy as np
from scipy.optimize import curve_fit as cv
import glob
from matplotlib import gridspec
import re
from matplotlib_scalebar.scalebar import ScaleBar
##for file choosing dialog ##
import tkinter as tk
from tkinter import filedialog
##

def string_simplify(str):
	"""simplifies a string (i.e. removes replaces space for "_", and makes it lowercase"""
	return str.replace(' ','_').lower()

def load_spec(data):
	"""Reads data file for spectral information"""	
	header = {}
	f = open(data, encoding='utf-8', errors='ignore')
	if debug2: print(bcolors.OKBLUE + "\nThis is funcion load_spec()" + bcolors.ENDC)	
	if debug2: print(bcolors.OKBLUE + "...from file: {0}....".format(data) + bcolors.ENDC)
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

	global pixelnumber
	pixelnumber = pixelsize[0]		# gets numbers of pixels in a line
#	print("Spectral image is {0} pixel wide".format(pixelnumber))
#	global scalebar_pixelsize
#	scalebar_pixelsize=imagesize[0]*1e-10/pixelsize[0]		# global variable to calculate how large a pixel is in [m]

	A=np.genfromtxt(data,delimiter='	',skip_header=212,skip_footer=0)
	U=A[:,3]
	dIdU=A[:,2]
	return(U,dIdU,posi)

def load_image(data):
	"""Reads data file for topographic information, returns X:"""	
	header = {}
	f = open(data, encoding='utf-8', errors='ignore')
	if debug2:	print(bcolors.OKBLUE + "\nThis is funcion load_image()" + bcolors.ENDC)	
	if debug2:	print("...Loading data from file: {0}....".format(data))
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
	global imagewidth
	imagewidth = ext[0]*1e-9	#fetches imagewidth in meter
	if debug: print("Image is {0} meter wide".format(imagewidth))
	X=np.loadtxt(data)*1e10		#set height information to angströms, as data is saved in [m] by gwyddion
	if debug2: print(bcolors.OKBLUE + "returing X with {2}\n{0} \n and \next {3}\n{1}".format(X,ext,type(X),type(ext)) + bcolors.ENDC)	
	return(X,ext)			#X contains height information in A as [[]] , ext contains amge width in nm as []

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
	print(bcolors.WARNING + "\nPlease adjust contrast and click \"Save\"" + bcolors.ENDC)
	print(bcolors.WARNING + "Close " + bcolors.UNDERLINE + "Popup" + bcolors.ENDC + bcolors.WARNING + " window afterwards" + bcolors.ENDC)

	axcolor = 'lightgoldenrodyellow'
	axunten = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)		#facecolor=axcolor
	axoben = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)
	
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
########################################################################################
###########################  MAIN ROUTINE  #############################################
########################################################################################
########################################################################################
if debug2:	print(bcolors.OKBLUE + "\nThis is funcion main()" + bcolors.ENDC)
print(bcolors.HEADER + "#######################################################################" + bcolors.ENDC)
print(bcolors.HEADER + "### Load-Createc-VERT-files_Plot-line-spectra_Plot-images-txt-v3 \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "###\t \t \t Version 3, 06/30/2017 \t \t \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "### works with \t Python: 3.5.2  \t \t \t \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "### \t \t Matplotlib: 1.1.5 \t \t \t \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "### \t \t Numpy: 1.1.11 \t \t \t \t \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "### \t \t Scipy: 0.17.0 \t \t \t \t \t ###" + bcolors.ENDC)
print(bcolors.HEADER + "#######################################################################" + bcolors.ENDC)

#Load data
#Topography
print(bcolors.WARNING + "#\nThis is the gwyddion text matrix export of your topopgraphy file"+ bcolors.ENDC) 
print(bcolors.WARNING + "#Export options:" + bcolors.ENDC)
print(bcolors.WARNING + "\t dot decimal seperator " + bcolors.ENDC)
print(bcolors.WARNING + "\t informational comment header" + bcolors.ENDC)
print(bcolors.WARNING + "#Important: Do not trim images"+ bcolors.ENDC)
print(bcolors.WARNING + "Input something like F100101.232323.txt "+ bcolors.ENDC)
if debug:	print ("\n...Loading Topographic information...")

root = tk.Tk()
root.withdraw()
data_name = filedialog.askopenfilename()
ima,imagesize=load_image(data_name)
root.destroy()

#Load data
#dI/dV
print(bcolors.WARNING + "\n#This is the gwyddion text matrix export of your dIdV file"+ bcolors.ENDC) 
print(bcolors.WARNING + "#Export options:" + bcolors.ENDC)
print(bcolors.WARNING + "\t dot decimal seperator " + bcolors.ENDC)
print(bcolors.WARNING + "\t informational comment header" + bcolors.ENDC)
print(bcolors.WARNING + "#Important: Do not trim images"+ bcolors.ENDC)
print(bcolors.WARNING + "Input something like F100101.232323-dIdV.txt "+ bcolors.ENDC)
print(bcolors.WARNING + "Leave empty if no dIdV is present"+ bcolors.ENDC)

root = tk.Tk()
root.withdraw()
didv_name = filedialog.askopenfilename()
root.destroy()

if didv_name == '':				#checking for empty string and dont read dIdV data / configure graphics output woth with_didv flag
	if debug: print("Omitting dIdV data ...")
	with_didv = 0
else:
	if debug:	print ("\n...Loading dI/dV information...")
	didv,didvsize=load_image(didv_name) 
	with_didv = 1

#Load data
#Spectra
print(bcolors.WARNING + "#This are the names of your spectral *.VERT files"+ bcolors.ENDC) 
print(bcolors.WARNING + "Input something like F100101.232323.L*.VERT"+ bcolors.ENDC)
if debug:	print ("\n...Loading Spectral information...")

root = tk.Tk()
root.withdraw()
spectrum_files = filedialog.askopenfilenames()		#creates a tuple with selected spectra files files
root.destroy()

ext=[]
matrixx=[]
matrixy=[]
spec_posi=[]
count=0
for i in spectrum_files:
	x,y,posi=load_spec(i)
	matrixy.append(y)
	matrixx.append(x)
	spec_posi.append(posi)
	if i==spectrum_files[0] or i==spectrum_files[-1]:
		ext.append(posi)
	count=count+1
matrixx=np.array(matrixx,float)
matrixy=np.array(matrixy,float)
if debug:	print ("Read {0} spectra".format(count))
line_length=np.sqrt((ext[0][0]-ext[1][0])**2+(ext[0][1]-ext[1][1])**2)
	
if debug:	print ("Spectral line_length is {0} nm".format(line_length))

#normalize specs
if debug:	print("\n...Normalizing spectra...")	

maxi=[]
globmaxy=0
for n,i in enumerate(matrixy):
	maxi.append(0)
	for m,j in enumerate(i):
		#change matrixx[n][m]>-700 and matrixx[n][m]<0 for range where max is found
		if matrixx[n][m]>-700 and matrixx[n][m]<0 and matrixy[n][m]>maxi[n]:
			maxi[n]=matrixy[n][m]
	if max(i)>globmaxy:
		globmaxy=max(i)

if debug:	print("...Floating average of spectra is calculated...")	
#average specs, floating average for 5pt  so if m%5==4: should be m%(x)==(x-1):     and    [m-(x-1):m])/x
matrixyneu=[]
for n,i in enumerate(matrixy):
	matrixyneu.append([])
	for m,j in enumerate(i):
		if m%5==4:
			matrixyneu[-1].append(sum(matrixy[n][m-4:m])/5)
matrixyneu=np.array(matrixyneu,float)

###################
# Choose contrast range
if debug2:	print(bcolors.WARNING + "\n_Input needed_" + bcolors.ENDC)	

cons=[]
ans='-'
while ans!='o' or ans!='n':
	ans=input(bcolors.WARNING + "Use (o)ld or (n)ew values for contrast? (o/n)"+ bcolors.ENDC)
	if ans=='o':
		cons=np.loadtxt(data_name[:-4]+'.csv',delimiter=',')
		break
	elif ans=='n':
		#find out clim topo
		if debug2: print("... for topography")

		topounten,topooben=contrast(ima,contrast_topo)
		cons.append(topounten)							#Code hangs here
		cons.append(topooben)
		if debug2: print("Done for topography")
		#find out clim didv

		if with_didv:
			didvunten,didvoben=contrast(didv,contrast_didv)
			cons.append(didvunten)
			cons.append(didvoben)
			if debug2: print("Done for dIdV")

		#find out clim specs along line
		specunten,specoben=contrast(matrixyneu.T,contrast_spec)
		cons.append(specunten)
		cons.append(specoben)
		if debug2: print("Done for spectra")


		if debug: print("Saving new contrasts in file {0}".format(data_name[:-4]+'.csv'))
		np.savetxt(data_name[:-4]+'.csv',cons,delimiter=',')
		break
######################### Plot section #########################
## Font setup 
labelfontsize=18
tickfontsize=16

# Total image size 
## plt.figure(figsize=(x,y) determines size of graphic in x,y direction, values given in inches (1"=2.54cm)
plt.figure(figsize=(10,5),dpi=300,tight_layout=True)    # tight_layout=False may be required for tweeking
if with_didv:
	plt.figure(figsize=(15,5),dpi=300,tight_layout=True)    # tight_layout=False may be required for tweeking

# How many subfigures are expected? 
gs = gridspec.GridSpec(1, 2)
if with_didv:
	gs = gridspec.GridSpec(1, 3)

######## Plots topography image
if debug:	print("\n...Plotting topography...")	
plt.subplot(gs[0])
plt.title('Topography',fontsize=labelfontsize)
plt.imshow(ima,cmap=contrast_topo,extent=[0,imagesize[0],0,imagesize[1]],vmin=cons[0],vmax=cons[1])

#### Tick setup
#set size of tick label
plt.tick_params(labelsize=tickfontsize)    
#

## where a tick label is drawn
plt.tick_params(labelbottom='off',labelleft='off',labeltop='off',labelright='off')    
##draw ticks only with direction 'in', 'out' and 'inout' are possible values
plt.tick_params(axis='both',direction='in')
##control if top/right ticks are drawn
#plt.tick_params(top='on',right='on')
####

#disable ticks completely, comment if u want ticks
plt.xticks([])
plt.yticks([])

# plots points of spectra in topography
# ms controlls size of dots for spectral positions, 
# possible shapes: [‘/’ | ‘\’ | ‘|’ | ‘-‘ | ‘+’ | ‘x’ | ‘o’ | ‘O’ | ‘.’ | ‘*’] 
if debug:	print("...Adding circles @ spectra positions...")	
for pos in spec_posi:
	plt.plot(pos[0],pos[1],'o',color='white',ms=3)

#plots scablebar
#"""
################## Double check its size ... something is wrong here ##################
if debug:	print("...Adding scalebar...")	
scalebar = ScaleBar(imagewidth/pixelnumber*10*5) # 1px = [arg] meter
plt.gca().add_artist(scalebar)
#"""
#######################################################################################

"""
################## Alternate way to plot scalebar, doesn't draw anything ...###########
#plots scalebar on starting position, (0,0) is lower left corner
for x in np.linspace(1,6,1000):		#creates an array with 1000 points in the closed interval between [1,6]
	plt.plot(x,5,color='white')
#######################################################################################
"""
###
#if debug:	print("...Adding colorbar...")	
#inserts color bar for topography image
#plt.colorbar()

######## Plots dI/dV image
if with_didv:
	plt.subplot(gs[1])
	plt.title('dI/dV',fontsize=labelfontsize)
	plt.imshow(didv,cmap=contrast_didv,extent=[0,imagesize[0],0,imagesize[1]],vmin=cons[2],vmax=cons[3])

	## draw without ticks, if ticks wanted => comment following two lines
#	plt.xticks(fontsize=tickfontsize)
#	plt.yticks(fontsize=tickfontsize)
	##

	##sets scalebar (0,0) unten links referenz
	#for x in np.linspace(1,6,1000):
	#	plt.plot(x,1,color='white')


######## Plots spectral map
if debug:	print("\n...Plotting line spectra...")	

## set new position of spectral map if no dI/dV is present
## without dI/dV => plt.subplot(gs[1])		with dI/dV => plt.subplot(gs[2])
plt.subplot(gs[1])
if with_didv:
	plt.subplot(gs[2])

plt.title('Line spectra',fontsize=labelfontsize)
# configures line spectra 'map'
plt.imshow(matrixy.T,cmap=contrast_spec,extent=[0,line_length,min(matrixx[0]),max(matrixx[0])],aspect='auto',vmin=cons[2],vmax=cons[3])
if with_didv:
	plt.imshow(matrixy.T,cmap=contrast_spec,extent=[0,line_length,min(matrixx[0]),max(matrixx[0])],aspect='auto',vmin=cons[4],vmax=cons[5])

if debug:	print("...Adding axes...")	
plt.xlabel('Distance x [nm]',fontsize=labelfontsize)
plt.xticks(fontsize=tickfontsize)
plt.ylabel('Bias voltage [mV]',fontsize=labelfontsize)

# use plt.yticks(fontsize=tickfontsize) for automatic values 
# or give fixed values like plt.yticks([-1000,-20,0,20,1000],fontsize=tickfontsize)
plt.yticks(fontsize=tickfontsize)

#inserts color bar for spectral map
#if debug:	print("...Adding colorbar...")	
#plt.colorbar()

# add some free space at corners
if debug:	print("\n...Adding some white space at the top...")	
plt.subplots_adjust(top=0.95,right=1,left=0,bottom=0)

################################################################
#saves figure in pdf file, png, jpg
if debug:	print("\n...Saving image to {0}...".format(data_name[:-4]+'.pdf'))	
plt.savefig(data_name[:-4]+'.pdf')

#display
#if debug:	print("\n...Displaying image...")	
#plt.show()
