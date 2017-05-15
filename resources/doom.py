# -*- coding: utf-8 -*-
# Advanced DOOM Launcher related functions and interface with OMG library.
#

# Copyright (c) 2017 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
import math
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except:
    PILLOW_AVAILABLE = False

# --- ADL packages ---
from utils import *
try:    from utils_kodi import *
except: from utils_kodi_standalone import *

# --- OMG library ---
from omg import *

# -------------------------------------------------------------------------------------------------
# Definitions and constants
# -------------------------------------------------------------------------------------------------
# --- DOOM IWAD list ---
# This is a list of possible IWADs needed to run a PWAD.
IWAD_DOOM_SW    = 'Doom shareware'
IWAD_DOOM       = 'Doom'
IWAD_DOOM_2     = 'Doom 2'
IWAD_UDOOM      = 'Ultimate Doom'
IWAD_TNT        = 'TNT Evilution'
IWAD_PLUTONIA   = 'TNT Plutonia'
IWAD_DOOM_BFG   = 'Doom BFG'
IWAD_DOOM_2_BFG = 'Doom 2 BFG'
IWAD_FD_1       = 'FreeDOOM Phase 1'
IWAD_FD_2       = 'FreeDOOM Phase 2'
IWAD_UNKNOWN    = 'Unknown'
IWAD_LIST       = [IWAD_DOOM_SW, IWAD_DOOM, IWAD_DOOM_2, IWAD_UDOOM, IWAD_TNT, IWAD_PLUTONIA,
                   IWAD_DOOM_BFG, IWAD_DOOM_2_BFG, IWAD_FD_1, IWAD_FD_2, IWAD_UNKNOWN]

# --- DOOM engine types ---
ENGINE_VANILLA = 'Vanilla'
ENGINE_NOLIMIT = 'No limit'
ENGINE_BOOM    = 'BOOM'
ENGINE_ZDOOM   = 'ZDOOM'
ENGINE_UNKNOWN = 'Unknown'
ENGINE_LIST    = [ENGINE_VANILLA, ENGINE_NOLIMIT, ENGINE_BOOM, ENGINE_ZDOOM, ENGINE_UNKNOWN]

