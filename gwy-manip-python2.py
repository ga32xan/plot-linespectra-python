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
import glob, os
from matplotlib import gridspec
import re
#from matplotlib_scalebar.scalebar import ScaleBar
import gwy

dir_path = os.path.dirname(os.path.realpath(__file__))   #gets directory where scripts file is at
cwd = os.getcwd()	#gets current working directory. same as dir_path if not changed in the meantime
# for filename in glob.glob('MARENA-0??C-Maximum.0??'):	#interate over files mathing a given pattern

def load_data(filename, debug = "true"):
	""" loads files into gwyydion container and returns it"""
	if debug:
		print("in load_data with arguments {0}".format(filename))
	mode = gwy.RUN_NONINTERACTIVE
	c=gwy.gwy_file_load(filename,mode)
	return c

def get_pixel_size(datafield):
	""" returns horizontal and vertical pixel width of datafield """
	#container is an gwyddion file container
	xres = datafield.get_xres()
	yres = datafield.get_yres()
	return xres, yres

def get_real_size(datafield):
	""" returns horizontal and vertical real width of datafield """
	#container is an gwyddion file container
	xreal = datafield.get_xreal()
	yreal = datafield.get_yreal()
	return xreal, yreal

def fill_datafield(datafield):
	""" fills datafield with values according to their index in data array"""	
	for idx in range(gwy.get_xres(datafield)*gwy.get_yres(datafield)):
		datafield[idx] = idx

def create_datafield(xres, yres, xreal, yreal):
	""" Create and Return datafield, i.e. Two-dimensional data representation with xrey,res pixel wide with pyhsical dimensions xreal,yreal"""
	d = gwy.DataField(xres, yres, xreal, yreal, 1)		#1 means initializing with 0's
	for i in range(xres):
		for j in range(yres):
			d.set_val(i, j, i) # draws linear gradient

	x,y = get_pixel_size(d)
	print ("Size of created datafield {0} is {1}x{2} pixel".format(d,x,y))
	xr,yr = get_real_size(d)
	print ("Size of created datafield {0} is {1}x{2} meter".format(d,xr,yr))
	return d

#filename=raw_input("which file to load from duccrent directory?")
#adjust some windows for file selection
###################
#filename = "F160627.152758.dat"
#container = gwy.gwy_app_file_load(filename) #automatically identifies a filetype, imports it and adds a container to the databrowser
#gwy.gwy_app_metadata_browser_for_channel(container, 0) #views metadata browser for a given channel(id) of a conatainer(container)
#gwy.gwy_file_save(container, filename[:-3]+"gwy", gwy.RUN_NONINTERACTIVE)	# save container in file
###################

###########################################################
#test=create_datafield(50,50,1e-9,1e-9)
#filename = "F160627.152758.dat"
#container = gwy.gwy_app_file_load(filename) #automatically identifies a filetype, imports it and adds a container to the databrowser
###########################################################
###
#adds datafield to a container and shows it if showit=1. container can be omitted if datafield should be added to current container
#returns id of datafield in container
#gwy_app_data_browser_add_data_field(datafield, container, showit) 
###



#container.set_object_by_name("/0/data", d)		#rename container 
#gwy_app_data_browser_remove() removes container from the data browser
