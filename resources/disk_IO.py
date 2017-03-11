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
from PIL import Image, ImageDraw

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
# >> List of IWADs
# >> https://doomwiki.org/wiki/IWAD
# >> See https://doomwiki.org/wiki/DOOM.WAD
iwad_list = [
    # Doom
    ['Doom (v1.9)',                     11159840, '1cd63c5ddff1bf8ce844237f580e9cf3'],
    ['The Ultimate Doom (v1.9)',        12408292, 'c4fe9fd920207691a9f493668e0a2083'],
    ['Doom (BFG edition)',              12487824, 'fb35c4a5a9fd49ec29ab6e900572c524'],
    ['Doom (v1.8)',                     11159840, '11e1cd216801ea2657723abc86ecb01f'],
    # Doom 2
    ['Doom 2 (v1.9)',                   14604584, '25e1459ca71d321525f84628f45ca8cd'],
    ['Doom 2 (BFG edition)',            14691821, 'c3bea40570c23e511a7ed3ebcd9865f7'],
    # TNT
    ['TNT: Evilution',                  18195736, '4e158d9953c79ccf97bd0663244cc6b6'],
    ['TNT: Evilution (Rev A)',          18654796, '1d39e405bf6ee3df69a8d2646c8d5c49'],
    # Plutonia
    ['The Plutonia Experiment',         17420824, '75c8cf89566741fa9d22447604053bd7'],
    ['The Plutonia Experiment (Rev A)', 18240172, '3493be7e1e2588bc9c8b31eab2587a04'],
]

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

def fs_scan_pwads(doom_wad_dir, pwad_file_list):
    log_debug('Starting fs_scan_pwads() ...')
    log_debug('Starting fs_scan_pwads() doom_wad_dir = "{0}"'.format(doom_wad_dir))
    pwads = {}
    for file in pwad_file_list:
        file_str = file.getPath()
        extension = file_str[-3:]
        # >> Check if file is a WAD file
        if extension.lower().endswith('wad'):
            log_debug('Processing PWAD "{0}"'.format(file.getPath()))
            
            # >> Get metadata for this PWAD
            inwad = WAD()
            inwad.from_file(file.getPath())
            level_name_list = []
            for i, name in enumerate(inwad.maps): level_name_list.append(name)
            # List is sorted in place
            level_name_list.sort()
            log_debug('  Number of levels {0}'.format(inwad.maps._n))

            # >> Create PWAD database dictionary entry
            pwad_dir = file.getDir()
            wad_dir = pwad_dir.replace(doom_wad_dir, '/')
            pwad = fs_new_PWAD_asset()
            pwad['dir']        = wad_dir
            pwad['filename']   = file.getPath()
            pwad['num_levels'] = inwad.maps._n
            pwad['level_list'] = level_name_list
            if inwad.maps._n > 0:
                # >> Create WAD info file. If NFO file exists just update automatic fields.
                nfo_FN = FileName(file.getPath_noext() + '.nfo')
                log_debug('  Creating NFO file {0}'.format(nfo_FN.getPath()))
                fs_write_PWAD_NFO_file(nfo_FN, pwad)

                # >> Create fanart with the first level
                map_name = level_name_list[0]
                fanart_FN = FileName(file.getPath_noext() + '_' + map_name + '.png')
                log_debug('  Creating fanart {0}'.format(fanart_FN.getPath()))
                drawmap(inwad, map_name, fanart_FN.getPath(), 1920, 'PNG')
                pwad['fanart'] = fanart_FN.getPath()

                # >> Add PWAD to database. Only add the PWAD if it contains level.
                log_debug('  Adding PWAD to database')
                pwads[pwad['filename']] = pwad
            else:
                log_debug('  Skipping PWAD. Does not have levels')

    return pwads