# --- List of IWADs files ---
# >> https://doomwiki.org/wiki/IWAD
# >> https://doomwiki.org/wiki/DOOM.WAD
# >> https://doomwiki.org/wiki/DOOM2.WAD
# >> https://zdoom.org/wiki/IWAD
iwad_info_list = [
    # Shareware Doom
    [IWAD_DOOM_SW,    'Doom shareware (1.0)',             4207819, '90facab21eede7981be10790e3f82da2'],
    [IWAD_DOOM_SW,    'Doom shareware (1.1 Rev A)',       4274218, 'cea4989df52b65f4d481b706234a3dca'],
    [IWAD_DOOM_SW,    'Doom shareware (1.1 Rev B)',       4274218, '52cbc8882f445573ce421fa5453513c1'],
    [IWAD_DOOM_SW,    'Doom shareware (1.2)',             4225504, '30aa5beb9e5ebfbbe1e1765561c08f38'],
    [IWAD_DOOM_SW,    'Doom shareware (1.25)',            4225460, '17aebd6b5f2ed8ce07aa526a32af8d99'],
    [IWAD_DOOM_SW,    'Doom shareware (1.4)',             4261144, 'a21ae40c388cb6f2c3cc1b95589ee693'],
    [IWAD_DOOM_SW,    'Doom shareware (1.5)',             4271324, 'e280233d533dcc28c1acd6ccdc7742d4'],
    [IWAD_DOOM_SW,    'Doom shareware (1.6)',             4211660, '762fd6d4b960d4b759730f01387a50a1'],
    [IWAD_DOOM_SW,    'Doom shareware (1.666)',           4234124, 'c428ea394dc52835f2580d5bfd50d76f'],
    [IWAD_DOOM_SW,    'Doom shareware (1.8)',             4196020, '5f4eb849b1af12887dec04a2a12e5e62'],
    # Doom
    [IWAD_DOOM,       'Doom (1.9)',                      11159840, '1cd63c5ddff1bf8ce844237f580e9cf3'],
    [IWAD_DOOM,       'Doom (1.8)',                      11159840, '11e1cd216801ea2657723abc86ecb01f'],    
    [IWAD_DOOM,       'Doom (1.666)',                    11159840, '54978d12de87f162b9bcc011676cb3c0'],
    [IWAD_DOOM,       'Doom (1.2)',                      10399316, '792fd1fea023d61210857089a7c1e351'],
    [IWAD_DOOM,       'Doom (1.1)',                      10396254, '981b03e6d1dc033301aa3095acc437ce'],
    [IWAD_DOOM,       'Doom (Beta)',                      5468456, '049e32f18d9c9529630366cfc72726ea'],
    [IWAD_DOOM,       'Doom (0.5)',                       3522207, '9c877480b8ef33b7074f1f0c07ed6487'],
    # Doom 2
    [IWAD_DOOM_2,     'Doom 2 (1.9)',                    14604584, '25e1459ca71d321525f84628f45ca8cd'],
    [IWAD_DOOM_2,     'Doom 2 (1.8f)',                   14607420, '3cb02349b3df649c86290907eed64e7b'],
    [IWAD_DOOM_2,     'Doom 2 (1.8)',                    14612688, 'c236745bb01d89bbb866c8fed81b6f8c'],
    [IWAD_DOOM_2,     'Doom 2 (1.7a)',                   14612688, 'd7a07e5d3f4625074312bc299d7ed33f'],
    [IWAD_DOOM_2,     'Doom 2 (1.7)',                    14612688, 'ea74a47a791fdef2e9f2ea8b8a9da13b'],
    [IWAD_DOOM_2,     'Doom 2 (1.666)',                  14943400, '30e3c2d0350b67bfbf47271970b74b2f'],
    [IWAD_DOOM_2,     'Doom 2 (1.666g)',                 14824716, 'd9153ced9fd5b898b36cc5844e35b520'],
    # The Ultimate Doom
    [IWAD_UDOOM,      'The Ultimate Doom (1.9)',         12408292, 'c4fe9fd920207691a9f493668e0a2083'],
    # Final Doom
    [IWAD_TNT,        'TNT: Evilution',                  18195736, '4e158d9953c79ccf97bd0663244cc6b6'],
    [IWAD_TNT,        'TNT: Evilution (Rev A)',          18654796, '1d39e405bf6ee3df69a8d2646c8d5c49'],
    [IWAD_PLUTONIA,   'The Plutonia Experiment',         17420824, '75c8cf89566741fa9d22447604053bd7'],
    [IWAD_PLUTONIA,   'The Plutonia Experiment (Rev A)', 18240172, '3493be7e1e2588bc9c8b31eab2587a04'],
    # BFG Edition
    [IWAD_DOOM_BFG,   'Doom (BFG edition)',              12487824, 'fb35c4a5a9fd49ec29ab6e900572c524'],
    [IWAD_DOOM_2_BFG, 'Doom 2 (BFG edition)',            14691821, 'c3bea40570c23e511a7ed3ebcd9865f7'],
    # FreeDoom
    [IWAD_FD_1,       'FreeDoom: Phase 1',                      0, '0'],
    [IWAD_FD_2,       'FreeDoom: Phase 2',                      0, '0'],
]

# { IWAD_IDENTIFIED : [ 'filename1.wad', 'filename2.wad', ...]
iwad_name_dic = {
    IWAD_DOOM_SW     : ['doom1.wad'],
    IWAD_DOOM        : ['doom.wad'],
    IWAD_DOOM_2      : ['doom2.wad'],
    IWAD_UDOOM       : ['doom.wad', 'doomu.wad'],
    IWAD_TNT         : ['tnt.wad'],
    IWAD_PLUTONIA    : ['plutonia.wad'],
    IWAD_DOOM_BFG    : ['doom.wad', 'doombfg.wad', 'bfgdoom.wad'],
    IWAD_DOOM_2_BFG  : ['doom2.wad', 'doombfg2.wad', 'bfgdoom2.wad'],
    IWAD_FD_1        : ['freedoom1.wad'],
    IWAD_FD_2        : ['freedoom2.wad'],
}

