import os
import sys
import re
import pymaging
from pymaging.image import Image
from pymaging.colors import Color
from pymaging import colors
from psd_tools import PSDImage

if len(sys.argv) <= 1 or sys.argv[1].find("help") != -1 or len(sys.argv) < 5:
    print("python atlaser.py <directory> <file name without -#> <layer name> <output path>")
    exit()

# Monkey patch cover_with to not divide by output alpha when it ends up 0...
old_cover_with = Color.cover_with
def working_cover_with(self, cover_color):
    try: return old_cover_with(self, cover_color)
    except ZeroDivisionError: return Color(0, 0, 0, 0)
Color.cover_with = working_cover_with

directory = sys.argv[1]
filename  = sys.argv[2]
layername = sys.argv[3]
outpath   = sys.argv[4]
filecheck = re.compile("^%s-(\d+)\.psd$" % filename)

print("Going for in %s" % directory)

def load_psd(f): return PSDImage.load("%s/%s" % (directory, f))
def filenum(f): return int(filecheck.match(f).group(1))

psdfiles = map(load_psd, sorted(filter(filecheck.match, os.listdir(directory)), key=filenum))

if len(psdfiles) <= 0:
    print("No matching files were found!")
    exit()
else:
    print("Found %i files" % len(psdfiles))

maxwidth  = 2048
maxheight = 2048

curwidth = 0
width    = 0
height   = psdfiles[0].header.height

# NOTE this kind of assumes that the layers are all the same height and width

def matchinglayer(psd):
    candidates = filter((lambda l: l.name == layername), psd.layers)
    if len(candidates) <= 0:
        print("Not all images have a layer called %s" % layername)
        exit()
    elif len(candidates) > 1:
        print("Somehow the layer name %s matches multiple layers in an image!" % layername)
        exit()
    else:
        return candidates[0]

layers = map(matchinglayer, psdfiles)

for psd in psdfiles:
    if curwidth + psd.header.width > maxwidth:
        height += psd.header.height
        curWidth = 0
    else:
        curwidth += psd.header.width
        width += psd.header.width

if height > maxheight:
    print("Resulting atlas is too large! Damn!!! (%ix%i)" % (width, height))
    exit()

print("Resulting atlas will be %ix%i pixels" % (width, height))

atlas = Image.new(colors.RGBA, width, height, Color.from_hexcode("#00000000"))

x = 0
y = 0

for layer in layers:
    atlas.blit(y, x, layer.as_pymaging())

    if x + psd.header.width > width:
        y += psd.header.height
        x = 0
    else:
        x += psd.header.width

atlas.save_to_path(outpath)
print("Saved atlas to %s" % outpath)
