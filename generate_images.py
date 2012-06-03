#!/usr/bin/python

import subprocess
import os,re,sys,shutil

dir_artwork = sys.argv[1]
dir_src = sys.argv[2]

class AndroidImage(object):

	dpis = {
		"xhdpi": 320,
		"hdpi": 240,
		"mdpi": 160,
		"ldpi": 120
	}

	img_sizes = {
		"small": {
			"xhdpi": 48,
			"hdpi": 36,
			"mdpi": 24,
			"ldpi": 18
			},
		"medium": {
			"hdpi": 48,
			"mdpi": 32,
			"ldpi": 24
			},
		"large": {
			"market": 512,
			"xhdpi": 96,
			"hdpi": 72,
			"mdpi": 48,
			"ldpi": 36
			},
		}


	types = {
		"launcher": {"size": "large"},
		"menu": {"size":"small","colorspace":"Gray"},
		"stat_notify": {"size": "small"},
		"tab": {"size": "medium"},
		"dialog": {"size": "medium"},
		"list": {"size": "medium"},
		"image": {"size": None},
		"icon": {"size": "medium"}
	}
	
	def __init__(self,filename):
		self.filename = filename
	
	@property
	def type(self):
		match = re.match("^ic_(([a-zA-Z_]+)_)?",self.name)
	
		if match is None:
			return "image"
		else:
			desc = match.groups()[1]
			if desc == None:
				return "icon"
			else:
				return desc
	
	@property
	def type_dict(self):
		return self.types[self.type]
		
	@property
	def sizes(self):
		type = self.type_dict
		if type.get('size',None) is None:
			return None
		return self.img_sizes.get(type['size'])
	
	@property
	def format(self):
		return os.path.splitext(os.path.basename(self.filename))[1][1:]
	
	@property
	def name(self):
		return os.path.splitext(os.path.basename(self.filename))[0]
	
	def get_path(self, dpi=None):
		if not dpi:
			return "res/drawable"
		if dpi in self.dpis:
			return "res/drawable-%s" % dpi
		else:
			return "res/drawable"
	
	def __ensure_dest(self,dest):
		subprocess.call(["mkdir","-p",os.path.dirname(dest)])
	
	def convert(self, dest, dpi, size):
		self.__ensure_dest(dest)
		if isinstance(dpi,str):
			dpi = self.dpis.get(dpi,90)
		
		if self.format == "svg":
			self._convert_svg(dest,dpi,size)
		elif self.format == "png":
			self._convert_png(dest,dpi,size)
		else:
			print self.format + " is not a recognised image type. Copying to res/drawable"
			shutil.copy(self.filename,os.path.join(os.path.dirname(dest),self.name+"."+self.format))
		
		self._colour_correct(dest)
	
	
	def _convert_svg(self, dest, dpi=None, size=None):
		command = ["inkscape","-e",dest]
		if dpi is not None:
			command.extend(["-d",str(dpi)])
		if size is not None:
			command.extend(["-w",str(size),"-h",str(size)])
		command.append(self.filename)
		subprocess.call(command)
	
	def _convert_png(self,dest, dpi=None, size=None):
		command = ["convert", self.filename]
		if dpi is not None:
			command.extend(["-resample",str(dpi)])
		if size is not None:
			command.extend(["-resize","%dx%d"%(size,size)])
		command.append(dest)
		subprocess.call(command)
	
	def _colour_correct(self,dest):
		command = ["convert", dest]
		for key,value in self.type_dict.items():
			if key in ["size"]:
				continue
			command.extend(["-%s" % (key),str(value)])
		if len(command) == 2:
			return
		command.append(dest)
		subprocess.call(command)
	
	def process(self):
		if self.type not in self.types:
			print "Image type %s not supported." % self.type
			return
		
		sizes = self.sizes
		if sizes is not None:
			for dpi, size in sizes.items():
				self.convert(os.path.join(dir_src,self.get_path(dpi),self.name+".png"),dpi,size)
		else:
			self.convert(os.path.join(dir_src,self.get_path(),self.name+".png"),None,None)


for filename in os.listdir(dir_artwork):
	if os.path.isfile(os.path.join(dir_artwork,filename)):
		AndroidImage(os.path.join(dir_artwork,filename)).process()