# How to deal with ZDoom custom names? Z1M1, etc.
#
# Doom levels:
#  str_0 = E1Mx
#  str_1 = E2Mx
#  str_2 = E3Mx
#  str_3 = E4Mx
#
# Doom 2 levels
#  str_0 = MAP0X
#  str_1 = MAP1X
#  str_2 = MAP2X
#  str_3 = MAP3X
#
DOOM_STR_LIST = [
    ['E1M1', 'E1M2', 'E1M3', 'E1M4', 'E1M5', 'E1M6', 'E1M7', 'E1M8', 'E1M9'],
    ['E2M1', 'E2M2', 'E2M3', 'E2M4', 'E2M5', 'E2M6', 'E2M7', 'E2M8', 'E2M9'],
    ['E3M1', 'E3M2', 'E3M3', 'E3M4', 'E3M5', 'E3M6', 'E3M7', 'E3M8', 'E3M9'],
    ['E4M1', 'E4M2', 'E4M3', 'E4M4', 'E4M5', 'E4M6', 'E4M7', 'E4M8', 'E4M9']
]

DOOM2_STR_LIST = [
    ['MAP01', 'MAP02', 'MAP03', 'MAP04', 'MAP05', 'MAP06', 'MAP07', 'MAP08', 'MAP09', 'MAP10'],
    ['MAP11', 'MAP12', 'MAP13', 'MAP14', 'MAP15', 'MAP16', 'MAP17', 'MAP18', 'MAP19', 'MAP20'],
    ['MAP21', 'MAP22', 'MAP23', 'MAP24', 'MAP25', 'MAP26', 'MAP27', 'MAP28', 'MAP29', 'MAP30'],
    ['MAP31', 'MAP32']
]

# --- Hard coded constants ---
BORDER_PERCENT = 10

# -------------------------------------------------------------------------------------------------
# Doom utility functions
# -------------------------------------------------------------------------------------------------
def doom_format_NFO_level_names(line_number, pwad):
    level_list = pwad['level_list']
    iwad_str = pwad['iwad']
    line_list = []
    if   iwad_str == IWAD_DOOM: STR_LIST = DOOM_STR_LIST
    elif iwad_str == IWAD_DOOM_2: STR_LIST = DOOM2_STR_LIST
    else:
        return 'Unrecognize IWAD {0}'.format(iwad_str)

    for level in level_list:
        # log_debug('doom_format_NFO_level_names() level {0}'.format(level))
        # log_debug('doom_format_NFO_level_names() DOOM_STR_LIST[line_number] {0}'.format(STR_LIST[line_number]))
        if level in STR_LIST[line_number]:
            line_list.append(level)
    if line_list: line_str = ', '.join(line_list)
    else:         line_str = ''
    
    return line_str

#
# Determintes the IWAD required to run this PWAD
# Returns a string from IWAD_LIST
#
def doom_determine_iwad(pwad):
    level_list = pwad['level_list']
    iwad_str = IWAD_UNKNOWN
    for level_name in level_list:
        if re.match('E[0-9]M[0-9]', level_name):
            iwad_str = IWAD_DOOM
            break
        elif re.match('MAP[0-9][0-9]', level_name):
            iwad_str = IWAD_DOOM_2
            break

    return iwad_str

#
# Determintes the engine required to run this PWAD
# Returns a string from ENGINE_LIST
#
def doom_determine_engine(pwad):
    return ENGINE_VANILLA

