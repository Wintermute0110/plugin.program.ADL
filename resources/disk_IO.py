# -*- coding: utf-8 -*-
# Advanced DOOM Launcher filesystem I/O functions
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
import json
import io
import codecs, time
import subprocess
import re
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except:
    PILLOW_AVAILABLE = False

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- ADL packages ---
from utils import *
try:    from utils_kodi import *
except: from utils_kodi_standalone import *

# --- OMG library ---
from omg import *

# -------------------------------------------------------------------------------------------------
# Advanced DOOM Launcher data model
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
IWAD_LIST       = [IWAD_DOOM_1 IWAD_DOOM_2 IWAD_UDOOM]

# --- DOOM engine types ---
ENGINE_VANILLA = 'Vanilla'
ENGINE_NOLIMIT = 'No limit'
ENGINE_BOOM    = 'BOOM'
ENGINE_ZDOOM   = 'ZDOOM'
ENGINE_LIST    = [ENGINE_VANILLA ENGINE_NOLIMIT ENGINE_BOOM ENGINE_ZDOOM]

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
iwad_name_list = {
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

# ASSET_MAME_KEY_LIST  = ['cabinet',  'cpanel',  'flyer',  'marquee',  'PCB',  'snap',  'title',  'clearlogo']
# ASSET_MAME_PATH_LIST = ['cabinets', 'cpanels', 'flyers', 'marquees', 'PCBs', 'snaps', 'titles', 'clearlogos']
def fs_new_IWAD_asset():
    a = {
        'filename' : '',
        'name'     : '',
        'size'     : 0,
    }

    return a

def fs_new_PWAD_asset():
    a = {
        'dir'       : '',
        'filename'  : '',
    }

    return a

# -------------------------------------------------------------------------------------------------
# Exceptions raised by this module
# -------------------------------------------------------------------------------------------------
class DiskError(Exception):
    """Base class for exceptions in this module."""
    pass

class CriticalError(DiskError):
    def __init__(self, msg):
        self.msg = msg

# -------------------------------------------------------------------------------------------------
# Filesystem very low-level utilities
# -------------------------------------------------------------------------------------------------
#
# Writes a XML text tag line, indented 2 spaces (root sub-child)
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def XML_text(tag_name, tag_text):
    tag_text = text_escape_XML(tag_text)
    line     = '  <{0}>{1}</{2}>\n'.format(tag_name, tag_text, tag_name)

    return line

#
# See https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
# This function is not needed. It is deprecated and will be removed soon.
def get_fs_encoding():
    return sys.getfilesystemencoding()

# -------------------------------------------------------------------------------------------------
# JSON write/load
# -------------------------------------------------------------------------------------------------
def fs_load_JSON_file(json_filename):
    # --- If file does not exist return empty dictionary ---
    data_dic = {}
    if not os.path.isfile(json_filename): return data_dic
    log_verb('fs_load_ROMs_JSON() "{0}"'.format(json_filename))
    with open(json_filename) as file:
        data_dic = json.load(file)

    return data_dic

def fs_write_JSON_file(json_filename, json_data):
    log_verb('fs_write_JSON_file() "{0}"'.format(json_filename))
    try:
        with io.open(json_filename, 'wt', encoding='utf-8') as file:
          file.write(unicode(json.dumps(json_data, ensure_ascii = False, sort_keys = True,
                                        indent = 2, separators = (',', ': '))))
    except OSError:
        gui_kodi_notify('Advanced DOOM Launcher', 'Cannot write {0} file (OSError)'.format(roms_json_file))
    except IOError:
        gui_kodi_notify('Advanced DOOM Launcher', 'Cannot write {0} file (IOError)'.format(roms_json_file))

# -------------------------------------------------------------------------------------------------
# IWAD/PWAD scanner
# -------------------------------------------------------------------------------------------------
def fs_scan_iwads(root_file_list):
    log_debug('Starting fs_scan_iwads() ...')
    iwads = []
    for file in root_file_list:
        # >> For now just check size of the IWAD. Later check MD5
        stat_obj = os.stat(file.getPath())
        file_size = stat_obj.st_size
        IWAD_found = False
        for iwad_info in iwad_list:
            if file_size == iwad_info[1]:
                IWAD_found = True
                IWAD_info = iwad_info
                break
        if IWAD_found: 
            log_info('Found IWAD {0}'.format(IWAD_info[0]))
            iwad = fs_new_IWAD_asset()
            iwad['filename'] = file.getPath()
            iwad['name']     = IWAD_info[0]
            iwad['size']     = IWAD_info[1]
            iwads.append(iwad)

    return iwads

def fs_scan_pwads(doom_wad_dir, pwad_file_list, FONT_FILE_PATH):
    log_debug('Starting fs_scan_pwads() ...')
    log_debug('Starting fs_scan_pwads() doom_wad_dir = "{0}"'.format(doom_wad_dir))
    pwads = {}
    for file in pwad_file_list:
        file_str = file.getPath()
        extension = file_str[-3:]
        # >> Check if file is a WAD file
        if extension.lower().endswith('wad'):
            log_debug('>>>>>>>>>> Processing PWAD "{0}"'.format(file.getPath()))

            # >> Get metadata for this PWAD
            inwad = WAD()
            inwad.from_file(file.getPath())
            level_name_list = []
            for i, name in enumerate(inwad.maps): level_name_list.append(name)
            # List is sorted in place
            level_name_list.sort()
            log_debug('Number of levels {0}'.format(inwad.maps._n))

            # >> Create PWAD database dictionary entry
            pwad_dir = file.getDir()
            wad_dir = pwad_dir.replace(doom_wad_dir, '/')
            pwad = fs_new_PWAD_asset()
            pwad['dir']        = wad_dir
            pwad['filename']   = file.getPath()
            pwad['name']       = file.getBase_noext()
            pwad['num_levels'] = inwad.maps._n
            pwad['level_list'] = level_name_list
            pwad['iwad']       = doom_determine_iwad(pwad)
            pwad['engine']     = doom_determine_engine(pwad)
            if inwad.maps._n > 0:
                # >> Create WAD info file. If NFO file exists just update automatic fields.
                nfo_FN = FileName(file.getPath_noext() + '.nfo')
                log_debug('Creating NFO file "{0}"'.format(nfo_FN.getPath()))
                fs_write_PWAD_NFO_file(nfo_FN, pwad)

                # >> Create fanart with the first level
                map_name = level_name_list[0]
                fanart_FN = FileName(file.getPath_noext() + '_' + map_name + '.png')
                log_debug('Creating FANART "{0}"'.format(fanart_FN.getPath()))
                drawmap(inwad, map_name, fanart_FN.getPath(), 'PNG', 1920, 1080)
                pwad['fanart'] = fanart_FN.getPath()

                # >> Create poster with level information
                poster_FN = FileName(file.getPath_noext() + '_poster.png')
                log_debug('Creating POSTER "{0}"'.format(poster_FN.getPath()))
                drawposter(pwad, poster_FN.getPath(), FONT_FILE_PATH)
                pwad['poster'] = poster_FN.getPath()

                # >> Add PWAD to database. Only add the PWAD if it contains level.
                log_debug('Adding PWAD to database')
                pwads[pwad['filename']] = pwad
            else:
                log_debug('Skipping PWAD. Does not have levels')

    return pwads

#
# Generate browser index. Given a directory the list of PWADs in that directory must be get instantly.
# pwad_index_dic = { 
#     'dir_name_1' : {
#         'dirs' : ['dir_1', 'dir_2', ...], 
#         'wads' : ['filename_1', 'filename_2', ...]
#     },
#     ... 
# }
#
def fs_build_pwad_index_dic(doom_wad_dir, pwads):
    log_debug('Starting fs_build_pwad_index_dic() ...')
    directories_set = set()
    pwad_index_dic = {}
    
    # Make a list of all directories
    for pwad_key in pwads:
        log_debug('Directory {0}'.format(pwads[pwad_key]['dir']))
        directories_set.add(pwads[pwad_key]['dir'])

    # Traverse list of directories and fill content
    for dir_name in directories_set:
        # Find PWADs in that directory
        pwad_fn_list = []
        for pwad_key in pwads:
            pwad = pwads[pwad_key]
            wad_dir = pwad['dir']
            if wad_dir == dir_name: pwad_fn_list.append(pwad['filename'])
        pwad_index_dic[dir_name] = { 'dirs' : [], 'wads' : pwad_fn_list }

    # >> Workaround
    pwad_index_dic['/'] = { 'dirs' : list(directories_set), 'wads' : [] }

    return pwad_index_dic

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
#
# Determintes the IWAD required to run this PWAD
# Returns: Doom 1, Doom 2, UDoom, Hexen, ...
#
IWAD_DOOM1_STR = 'Doom 1'
IWAD_DOOM2_STR = 'Doom 2'
def doom_determine_iwad(pwad):
    level_list = pwad['level_list']
    iwad_str = IWAD_DOOM1_STR
    for level_name in level_list:
        if re.match('E[0-9]M[0-9]', level_name):
            iwad_str = IWAD_DOOM1_STR
            break
        elif re.match('MAP[0-9][0-9]', level_name):
            iwad_str = IWAD_DOOM2_STR
            break

    return iwad_str

#
# Determintes the engine required to run this PWAD
# Returns: Vanilla, NoLimits, Boom, ZDoom, ...
#
def doom_determine_engine(pwad):
    return 'Vanilla'

BORDER_PIXELS = 25
def drawmap(wad, name, filename, format, pxsize, pysize):
    log_debug('drawmap() Drawing map "{0}"'.format(filename))
    if not PILLOW_AVAILABLE:
        log_debug('drawmap() Pillow not available. Returning...')
        return

    # Load map in editor
    edit = MapEditor(wad.maps[name])

    # Determine scale = map area unit / pixel
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([-v.y for v in edit.vertexes])
    ymax = max([-v.y for v in edit.vertexes])
    xsize = xmax - xmin
    ysize = ymax - ymin
    scale_x = (pxsize-BORDER_PIXELS*2) / float(xsize)
    scale_y = (pysize-BORDER_PIXELS*2) / float(ysize)
    if scale_x < scale_y:
        scale = scale_x
        xoffset = 0
        yoffset = (pysize - int(ysize*scale)) / 2
    else:
        scale = scale_y
        xoffset = (pxsize - int(xsize*scale)) / 2
        yoffset = 0

    # --- Create image ---
    im = Image.new('RGB', (pxsize, pysize), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    # --- Draw lines ---
    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))
    for line in edit.linedefs:
        # >> Flip coordinates of Y axis
        p1x =  ( edit.vertexes[line.vx_a].x - xmin) * scale + BORDER_PIXELS + xoffset
        p1y =  (-edit.vertexes[line.vx_a].y - ymin) * scale + BORDER_PIXELS + yoffset
        p2x =  ( edit.vertexes[line.vx_b].x - xmin) * scale + BORDER_PIXELS + xoffset
        p2y =  (-edit.vertexes[line.vx_b].y - ymin) * scale + BORDER_PIXELS + yoffset
        color = (0, 0, 0)
        if   line.two_sided: color = (144, 144, 144)
        elif line.action:    color = (220, 130, 50)

        # >> Draw several lines to simulate thickness 
        draw.line((p1x, p1y, p2x, p2y), fill = color)
        draw.line((p1x+1, p1y, p2x+1, p2y), fill = color)
        draw.line((p1x-1, p1y, p2x-1, p2y), fill = color)
        draw.line((p1x, p1y+1, p2x, p2y+1), fill = color)
        draw.line((p1x, p1y-1, p2x, p2y-1), fill = color)

    # --- Draw things ---
    RADIUS = 4
    for thing in edit.things:
        # >> Flip coordinates of Y axis
        p1x =  ( thing.x - xmin) * scale + BORDER_PIXELS + xoffset
        p1y =  (-thing.y - ymin) * scale + BORDER_PIXELS + yoffset
        color = (0, 255, 0)
        draw.ellipse((p1x-RADIUS, p1y-RADIUS, p1x+RADIUS, p1y+RADIUS), outline = color)

    # --- Save image file ---
    del draw
    im.save(filename, format)

