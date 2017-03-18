#!/usr/bin/python
#
#
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

# --- CONSTANTS ---
FONTSIZE  = 40
LINESPACE = 55
XMARGIN   = 40
YMARGIN   = 25
T_LINES_Y = [x * LINESPACE for x in range(0, 50)]

img = Image.new('RGB', (1000, 1200), (0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('../../fonts/DooM.ttf', FONTSIZE)

# --- Draw text ---
draw.text((XMARGIN, YMARGIN + T_LINES_Y[0]), 'ENGINE: DOOM 1', (255, 100, 100), font = font)
draw.text((XMARGIN, YMARGIN + T_LINES_Y[2]), 'NUMBER of LEVELS: 32', (255, 100, 100), font = font)

draw.text((XMARGIN, YMARGIN + T_LINES_Y[4]), 'LEVELS:', (255, 100, 100), font = font)
draw.text((XMARGIN, YMARGIN + T_LINES_Y[5]), 'E1M1 E1M2 E1M3 E1M4', (255, 100, 100), font = font)
draw.text((XMARGIN, YMARGIN + T_LINES_Y[6]), 'MAP01 MAP02 MAP03 MAP04', (255, 100, 100), font = font)

for i in range(10, 30):
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[i]), 
              'Sample Text Line {0}'.format(i), 
              (255, 100, 100), font = font)

img.save('sample-out.png')
