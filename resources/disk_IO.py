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

# --- OMG library ---
# from omg.wad import *

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
            # inwad = WAD()
            # inwad.from_file(file.getPath())
            # log_debug('Number of levels {0}'.format(inwad.maps._n))

            # >> Create WAD info file

            # >> Add PWAD to database
            pwad_dir = file.getDir()
            wad_dir = pwad_dir.replace(doom_wad_dir, '/')
            pwad = fs_new_PWAD_asset()
            pwad['dir']      = wad_dir
            pwad['filename'] = file.getPath()
            pwads[pwad['filename']] = pwad

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
