#!/usr/bin/python2.7

import subprocess
import os,re,sys,shutil



try:
	action = sys.argv[1]
	dir_artwork = sys.argv[2]
	dir_src = sys.argv[3]
except:
	print "Usage: generate_images <action> <artwork_directory> <android src directory>"
	print "Action may be 'generate' or 'clean' ."
	sys.exit(1)

def clean_drawable_folder(known_filenames,dir_drawable):
	print colour_text("Cleaning %s"%dir_drawable, "GREEN", bold=True)
	files = os.listdir(dir_drawable)
	for filename in files:
		if filename in known_filenames:
			print colour_text("Removing: %s" % filename, "RED")
			os.remove(os.path.join(dir_drawable,filename))
	
	files = os.listdir(dir_drawable)
	if len(files) == 0:
		os.rmdir(dir_drawable)

def clean(dir_artwork,dir_src):
	known_files = []
	for filename in os.listdir(dir_artwork):
		if os.path.isfile(os.path.join(dir_artwork,filename)):
			if filename.endswith(".svg"):
				filename = filename[:-4] + ".png"
			known_files.append(filename)
	
	d = os.path.join(dir_src,"res")
	files = os.listdir(d)
	for filename in files:
		if filename.startswith('drawable') and os.path.isdir(os.path.join(d,filename)):
			clean_drawable_folder(known_files,os.path.join(d,filename))
	
##################### COLOUR OUTPUT

#!/usr/bin/env python
import sys
COLOURS = (
    'BLACK', 'RED', 'GREEN', 'YELLOW',
    'BLUE', 'MAGENTA', 'CYAN', 'WHITE'
)

def colour_text(text, colour_name='WHITE', bold=False):
    if colour_name in COLOURS:
        return '\033[{0};{1}m{2}\033[0m'.format(
            int(bold), COLOURS.index(colour_name) + 30, text)
    sys.stderr.write('ERROR: "{0}" is not a valid colour.\n'.format(colour_name))
    sys.stderr.write('VALID COLOURS: {0}.\n'.format(', '.join(COLOURS)))
    
##################

class AndroidImage(object):

	dpis = {
		"xhdpi": 320,
		"hdpi": 240,
		"mdpi": 160,
		"ldpi": 120
	}

	img_sizes = {
		"bar": {
			"xhdpi": 64,
			"hdpi": 48,
			"mdpi": 32,
			"ldpi": 24
		},
		"small": {
			"xhdpi": 48,
			"hdpi": 36,
			"mdpi": 24,
			"ldpi": 18
			},
		"medium": {
			"xhdpi": 72, # Guessed; not actually part of the spec
			"hdpi": 48,
			"mdpi": 32,
			"ldpi": 24
			},
		"large": {
			#"market": 512,
			"xhdpi": 96,
			"hdpi": 72,
			"mdpi": 48,
			"ldpi": 36
			},
		}


	types = {
		"launcher": {"size": "large"},
		"menu": {"size":"bar","colorspace":"Gray"},
		"stat_notify": {"size": "small"},
		"tab": {"size": "medium"},
		"dialog": {"size": "medium"},
		"list": {"size": "medium"},
		"image": {"size": None},
		"drawable": {"size":None},
		"icon": {"size": "medium"}
	}
	
	def __init__(self,filename):
		self.filename = filename
	
	@property
	def type(self):
		match = re.match("^ic_(([a-zA-Z_]+)_)?",self.name)
		
		if match is None:
			if self.format.lower() in ['jpg','png','svg']:
				return "image"
			else:
				return "drawable"
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
	def preferred_size(self):
		name = os.path.splitext(os.path.basename(self.filename))[0]
		if name.split(".")[-1].isdigit() and not self.filename.endswith(".9.png"):
			return int(name.split(".")[-1])
		return None
	
	@property
	def format(self):
		return os.path.splitext(os.path.basename(self.filename))[1][1:]
	
	@property
	def name(self):
		name = os.path.splitext(os.path.basename(self.filename))[0]
		if name.split(".")[-1].isdigit() and not self.filename.endswith(".9.png"):
			return ".".join(name.split(".")[:-1])
		return name
			
	
	def get_path(self, dpi=None):
		if not dpi:
			#if self.type == "drawable":
			return "res/drawable-mdpi"
			#else:
			#	return "res/drawable-nodpi"
		if dpi in self.dpis:
			return "res/drawable-%s" % dpi
		else:
			return "res/drawable-mdpi"
	
	def __ensure_dest(self,dest):
		subprocess.check_call(["mkdir","-p",os.path.dirname(dest)])
	
	def convert(self, dest, dpi, size):
		self.__ensure_dest(dest)
		if isinstance(dpi,str):
			dpi = self.dpis.get(dpi,90)
		
		if self.format == "svg":
			self._convert_svg(dest,dpi,size)
		elif self.format == "png" and not self.filename.endswith(".9.png"):
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
		subprocess.check_call(command)
		print colour_text("Generated PNG from SVG source: %s" % dest,"RED")
	
	def _convert_png(self,dest, dpi=None, size=None):
		command = ["convert", self.filename]
		if dpi is not None:
			command.extend(["-resample",str(dpi)])
		if size is not None:
			command.extend(["-resize","%dx%d"%(size,size)])
		command.append(dest)
		subprocess.check_call(command)
		print colour_text("Generated PNG from PNG source: %s" % dest,"RED")
	
	def _colour_correct(self,dest):
		command = ["convert", dest]
		for key,value in self.type_dict.items():
			if key in ["size"]:
				continue
			command.extend(["-%s" % (key),str(value)])
		if len(command) == 2:
			return
		command.append(dest)
		subprocess.check_call(command)
		print colour_text("Corrected colours.","RED")
	
	def process(self):
		if self.type not in self.types:
			print "Image type %s not supported." % self.type
			return
		
		sizes = self.sizes
		if sizes is not None:
			for dpi, size in sizes.items():
				self.convert(os.path.join(dir_src,self.get_path(dpi),self.name+".png"),dpi,size)
		else:
			self.convert(os.path.join(dir_src,self.get_path(),self.name+".png"),None,self.preferred_size)
	
	def __repr__(self):
		return colour_text(self.filename,"BLUE",True) + " " + colour_text(self.type,"GREEN",False)

if __name__ == "__main__":
	if action == "clean":
		clean(dir_artwork,dir_src)
		sys.exit(0)
	elif action == "generate":
		for filename in os.listdir(dir_artwork):
			if os.path.isfile(os.path.join(dir_artwork,filename)):
				imageFile = AndroidImage(os.path.join(dir_artwork,filename))
				print imageFile
				imageFile.process()
				print