#
# Generate browser index. Given a directory the list of PWADs in that directory must be get instantly.
# pwad_index_dic = { 'dir_name_1' : ['filename_1', 'filename_2', ...], ... }
#
def fs_build_pwad_index_dic(doom_wad_dir, pwads):
    log_debug('Starting fs_build_pwad_index_dic() ...')
    pwad_index_dic = {}
    
    for pwad_key in pwads:
        pwad = pwads[pwad_key]
        wad_dir = pwad['dir']
        if wad_dir not in pwad_index_dic: pwad_index_dic[wad_dir] = []
        pwad_index_dic[wad_dir].append(pwad['filename'])

    return pwad_index_dic

# -------------------------------------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------------------------------------
border = 25
scales = 0
total = 0

# -------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------
def drawmap(wad, name, filename, width, format):
    global scales, total
    maxpixels = width
    reqscale = 0
    edit = MapEditor(wad.maps[name])
    
   # determine scale = map area unit / pixel
    xmin = min([v.x for v in edit.vertexes])
    xmax = max([v.x for v in edit.vertexes])
    ymin = min([-v.y for v in edit.vertexes])
    ymax = max([-v.y for v in edit.vertexes])
    xsize = xmax - xmin
    ysize = ymax - ymin
    scale = (maxpixels-border*2) / float(max(xsize, ysize))

    # tally for average scale or compare against requested scale
    if reqscale == 0:
        scales = scales + scale
        total = total + 1
    else:
        if scale > 1.0 / reqscale:
            scale = 1.0 / reqscale

    # convert all numbers to image space
    xmax = int(xmax*scale); xmin = int(xmin*scale)
    ymax = int(ymax*scale); ymin = int(ymin*scale)
    xsize = int(xsize*scale) + border*2;
    ysize = int(ysize*scale) + border*2;
    for v in edit.vertexes: 
        v.x =  v.x * scale
        v.y = -v.y * scale 

    # --- Create image ---
    im = Image.new('RGB', (xsize, ysize), (255,255,255))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(lambda a, b: cmp(not a.two_sided, not b.two_sided))

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + border
         p1y = edit.vertexes[line.vx_a].y - ymin + border
         p2x = edit.vertexes[line.vx_b].x - xmin + border
         p2y = edit.vertexes[line.vx_b].y - ymin + border
         color = (0, 0, 0)
         if line.two_sided: color = (144, 144, 144)
         if line.action:    color = (220, 130, 50)

         # draw several lines to simulate thickness 
         draw.line((p1x, p1y, p2x, p2y), fill=color)
         draw.line((p1x+1, p1y, p2x+1, p2y), fill=color)
         draw.line((p1x-1, p1y, p2x-1, p2y), fill=color)
         draw.line((p1x, p1y+1, p2x, p2y+1), fill=color)
         draw.line((p1x, p1y-1, p2x, p2y-1), fill=color)

    # --- Draw scale (or grid or XY axis) ---
    # scale_size = 654 * scale
    # draw.line((10, 10, 10 + scale_size, 10), fill=(255, 255, 0))

    # --- Draw XY axis ---
    # scale_size = 654 * scale
    # draw.line((10, 10, 10 + scale_size, 10), fill=(255, 0, 0))

    # --- Save image file ---
    del draw
    im.save(filename, format)

# -------------------------------------------------------------------------------------------------
# NFO files
# -------------------------------------------------------------------------------------------------
#
#
#
def fs_write_PWAD_NFO_file(nfo_FN, pwad):
    nfo_file_path = nfo_FN.getPath_noext() + '.nfo'
    log_debug('fs_write_PWAD_NFO_file() Exporting "{0}"'.format(nfo_file_path))

    # Always overwrite NFO files.
    nfo_content = []
    nfo_content.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
    nfo_content.append('<PWAD>\n')
    nfo_content.append(XML_text('num_levels', unicode(pwad['num_levels'])))
    nfo_content.append(XML_text('level_list', unicode(pwad['level_list'])))
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