# -------------------------------------------------------------------------------------------------
# Drawing functions
# -------------------------------------------------------------------------------------------------
class LinearTransform:
    def __init__(self, left, right, bottom, top, px_size, py_size, border):
        self.left    = left
        self.right   = right
        self.bottom  = bottom
        self.top     = top
        self.x_size  = right - left
        self.y_size  = top - bottom
        # --- Shift map in x or y direction ---
        self.pan_x  = 0
        self.pan_y  = 0

        print('LinearTransform() left       = {0}'.format(left))
        print('LinearTransform() right      = {0}'.format(right))
        print('LinearTransform() bottom     = {0}'.format(bottom))
        print('LinearTransform() top        = {0}'.format(top))
        print('LinearTransform() x_size     = {0}'.format(self.x_size))
        print('LinearTransform() y_size     = {0}'.format(self.y_size))

        # --- Calculate scale in [pixels] / [map_unit] ---
        self.px_size = px_size
        self.py_size = py_size
        self.border  = border
        self.border_x = px_size * border / 100
        self.border_y = py_size * border / 100
        self.pxsize_nob = px_size - 2*self.border_x
        self.pysize_nob = py_size - 2*self.border_y
        self.x_scale = self.pxsize_nob / float(self.x_size)
        self.y_scale = self.pysize_nob / float(self.y_size)
        if self.x_scale < self.y_scale:
            self.scale   = self.x_scale
            self.xoffset = self.border_x
            self.yoffset = (py_size - int(self.y_size*self.scale)) / 2
        else:
            self.scale   = self.y_scale
            self.xoffset = (px_size - int(self.x_size*self.scale)) / 2
            self.yoffset = self.border_y
        print('LinearTransform() px_size    = {0}'.format(px_size))
        print('LinearTransform() py_size    = {0}'.format(py_size))
        print('LinearTransform() border     = {0}'.format(border))
        print('LinearTransform() border_x   = {0}'.format(self.border_x))
        print('LinearTransform() border_y   = {0}'.format(self.border_y))
        print('LinearTransform() pxsize_nob = {0}'.format(self.pxsize_nob))
        print('LinearTransform() pysize_nob = {0}'.format(self.pysize_nob))
        print('LinearTransform() xscale     = {0}'.format(self.x_scale))
        print('LinearTransform() yscale     = {0}'.format(self.y_scale))
        print('LinearTransform() scale      = {0}'.format(self.scale))
        print('LinearTransform() xoffset    = {0}'.format(self.xoffset))
        print('LinearTransform() yoffset    = {0}'.format(self.yoffset))

    def MapToScreen(self, map_x, map_y):
        screen_x = self.scale * (+map_x - self.left) + self.xoffset
        screen_y = self.scale * (-map_y + self.top)  + self.yoffset

        return (int(screen_x), int(screen_y))

    def ScreenToMap(self, screen_x, screen_y):
        map_x = +(screen_x - self.xoffset + self.scale * self.left) / self.scale
        map_y = -(screen_y - self.yoffset - self.scale * self.top) / self.scale

        return (int(map_x), int(map_y))

# See https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c
class ColorScheme:
    def __init__(self, back, wall, tswall, awall, fdwall, cdwall, thing):
        self.BG      = back
        self.WALL    = wall   # One sided linedef
        self.TS_WALL = tswall # Two sided linedef
        self.A_WALL  = awall  # Action wall
        self.FD_WALL = fdwall # Two sided, floor level change
        self.CD_WALL = cdwall # Two sided, ceiling level change and same floor level
        self.THING   = thing  # Thing color

CDoomWorld = ColorScheme(
    (255, 255, 255),
    (0, 0, 0),
    (144, 144, 144),
    (0, 255, 0),
    (0, 0, 255),
    (220, 130, 50),
    (0, 255, 0)
)

CClassic = ColorScheme(
    (0, 0, 0),       # BACK black
    (255, 0, 0),     # WALL red
    (150, 150, 150), # TS_WALL grey
    (255, 255, 255), # A_WALL white
    (139, 92, 55),   # FD_WALL brown
    (255, 255, 0),   # CD_WALL yellow
    (220, 130, 50),  # THING green
)