def drawposter(pwad, filename, FONT_FILE_PATH):
    log_debug('drawposter() Drawing poster "{0}"'.format(filename))
    if not PILLOW_AVAILABLE:
        log_debug('drawposter() Pillow not available. Returning...')
        return

    # --- CONSTANTS ---
    font_filename = FONT_FILE_PATH.getPath()
    FONTSIZE  = 40
    LINESPACE = 65
    XMARGIN   = 40
    YMARGIN   = 25
    T_LINES_Y = [x * LINESPACE for x in range(0, 50)]

    img = Image.new('RGB', (1000, 1200), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_filename, FONTSIZE)

    # --- Draw text ---
    iwad_str       = 'IWAD: {0}'.format(pwad['iwad'])
    engine_str     = 'ENGINE: {0}'.format(pwad['engine'])
    num_levels_str = 'NUMBER of LEVELS: {0}'.format(pwad['num_levels'])
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[0]), iwad_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[1]), engine_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[2]), num_levels_str, (255, 100, 100), font = font)
    draw.text((XMARGIN, YMARGIN + T_LINES_Y[4]), 'LEVELS:', (255, 100, 100), font = font)
    level_counter = 0
    text_line_counter = 5
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

# -------------------------------------------------------------------------------------------------
# NFO files
# -------------------------------------------------------------------------------------------------
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

