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

# --- XML stuff ---
# ~~~ cElementTree sometimes fails to parse XML in Kodi's Python interpreter... I don't know why
# import xml.etree.cElementTree as ET

# ~~~ Using ElementTree seems to solve the problem
import xml.etree.ElementTree as ET

# --- ADL packages ---
from utils import *
try:    from utils_kodi import *
except: from utils_kodi_standalone import *
from doom import *

# -------------------------------------------------------------------------------------------------
# Advanced DOOM Launcher data model
# -------------------------------------------------------------------------------------------------
def fs_new_IWAD_object():
    a = {
        'filename' : '',
        'iwad'     : IWAD_UNKNOWN,
        'name'     : '',
        'size'     : 0,
    }

    return a

def fs_new_PWAD_object():
    a = {
        'dir'        : '',
        'engine'     : ENGINE_UNKNOWN,
        'filename'   : '',
        'iwad'       : IWAD_UNKNOWN,
        'level_list' : [],
        'name'       : '',
        'num_levels' : 0,
        's_icon'     : '',
        's_fanart'   : '',
        's_poster'   : '',    
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
        log_debug('Scanning file "{0}"'.format(file.getPath()))

        # >> First try to match the IWAD by file size
        stat_obj = os.stat(file.getPath())
        file_size = stat_obj.st_size
        IWAD_found = False
        for iwad_info in iwad_info_list:
            if file_size == iwad_info[2]:
                log_info('Found IWAD "{0}" by file size matching'.format(iwad_info[1]))
                IWAD_found = True
                break
        if IWAD_found:
            iwad = fs_new_IWAD_object()
            # In database paths separators are always '/'
            iwad['filename'] = file.getPath().replace('\\', '/')
            iwad['iwad']     = iwad_info[0]
            iwad['name']     = iwad_info[1]
            iwad['size']     = iwad_info[2]
            iwads.append(iwad)
            continue
            
        # >> If not found then try to match by filename
        # >> This can produce a lot of wrong matches due to WAD filename alises. However, it should
        # >> work OK for the FreeDoom WADs freedoom1.wad and freedoom2.wad
        IWAD_found = False
        for iwad_type in iwad_name_dic:
            iwad_fn_list = iwad_name_dic[iwad_type]
            for wad_name in iwad_fn_list:
                if wad_name == file.getBase():
                    log_info('Found IWAD "{0}" by file name matching'.format(file.getBase()))
                    IWAD_found = True
                    break
            if IWAD_found: break
        if IWAD_found:
            iwad = fs_new_IWAD_object()
            iwad['filename'] = file.getPath().replace('\\', '/')
            iwad['iwad']     = iwad_type
            if iwad_type == IWAD_FD_1:   iwad['name'] = 'FreeDoom: Phase 1'
            elif iwad_type == IWAD_FD_2: iwad['name'] = 'FreeDoom: Phase 2'
            else:                        iwad['name'] = file.getBase()
            iwad['size']     = file_size
            iwads.append(iwad)
            continue

    return iwads

def fs_scan_pwads(PATHS, pwad_file_list):
    log_debug('Starting fs_scan_pwads() ...')
    log_debug('doom_wad_dir = "{0}"'.format(PATHS.doom_wad_dir.getPath()))
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Advanced DOOM Launcher', 'Scanning PWADs ...')
    num_files = len(pwad_file_list)
    file_count = 0
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
            wad_relative_dir_FN = FileName(pwad_dir.replace(PATHS.doom_wad_dir.getPath(), ''))
            log_debug('Relative dir "{0}"'.format(wad_relative_dir_FN.getPath()))
            # In the database paths are always stored as '/'
            database_filename = file.getPath().replace('\\', '/')
            pwad = fs_new_PWAD_object()
            pwad['dir']        = wad_relative_dir_FN.getPath()
            pwad['filename']   = database_filename
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

                # >> Artwork path
                artwork_path_FN = PATHS.artwork_dir.pjoin(wad_relative_dir_FN.getPath())
                log_debug('artwork_path_FN "{0}"'.format(artwork_path_FN.getPath()))
                if not artwork_path_FN.isdir():
                    log_info('Creating artwork dir "{0}"'.format(artwork_path_FN.getPath()))
                    artwork_path_FN.makedirs()

                # >> Savegame directory.
                # >> Create a diferent directory for each PWAD. NOT SUPPORTED YET.
                

                # >> Create fanart with the first level
                map_name = level_name_list[0]
                fanart_FN = artwork_path_FN.pjoin(file.getBase_noext() + '_' + map_name + '.png')
                log_debug('Creating FANART "{0}"'.format(fanart_FN.getPath()))
                doom_draw_map(inwad, map_name, fanart_FN.getPath(), 'PNG', 1920, 1080)
                pwad['s_fanart'] = fanart_FN.getPath()

                # >> Create poster with level information
                poster_FN = artwork_path_FN.pjoin(file.getBase_noext() + '_poster.png')
                log_debug('Creating POSTER "{0}"'.format(poster_FN.getPath()))
                doom_draw_poster(pwad, poster_FN.getPath(), PATHS.FONT_FILE_PATH.getPath())
                pwad['s_poster'] = poster_FN.getPath()

                # >> Create icon with level information
                poster_FN = artwork_path_FN.pjoin(file.getBase_noext() + '_icon.png')
                log_debug('Creating ICON "{0}"'.format(poster_FN.getPath()))
                doom_draw_icon(pwad, poster_FN.getPath(), PATHS.FONT_FILE_PATH.getPath())
                pwad['s_icon'] = poster_FN.getPath()

                # >> Add PWAD to database. Only add the PWAD if it contains level.
                log_debug('Adding PWAD to database')
                pwads[pwad['filename']] = pwad
            else:
                log_debug('Skipping PWAD. Does not have levels')
        # >> Update progress dialog
        file_count += 1
        pDialog.update(file_count * 100 / num_files)
    pDialog.update(100)
    pDialog.close()

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
# NFO files
# -------------------------------------------------------------------------------------------------
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