def draw_line(draw, p1x, p1y, p2x, p2y, color):
    draw.line((p1x, p1y, p2x, p2y), fill = color)

def draw_thick_line(draw, p1x, p1y, p2x, p2y, color):
    draw.line((p1x, p1y, p2x, p2y), fill = color)
    draw.line((p1x+1, p1y, p2x+1, p2y), fill = color)
    draw.line((p1x-1, p1y, p2x-1, p2y), fill = color)
    draw.line((p1x, p1y+1, p2x, p2y+1), fill = color)
    draw.line((p1x, p1y-1, p2x, p2y-1), fill = color)

def draw_axis(draw, LT, color):
    (pxzero, pyzero) = LT.MapToScreen(0, 0)
    draw.line((0, pyzero, LT.px_size, pyzero), fill = color)
    draw.line((pxzero, 0, pxzero, LT.py_size), fill = color)

#
# A level must be contained within a 16384-unit radius as measured from its center point.
# Point A is the top-left corner.
#
# A---------B---------C   A-C gap 327 map units
# |         |         |   A-B gap 163 map units
# |         E         |   A-D gap is 163/2 map units
# D                   F   B-E gap is 163/4 map units
#
def draw_scale(draw, LT, color):
    (A_px, A_py) = LT.MapToScreen(LT.right-256, LT.top)
    (B_px, B_py) = LT.MapToScreen(LT.right-128, LT.top)
    (C_px, C_py) = LT.MapToScreen(LT.right, LT.top)
    (D_px, D_py) = LT.MapToScreen(LT.right-256, LT.top-128/2)
    (E_px, E_py) = LT.MapToScreen(LT.right-128, LT.top-128/4)
    (F_px, F_py) = LT.MapToScreen(LT.right, LT.top-128/2)

    draw.line((A_px, A_py, C_px, C_py), fill = color) # A -> C
    draw.line((A_px, A_py, D_px, D_py), fill = color) # A -> D
    draw.line((B_px, B_py, E_px, E_py), fill = color) # B -> E
    draw.line((C_px, C_py, F_px, F_py), fill = color) # C -> F

#
# Draw a triangle with same size as in Vanilla Doom
# https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c#L186
# https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c#L1314
#
thintriangle_guy = [
    [[-8, -11.2], [16,   0.0]],
    [[16,   0.0], [-8,  11.2]],
    [[-8,  11.2], [-8, -11.2]]
]

def draw_thing(draw, LT, map_x, map_y, angle, color):
    angle_rad = math.radians(angle)
    for line in thintriangle_guy:
        # -- Rotate ---
        rot_a_x = line[0][0] * math.cos(angle_rad) - line[0][1] * math.sin(angle_rad)
        rot_a_y = line[0][0] * math.sin(angle_rad) + line[0][1] * math.cos(angle_rad)
        rot_b_x = line[1][0] * math.cos(angle_rad) - line[1][1] * math.sin(angle_rad)
        rot_b_y = line[1][0] * math.sin(angle_rad) + line[1][1] * math.cos(angle_rad)

        # --- Translate to thing coordinates on map ---
        A_x = rot_a_x + map_x
        A_y = rot_a_y + map_y
        B_x = rot_b_x + map_x
        B_y = rot_b_y + map_y

        # --- Draw line ---
        (A_px, A_py) = LT.MapToScreen(A_x, A_y)
        (B_px, B_py) = LT.MapToScreen(B_x, B_y)
        draw.line((A_px, A_py, B_px, B_py), fill = (0, 255, 0))