def doom_format_NFO_level_names(line_number, pwad):
    level_list = pwad['level_list']
    iwad_str = pwad['iwad']
    line_list = []
    if   iwad_str == IWAD_DOOM1_STR: STR_LIST = DOOM_STR_LIST
    elif iwad_str == IWAD_DOOM2_STR: STR_LIST = DOOM2_STR_LIST
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
#
#
def fs_write_PWAD_NFO_file(nfo_FN, pwad):
    nfo_file_path = nfo_FN.getPath_noext() + '.nfo'
    log_debug('fs_write_PWAD_NFO_file() Exporting "{0}"'.format(nfo_file_path))
    level_str_0 = doom_format_NFO_level_names(0, pwad)
    level_str_1 = doom_format_NFO_level_names(1, pwad)
    level_str_2 = doom_format_NFO_level_names(2, pwad)
    level_str_3 = doom_format_NFO_level_names(3, pwad)

    # >> Always overwrite NFO files (for now ...)
    # log_debug(unicode(pwad))
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<PWAD>\n')
    # nfo_content.append(XML_text('ADL_file', unicode(pwad['iwad'])))
    nfo_content.append(XML_text('ADL_iwad', unicode(pwad['iwad'])))
    nfo_content.append(XML_text('ADL_engine', unicode(pwad['engine'])))
    nfo_content.append(XML_text('ADL_num_levels', unicode(pwad['num_levels'])))
    if level_str_0: nfo_content.append(XML_text('ADL_map', level_str_0))
    if level_str_1: nfo_content.append(XML_text('ADL_map', level_str_1))
    if level_str_2: nfo_content.append(XML_text('ADL_map', level_str_2))
    if level_str_3: nfo_content.append(XML_text('ADL_map', level_str_3))
    nfo_content.append('</PWAD>\n')
    full_string = ''.join(nfo_content).encode('utf-8')
    try:
        usock = open(nfo_file_path, 'w')
        usock.write(full_string)
        usock.close()
    except:
        if verbose:
            kodi_notify_warn('Error writing {0}'.format(nfo_file_path))
        log_error("fs_write_PWAD_NFO_file() Exception writing '{0}'".format(nfo_file_path))

