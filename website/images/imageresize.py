import sys
import os
from PIL import Image

targetdir = sys.argv[1]


size = 415, 311

for x in os.listdir(targetdir):
    img = os.path.join(targetdir, x)
    im = Image.open(img)
    print "Doing %s ...." % img
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(img, "PNG")