#
# Fanarts have resolutions
# A) 1280x720 (720p)
# B) 1920x1080 (1080p or 2K)
# C) 3840x2160 (2160p or 4K)
# D) 7680x4320 (4320p or 8K)
#
def doom_draw_map(wad, name, filename, format, px_size, py_size):
    log_debug('drawmap() Drawing map "{0}"'.format(filename))
    if not PILLOW_AVAILABLE:
        log_debug('drawmap() Pillow not available. Returning...')
        return
    cscheme = CClassic

    # --- Load map in editor ---
    edit = MapEditor(wad.maps[name])

    # --- Determine scale = pixel / map unit ---
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([v.y for v in edit.vertexes])
    ymax = max([v.y for v in edit.vertexes])
    LT = LinearTransform(xmin, xmax, ymin, ymax, px_size, py_size, BORDER_PERCENT)

    # --- Create image ---
    im = Image.new('RGB', (px_size, py_size), cscheme.BG)
    draw = ImageDraw.Draw(im)

    # --- Draw map scale ---
    draw_scale(draw, LT, (256, 256, 256))

    # --- MAP DRAWING CODE BEGINS -----------------------------------------------------------------
    # NOTE Bad/incorrect PWADs may produce this code to crash (Exception IndexError: list index
    #      out of bounds). Caller of this function should check for exceptions.

    # --- sorts lines ---
    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))

    # --- Draw lines ---
    # --- Create floorheight and ceilingheight for two-sided linedefs ---
    for line in edit.linedefs:
        # Skin one-sided linedefs
        if line.back < 0: continue
        front_sidedef = edit.sidedefs[line.front]
        back_sidedef  = edit.sidedefs[line.back]
        front_sector  = edit.sectors[front_sidedef.sector]
        back_sector   = edit.sectors[back_sidedef.sector]
        line.frontsector_floorheight   = front_sector.z_floor
        line.frontsector_ceilingheight = front_sector.z_ceil
        line.backsector_floorheight    = back_sector.z_floor
        line.backsector_ceilingheight  = back_sector.z_ceil

    # >> Use Vanilla Doom automap colours and drawing algortihm
    # >> https://github.com/chocolate-doom/chocolate-doom/blob/sdl2-branch/src/doom/am_map.c#L1146
    for line in edit.linedefs:
        (p1x, p1y) = LT.MapToScreen(edit.vertexes[line.vx_a].x, edit.vertexes[line.vx_a].y)
        (p2x, p2y) = LT.MapToScreen(edit.vertexes[line.vx_b].x, edit.vertexes[line.vx_b].y)

        # >> Use same algorithm as AM_drawWalls(). cheating variable is true
        # >> In vanilla secret walls have same colours as walls.
        if line.back < 0:
            color = cscheme.WALL
        elif line.backsector_floorheight != line.frontsector_floorheight:
            color = cscheme.FD_WALL
        elif line.backsector_ceilingheight != line.frontsector_ceilingheight:
            color = cscheme.CD_WALL
        else:
            color = cscheme.TS_WALL

        # >> Draw several lines to simulate thickness
        # draw_line(draw, p1x, p1y, p2x, p2y, color)
        draw_thick_line(draw, p1x, p1y, p2x, p2y, color)

    # --- Draw things ---
    for thing in edit.things:
        draw_thing(draw, LT, thing.x, thing.y, thing.angle, cscheme.THING)
    # --- MAP DRAWING CODE ENDS -------------------------------------------------------------------

    # --- Save image file ---
    del draw
    im.save(filename, format)