#
#
#
def fs_import_PWAD_NFO(roms, romID, verbose = True):
    ROMFileName = FileName(roms[romID]['filename'])
    nfo_file_path = ROMFileName.getPath_noext() + '.nfo'
    log_debug('fs_import_PWAD_NFO() Loading "{0}"'.format(nfo_file_path))

    # --- Import data ---
    if os.path.isfile(nfo_file_path):
        # >> Read file, put in a string and remove line endings.
        # >> We assume NFO files are UTF-8. Decode data to Unicode.
        # file = open(nfo_file_path, 'rt')
        file = codecs.open(nfo_file_path, 'r', 'utf-8')
        nfo_str = file.read().replace('\r', '').replace('\n', '')
        file.close()

        # Search for items
        item_title     = re.findall('<title>(.*?)</title>', nfo_str)
        item_year      = re.findall('<year>(.*?)</year>', nfo_str)
        item_genre     = re.findall('<genre>(.*?)</genre>', nfo_str)
        item_publisher = re.findall('<publisher>(.*?)</publisher>', nfo_str)
        item_rating    = re.findall('<rating>(.*?)</rating>', nfo_str)
        item_plot      = re.findall('<plot>(.*?)</plot>', nfo_str)

        if len(item_title) > 0:     roms[romID]['m_name']   = text_unescape_XML(item_title[0])
        if len(item_year) > 0:      roms[romID]['m_year']   = text_unescape_XML(item_year[0])
        if len(item_genre) > 0:     roms[romID]['m_genre']  = text_unescape_XML(item_genre[0])
        if len(item_publisher) > 0: roms[romID]['m_studio'] = text_unescape_XML(item_publisher[0])
        if len(item_rating) > 0:    roms[romID]['m_rating'] = text_unescape_XML(item_rating[0])
        if len(item_plot) > 0:      roms[romID]['m_plot']   = text_unescape_XML(item_plot[0])

        if verbose:
            kodi_notify('Imported {0}'.format(nfo_file_path))
    else:
        if verbose:
            kodi_notify_warn('NFO file not found {0}'.format(nfo_file_path))
        log_debug("fs_import_PWAD_NFO() NFO file not found '{0}'".format(nfo_file_path))
        return False

    return True

# -------------------------------------------------------------------------------------------------
# Doom utility functions
# -------------------------------------------------------------------------------------------------
