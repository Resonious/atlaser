import os
import sys
import re
import pymaging
from pymaging.image import Image
from pymaging.colors import Color
from pymaging import colors
from psd_tools import PSDImage

if len(sys.argv) <= 1 or sys.argv[1].find("help") != -1 or len(sys.argv) < 5:
    print("usage: `python atlaser.py <directory> <layer name> <output path> [--positioning]`")
    exit(1)

# Monkey patch cover_with to not divide by output alpha when it ends up 0...
old_cover_with = Color.cover_with
def working_cover_with(self, cover_color):
    try: return old_cover_with(self, cover_color)
    except ZeroDivisionError: return Color(0, 0, 0, 0)
Color.cover_with = working_cover_with

directory = sys.argv[1]
layername = sys.argv[2]
outpath   = sys.argv[3]
do_positioning = len(sys.argv) >= 5
filecheck = re.compile(r"^(\w+)-(\d+)\.psd$")

print("Going for in %s" % directory)

def load_psd(f): return (f, PSDImage.load("%s/%s" % (directory, f)))

filenames = sorted(filter(filecheck.match, os.listdir(directory)))
psdfiles = list(map(load_psd, filenames))

if len(psdfiles) <= 0:
    print("No matching files were found!")
    exit(1)
else:
    print("Found %i files" % len(psdfiles))

frames = []
unused_image_count = 0
next_index = 0

for filename, psd in psdfiles:
    candidates = list(filter((lambda l: l.name == layername), psd.layers))

    if len(candidates) <= 0:
        unused_image_count += 1
    elif len(candidates) > 1:
        print("Somehow the layer name %s matches multiple layers in %s!" % (layername, filename))
        exit(1)
    else:
        match = filecheck.match(filename)

        framename = match.group(1)
        framenum  = int(match.group(2))
        index     = next_index

        next_index += 1
        frames.append((framename, framenum, index, candidates[0]))

if len(frames) <= 0:
    print("No images in %s had any layers of the name %s!" % (directory, layername))
    exit(1)
if unused_image_count > 0:
    print("%i images lacked a layer called %s and were skipped" % (unused_image_count, layername))

maxwidth  = 2048
maxheight = 2048

curwidth = 0
width    = 0
_f, refpsd = psdfiles[0]
height   = refpsd.header.height

# NOTE this kind of assumes that the layers (and images) are all the same height and width.

for _name, _number, _index, layer in frames:
    if curwidth + refpsd.header.width > maxwidth:
        height += refpsd.header.height
        curWidth = 0
    else:
        curwidth += refpsd.header.width
        width += refpsd.header.width

if height > maxheight:
    print("Resulting atlas is too large! Damn!!! (%ix%i)" % (width, height))
    exit(1)

print("Resulting atlas will be %ix%i pixels" % (width, height))

x = 0
y = 0

if do_positioning:
    offsets = open(outpath, "w")
    offsets.write("[\n")

    for name, number, index, layer in frames:
        # TODO loop through the pixels in layer.
        # First: find #000000FF pixel - offset from center to this guy is your position
        # Second: find #7D7D7DFF pixel - angle between this guy and previous guy is your angle
        layerimg = layer.as_pymaging()
        print(layerimg.pixels.get(0, 3))

        if x + psd.header.width > width:
            y += psd.header.height
            x = 0
        else:
            x += psd.header.width

    offsets.write("];\n")
else:
    atlas = Image.new(colors.RGBA, width, height, Color.from_hexcode("#00000000"))

    metadata_filename = outpath + ".info"
    metadata = open(metadata_filename, "w")
    currentframe = None

    for name, number, index, layer in frames:
        if name != currentframe:
            currentframe = name
            metadata.write("%s frame %i offset = %i\n" % (name, number, index))

        atlas.blit(y + layer.bbox.y1, x + layer.bbox.x1, layer.as_pymaging())

        if x + psd.header.width > width:
            y += psd.header.height
            x = 0
        else:
            x += psd.header.width

    metadata.close()
    atlas.save_to_path(outpath)
    print("Saved atlas to %s" % outpath)