#
# Posters have a size of 1500x1000 pixels (aspect ratio 2:3)
#
def doom_draw_poster(pwad, filename, font_filename):
    log_debug('doom_draw_poster() Drawing poster "{0}"'.format(filename))
    if not PILLOW_AVAILABLE:
        log_debug('doom_draw_poster() Pillow not available. Returning...')
        return

    # --- CONSTANTS ---
    FONTSIZE  = 40
    LINESPACE = 65
    XMARGIN   = 40
    YMARGIN   = 40
    T_LINES_Y = [x * LINESPACE for x in range(0, 50)]

    img = Image.new('RGB', (1000, 1500), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_filename, FONTSIZE)

    # --- Draw text ---
    iwad_str       = 'IWAD: {0}'.format(pwad['iwad'])
    engine_str     = 'ENGINE: {0}'.format(pwad['engine'])
    info_TXT_str   = 'TXT FILE: {0}'.format('YES' if pwad['filename_TXT'] else 'NO')
    num_levels_str = 'NUMBER of LEVELS: {0}'.format(pwad['num_levels'])
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[0]), iwad_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[1]), engine_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[2]), info_TXT_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[3]), num_levels_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[5]), 'LEVELS:', (255, 100, 100), font = font)
    level_counter = 0
    text_line_counter = 6
    LEVELS_PER_LINE = 4
    if len(pwad['level_list']) <= LEVELS_PER_LINE:
        # --- Levels fit in one line ---
        line_list = []
        for level in pwad['level_list']:
            line_list.append(level)
        line_str = ' '.join(line_list)
        draw.text((XMARGIN, YMARGIN + T_LINES_Y[text_line_counter]), line_str, (255, 100, 100), font = font)
    else:
        # --- Several lines required ---
        for level in pwad['level_list']:
            # >> Beginning of line
            if level_counter % LEVELS_PER_LINE == 0:
                line_list = []
                line_list.append(level)
            # >> End of line
            elif level_counter % LEVELS_PER_LINE == (LEVELS_PER_LINE - 1):
                line_list.append(level)
                line_str = ' '.join(line_list)
                draw.text((XMARGIN, YMARGIN + T_LINES_Y[text_line_counter]), line_str, (255, 100, 100), font = font)
                text_line_counter += 1
            else:
                line_list.append(level)
            level_counter += 1

    img.save(filename)

#
# Icons have a size of 512x512 pixels
#
def doom_draw_icon(pwad, filename, font_filename):
    log_debug('doom_draw_icon() Drawing poster "{0}"'.format(filename))
    if not PILLOW_AVAILABLE:
        log_debug('doom_draw_icon() Pillow not available. Returning...')
        return

    # --- CONSTANTS ---
    FONTSIZE  = 20
    LINESPACE = 30
    XMARGIN   = 30
    YMARGIN   = 30
    T_LINES_Y = [x * LINESPACE for x in range(0, 50)]

    img = Image.new('RGB', (512, 512), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_filename, FONTSIZE)

    # --- Draw text ---
    iwad_str       = 'IWAD: {0}'.format(pwad['iwad'])
    engine_str     = 'ENGINE: {0}'.format(pwad['engine'])
    info_TXT_str   = 'TXT FILE: {0}'.format('YES' if pwad['filename_TXT'] else 'NO')
    num_levels_str = 'NUMBER of LEVELS: {0}'.format(pwad['num_levels'])
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[0]), iwad_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[1]), engine_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[2]), info_TXT_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[3]), num_levels_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[5]), 'LEVELS:', (255, 100, 100), font = font)
    level_counter = 0
    text_line_counter = 6
    LEVELS_PER_LINE = 4
    if len(pwad['level_list']) <= LEVELS_PER_LINE:
        # --- Levels fit in one line ---
        line_list = []
        for level in pwad['level_list']:
            line_list.append(level)
        line_str = ' '.join(line_list)
        draw.text((XMARGIN, YMARGIN + T_LINES_Y[text_line_counter]), line_str, (255, 100, 100), font = font)
    else:
        # --- Several lines required ---
        for level in pwad['level_list']:
            # >> Beginning of line
            if level_counter % LEVELS_PER_LINE == 0:
                line_list = []
                line_list.append(level)
            # >> End of line
            elif level_counter % LEVELS_PER_LINE == (LEVELS_PER_LINE - 1):
                line_list.append(level)
                line_str = ' '.join(line_list)
                draw.text((XMARGIN, YMARGIN + T_LINES_Y[text_line_counter]), line_str, (255, 100, 100), font = font)
                text_line_counter += 1
            else:
                line_list.append(level)
            level_counter += 1

    img.save(filename)
