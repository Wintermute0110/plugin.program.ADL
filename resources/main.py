# -*- coding: utf-8 -*-
#
# Advanced DOOM Launcher main script file
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
import sys, os, shutil, fnmatch, string, time, traceback, pprint
import re, urllib, urllib2, urlparse, socket, exceptions, hashlib
# from collections import OrderedDict

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Addon object (used to access settings) ---
__addon_obj__     = xbmcaddon.Addon()
__addon_id__      = __addon_obj__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon_obj__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon_obj__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon_obj__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon_obj__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon_obj__.getAddonInfo('type').decode('utf-8')

# >> WORKAROUND!
# >> In order for omg to work well "PLUGIN_DIR/resources" must be in the Python path.
# >> Another solution is to put omg module in PLUGIN_DIR which is automatically in the path.
# addon_resources_dir_u = 'special://home/addons/{0}/resources'.format(__addon_id__)
# sys.path.insert(0, xbmc.translatePath(addon_resources_dir_u))

# --- Modules/packages in this plugin ---
from disk_IO import *
from utils import *
from utils_kodi import *

# --- Addon paths and constant definition ---
# _FILE_PATH is a filename
# _DIR is a directory (with trailing /)
ADDONS_DATA_DIR         = FileName('special://profile/addon_data')
PLUGIN_DATA_DIR         = ADDONS_DATA_DIR.pjoin(__addon_id__)
BASE_DIR                = FileName('special://profile')
HOME_DIR                = FileName('special://home')
KODI_FAV_FILE_PATH      = FileName('special://profile/favourites.xml')
ADDONS_DIR              = HOME_DIR.pjoin('addons')
CURRENT_ADDON_DIR       = ADDONS_DIR.pjoin(__addon_id__)

# --- Plugin database indices ---
class Adoon_Paths:
    def __init__(self):
        self.IWADS_FILE_PATH         = PLUGIN_DATA_DIR.pjoin('iwads.json')
        self.PWADS_FILE_PATH         = PLUGIN_DATA_DIR.pjoin('pwads.json')
        self.PWADS_IDX_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('pwads_idx.json')
        self.LAUNCH_LOG_FILE_PATH    = PLUGIN_DATA_DIR.pjoin('launcher.log')
        self.RECENT_PLAYED_FILE_PATH = PLUGIN_DATA_DIR.pjoin('history.json')
        self.MOST_PLAYED_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('most_played.json')
        self.DOOM_OUTPUT_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('doom_output.log')
        self.FONT_FILE_PATH          = CURRENT_ADDON_DIR.pjoin('fonts/DooM.ttf')
# Global variable with all paths
PATHS = Adoon_Paths()

# --- Main code -----------------------------------------------------------------------------------
class Main:
    #
    # This is the plugin entry point.
    #
    def run_plugin(self):
        # --- Initialise log system ---
        # Force DEBUG log level for development.
        # Place it before setting loading so settings can be dumped during debugging.
        # set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using __addon_obj__.getSetting() ---
        self._get_settings()
        set_log_level(self.settings['log_level'])

        # --- Some debug stuff for development ---
        log_debug('---------- Called ADL Main::run_plugin() constructor ----------')
        log_debug('sys.platform {0}'.format(sys.platform))
        log_debug('Python version ' + sys.version.replace('\n', ''))
        log_debug('__addon_id__      {0}'.format(__addon_id__))
        log_debug('__addon_version__ {0}'.format(__addon_version__))
        for i in range(len(sys.argv)): log_debug('sys.argv[{0}] = "{1}"'.format(i, sys.argv[i]))
        # log_debug('sys.path {0}'.format(sys.path))

        # --- Addon data paths creation ---
        if not PLUGIN_DATA_DIR.exists():          PLUGIN_DATA_DIR.makedirs()

        # ~~~~~ Process URL ~~~~~
        self.base_url     = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args              = urlparse.parse_qs(sys.argv[2][1:])
        log_debug('args = {0}'.format(args))
        self.content_type = args['content_type'] if 'content_type' in args else None
        # log_debug('content_type = {0}'.format(self.content_type))

        # --- If no com parameter display addon root directory ---
        if 'command' not in args:
            self._command_render_main_menu()
            log_debug('Advanced DOOM Launcher exit (addon root)')
            return

        # --- Process command ---------------------------------------------------------------------
        command = args['command'][0]
        if command == 'BROWSE_FS':
            self._command_browse_fs(args['dir'][0])
        elif command == 'VIEW':
            if 'iwad' in args:   self._command_view('iwad', args['iwad'][0])
            elif 'pwad' in args: self._command_view('pwad', args['pwad'][0])
            else:                kodi_dialog_OK('Unknown VIEW mode')
        elif command == 'SETUP_PLUGIN':
            self._command_setup_plugin() 
        elif command == 'LAUNCH_IWAD':
            self._run_iwad(args['iwad'][0])
        elif command == 'LAUNCH_PWAD':
            self._run_pwad(args['pwad'][0])

        else:
            kodi_dialog_OK('Unknown command {0}'.format(command))

        log_debug('Advanced DOOM Launcher exit')

    #
    # Get Addon Settings
    #
    def _get_settings(self):
        # >> Modify global PATHS object instance
        global PATHS

        # Get the users preference settings
        self.settings = {}

        # --- Paths ---
        self.settings['chocolate_doom_prog']     = __addon_obj__.getSetting('chocolate_doom_prog').decode('utf-8')
        self.settings['prboom_plus_prog']        = __addon_obj__.getSetting('prboom_plus_prog').decode('utf-8')
        self.settings['zdoom_doom_prog']         = __addon_obj__.getSetting('zdoom_doom_prog').decode('utf-8')

        self.settings['doom_wad_dir']            = __addon_obj__.getSetting('doom_wad_dir').decode('utf-8')
        self.settings['artwork_dir']             = __addon_obj__.getSetting('artwork_dir').decode('utf-8')
        self.settings['savegame_dir']            = __addon_obj__.getSetting('savegame_dir').decode('utf-8')

        # --- Display ---
        self.settings['display_launcher_notify'] = True if __addon_obj__.getSetting('display_launcher_notify') == 'true' else False

        # --- Advanced ---
        self.settings['log_level']               = int(__addon_obj__.getSetting('log_level'))

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        # log_debug('Settings dump END')

        # >> Add addon settings paths to global paths. This is convenient for coding.
        PATHS.chocolate_doom_prog = FileName(self.settings['chocolate_doom_prog'])
        PATHS.prboom_plus_prog    = FileName(self.settings['prboom_plus_prog'])
        PATHS.zdoom_doom_prog     = FileName(self.settings['zdoom_doom_prog'])
        PATHS.doom_wad_dir        = FileName(self.settings['doom_wad_dir'])
        PATHS.artwork_dir         = FileName(self.settings['artwork_dir'])
        PATHS.savegame_dir        = FileName(self.settings['savegame_dir'])

    # ---------------------------------------------------------------------------------------------
    # Root menu rendering
    # ---------------------------------------------------------------------------------------------
    def _command_render_main_menu(self):
        # --- Sorting methods --
        self._set_Kodi_all_sorting_methods()

        # --- Render detected IWADs as standalone launchers ---
        self._render_IWAD_list()

        # --- Filesystem browser ---
        self._render_root_list_row('[Browse filesystem]', self._misc_url_2_arg('command', 'BROWSE_FS', 'dir', '/'))

        # --- Virtual Launchers ---
        # self._render_root_list_row('{Category browser}',    self._misc_url_1_arg('command', 'BROWSE_CATEGORIES'))
        # self._render_root_list_row('{Mega WADs}',           self._misc_url_1_arg('command', 'BROWSE_MEGA_WADS'))
        # self._render_root_list_row('{Episode WADs}',        self._misc_url_1_arg('command', 'BROWSE_EP_WADS'))
        # self._render_root_list_row('{Multiple level WADs}', self._misc_url_1_arg('command', 'BROWSE_ML_WADS'))
        # self._render_root_list_row('{Single level WADs}',   self._misc_url_1_arg('command', 'BROWSE_SL_WADS'))
        # self._render_root_list_row('<Favourite WADs>',      self._misc_url_1_arg('command', 'SHOW_FAVS'))
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _render_root_list_row(self, root_name, root_URL):
        # --- Create listitem row ---
        icon = 'DefaultFolder.png'
        ICON_OVERLAY = 6
        listitem = xbmcgui.ListItem(root_name, iconImage = icon)

        # listitem.setProperty('fanart_image', category_dic['fanart'])
        listitem.setInfo('video', {'title' : root_name, 'overlay' : ICON_OVERLAY } )

        # --- Create context menu ---
        commands = []
        commands.append(('View', self._misc_url_1_arg_RunPlugin('command', 'VIEW'), ))
        commands.append(('Setup plugin', self._misc_url_1_arg_RunPlugin('command', 'SETUP_PLUGIN'), ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = root_URL, listitem = listitem, isFolder = True)

    def _render_IWAD_list(self):
        # >> Open IWAD database
        iwads = fs_load_JSON_file(PATHS.IWADS_FILE_PATH.getPath())

        # >> Traverse and render
        self._set_Kodi_all_sorting_methods()
        for iwad in sorted(iwads):
            self._render_iwad_row(iwad)

    def _command_browse_fs(self, directory):
        log_debug('_command_browse_fs() directory "{0}"'.format(directory))

        # >> Open PWAD database and index
        pwads = fs_load_JSON_file(PATHS.PWADS_FILE_PATH.getPath())
        pwad_index_dic = fs_load_JSON_file(PATHS.PWADS_IDX_FILE_PATH.getPath())

        # >> Get dirs and wads
        dirs = pwad_index_dic[directory]['dirs']
        wads = pwad_index_dic[directory]['wads']
        
        # >> Traverse and render directories first
        self._set_Kodi_all_sorting_methods()
        for dir_name in dirs:
            self._render_directory_row(dir_name)

        # >> Traverse and render PWADs beloging to this directory
        for pwad_filename in wads:
            pwad = pwads[pwad_filename]
            self._render_pwad_row(pwad)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _render_iwad_row(self, wad):
        # --- Create listitem row ---
        title_str = wad['name']
        icon_path = 'DefaultProgram.png'
        fanart_path = wad['fanart'] if 'fanart' in wad else ''

        ICON_OVERLAY = 6
        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str, 'overlay' : ICON_OVERLAY})
        if fanart_path: listitem.setArt({'icon' : icon_path, 'fanart' : fanart_path})

        # --- Create context menu ---
        commands = []
        URL_view = self._misc_url_2_arg_RunPlugin('command', 'VIEW', 'iwad', wad['filename'])
        commands.append(('View', URL_view ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)' ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__) ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        URL = self._misc_url_2_arg('command', 'LAUNCH_IWAD', 'iwad', wad['filename'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = URL, listitem = listitem, isFolder = False)

    def _render_pwad_row(self, wad):
        # --- Create listitem row ---
        title_str = wad['name']
        icon_path = wad['s_icon'] if wad['s_icon'] else 'DefaultProgram.png'
        poster_path = wad['s_poster']
        fanart_path = wad['s_fanart']
        # log_debug('icon_path {0}'.format(icon_path))
        # log_debug('poster_path {0}'.format(poster_path))
        # log_debug('fanart_path {0}'.format(fanart_path))

        ICON_OVERLAY = 6
        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str, 'overlay' : ICON_OVERLAY})
        listitem.setArt({'icon' : icon_path, 'poster' : poster_path, 'fanart' : fanart_path})

        # --- Create context menu ---
        commands = []
        URL_view = self._misc_url_2_arg_RunPlugin('command', 'VIEW', 'pwad', wad['filename'])
        commands.append(('View', URL_view ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)' ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__) ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        URL = self._misc_url_2_arg('command', 'LAUNCH_PWAD', 'pwad', wad['filename'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = URL, listitem = listitem, isFolder = False)

    def _render_directory_row(self, directory):
        icon = 'DefaultFolder.png'
        title_str = directory[1:] if directory[0] == '/' else directory

        ICON_OVERLAY = 6
        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str, 'overlay' : ICON_OVERLAY})
        listitem.setArt({'icon' : icon})

        # --- Create context menu ---
        commands = []
        URL_view = self._misc_url_1_arg_RunPlugin('command', 'VIEW')
        commands.append(('View', URL_view ))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)' ))
        commands.append(('Add-on Settings', 'Addon.OpenSettings({0})'.format(__addon_id__) ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        URL = self._misc_url_2_arg('command', 'BROWSE_FS', 'dir', directory)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = URL, listitem = listitem, isFolder = True)

    # ---------------------------------------------------------------------------------------------
    # Information display
    # ---------------------------------------------------------------------------------------------
    def _command_view(self, wad_name, wad_filename):
        log_debug('_command_view() wad_name {0}'.format(wad_name))
        log_debug('_command_view() wad_filename "{0}"'.format(wad_filename))

        # >> Build menu base on view_type
        if DOOM_OUTPUT_FILE_PATH.exists():
            stat_stdout = DOOM_OUTPUT_FILE_PATH.stat()
            size_stdout = stat_stdout.st_size
            STD_status = '{0} bytes'.format(size_stdout)
        else:
            STD_status = 'not found'
        if wad_name == 'iwad':
            d_list = ['View IWAD database entry',
                      'View last execution output ({0})'.format(STD_status)]

        elif wad_name == 'pwad':
            d_list = ['View PWAD database entry',
                      'View last execution output ({0})'.format(STD_status),
                      'View WAD TXT file']

        dialog = xbmcgui.Dialog()
        selected_value = dialog.select('View', d_list)
        if selected_value < 0: return

        if selected_value == 0:
            if wad_name == 'iwad':
                window_title = 'IWAD database data'
                info_text  = '[COLOR orange]IWAD information[/COLOR]\n'
                info_text += self._misc_print_string_IWAD(wad_filename)
            elif wad_name == 'pwad':
                window_title = 'PWAD database data'
                info_text  = '[COLOR orange]PWAD information[/COLOR]\n'
                info_text += self._misc_print_string_PWAD(wad_filename)

            # --- Show information window ---
            # textviewer WINDOW_DIALOG_TEXT_VIEWER 10147 DialogTextViewer.xml
            try:
                xbmc.executebuiltin('ActivateWindow(textviewer)')
                window = xbmcgui.Window(10147)
                window.setProperty('FontWidth', 'monospaced')
                xbmc.sleep(100)
                window.getControl(1).setLabel(window_title)
                window.getControl(5).setText(info_text)
            except:
                log_error('_command_view() Exception rendering INFO window')

        # --- View last execution output ---
        # NOTE NOT available on Windows. See comments in _run_process()
        elif selected_value == 1:
            # --- Ckeck for errors and read file ---
            if sys.platform == 'win32':
                kodi_dialog_OK('This feature is not available on Windows.')
                return
            if not DOOM_OUTPUT_FILE_PATH.exists():
                kodi_dialog_OK('Log file not found. Try to run the emulator/application.')
                return
            info_text = ''
            with open(DOOM_OUTPUT_FILE_PATH.getPath(), 'r') as myfile:
                info_text = myfile.read()

            # --- Show information window ---
            window_title = 'DOOM last execution stdout'
            try:
                xbmc.executebuiltin('ActivateWindow(textviewer)')
                window = xbmcgui.Window(10147)
                xbmc.sleep(100)
                window.getControl(1).setLabel(window_title)
                window.getControl(5).setText(info_text)
            except:
                log_error('_command_view() Exception rendering INFO window')

        # --- View PWAD TXT info file ---
        elif selected_value == 2:
            kodi_dialog_OK('View of PWAD TXT not coded yet. Sorry.')

    def _misc_print_string_IWAD(self, wad_filename):
        iwads = fs_load_JSON_file(IWADS_FILE_PATH.getPath())
    
    def _misc_print_string_PWAD(self, wad_filename):
        # >> Windows workaround
        if sys.platform == 'win32': wad_filename = wad_filename.replace('/', '\\')
        pwads = fs_load_JSON_file(PWADS_FILE_PATH.getPath())
        pwad = pwads[wad_filename]

        info_text  = ''
        info_text += "[COLOR violet]dir[/COLOR]: '{0}'\n".format(pwad['dir'])
        info_text += "[COLOR violet]engine[/COLOR]: '{0}'\n".format(pwad['engine'])
        info_text += "[COLOR violet]fanart[/COLOR]: '{0}'\n".format(pwad['fanart'])
        info_text += "[COLOR violet]filename[/COLOR]: '{0}'\n".format(pwad['filename'])
        info_text += "[COLOR violet]iwad[/COLOR]: '{0}'\n".format(pwad['iwad'])
        info_text += "[COLOR skyblue]level_list[/COLOR]: '{0}'\n".format(pwad['level_list'])
        info_text += "[COLOR violet]name[/COLOR]: '{0}'\n".format(pwad['name'])
        info_text += "[COLOR violet]num_levels[/COLOR]: '{0}'\n".format(pwad['num_levels'])
        info_text += "[COLOR violet]poster[/COLOR]: '{0}'\n".format(pwad['poster'])

        return info_text

    # ---------------------------------------------------------------------------------------------
    # Setup plugin databases
    # ---------------------------------------------------------------------------------------------
    def _command_setup_plugin(self):
        dialog = xbmcgui.Dialog()
        menu_item = dialog.select('Setup plugin',
                                 ['Scan WAD directory', 'Remove dead PWADs'])
        if menu_item < 0: return

        # --- WAD directory scanner ---
        # >> Scans for IWADs and PWADs, builds databases, creates icons/posters/fanarts
        if menu_item == 0:
            log_info('_command_setup_plugin() Scanning WAD directory ...')

            # >> Check if WAD and artwork directory is set. Abort if not
            if not PATHS.doom_wad_dir.path:
                kodi_dialog_OK('WAD directory not configured. Open the addon settings and set it.')
                return
            if not PATHS.doom_wad_dir.isdir():
                kodi_dialog_OK('WAD directory not found. Open the addon settings and set a valid directory.')
                return
            if not PATHS.artwork_dir.path:
                kodi_dialog_OK('Artwork directory not configured. Open the addon settings and set it.')
                return
            if not PATHS.artwork_dir.isdir():
                kodi_dialog_OK('Artwork directory not configured. Open the addon settings and set a valid directory.')
                return
            log_info('_command_setup_plugin() doom_wad_dir "{0}"'.format(PATHS.doom_wad_dir.getPath()))
            log_info('_command_setup_plugin() artwork_dir  "{0}"'.format(PATHS.artwork_dir.getPath()))

            # >> Progress dialog
            pDialog = xbmcgui.DialogProgress()
            pDialog_canceled = False
            pDialog.create('Advanced DOOM Launcher', 'Scanning files in WAD directory ...')

            # >> Scan and get list of files
            root_file_list = []
            pwad_file_list = []
            for root, directories, filenames in os.walk(PATHS.doom_wad_dir.getPath()):
                # >> This produces one iteration for each directory found (including the root directory)
                # >> See http://www.saltycrane.com/blog/2007/03/python-oswalk-example/
                log_debug('_command_setup_plugin() Dir "{0}"'.format(root))
                # for directory in directories:
                #     log_debug('Dir  "{0}"'.format(os.path.join(root, directory)))

                # >> If root directory scan for IWADs only
                if root == PATHS.doom_wad_dir.getPath():
                    log_info('_command_setup_plugin() Adding files to IWAD scanner ...')
                    for filename in filenames: 
                        log_debug('File "{0}"'.format(os.path.join(root, filename)))
                        root_file_list.append(FileName(os.path.join(root, filename)))

                # >> If not scan for PWADs
                else:
                    log_info('_command_setup_plugin() Adding files to PWAD scanner ...')
                    for filename in filenames: 
                        log_debug('File "{0}"'.format(os.path.join(root, filename)))
                        pwad_file_list.append(FileName(os.path.join(root, filename)))
            pDialog.update(100)
            pDialog.close()

            # >> Now scan for actual IWADs/PWADs
            iwads = fs_scan_iwads(root_file_list)
            pwads = fs_scan_pwads(PATHS, pwad_file_list)
            pwad_index_dic = fs_build_pwad_index_dic(PATHS, pwads)

            # >> Save databases
            kodi_busydialog_ON()
            fs_write_JSON_file(PATHS.IWADS_FILE_PATH.getPath(), iwads)
            fs_write_JSON_file(PATHS.PWADS_FILE_PATH.getPath(), pwads)
            fs_write_JSON_file(PATHS.PWADS_IDX_FILE_PATH.getPath(), pwad_index_dic)
            kodi_busydialog_OFF()

            # >> Refresh container
            kodi_refresh_container()

        # >> Removes dead WADs and associated assets (to save disk space).
        elif menu_item == 1:
            log_info('_command_setup_plugin() Removing dead PWADs ...')

            # >> Open PWAD database and index
            pwads_old = fs_load_JSON_file(PATHS.PWADS_FILE_PATH.getPath())

            # >> Progress dialog
            pDialog = xbmcgui.DialogProgress()
            pDialog_canceled = False
            pDialog.create('Advanced DOOM Launcher', 'Removing dead PWADs ...')
            num_items = len(pwads_old)
            item_count = 0

            # >> Traverse PWAD dictionary and check if file exist
            #    To avoid issues changing the dictionary while iterating it make a new one.
            pwads_new = {}
            for key, pwad in pwads_old.iteritems():
                pwad_FN = FileName(key)
                if pwad_FN.exists():
                    log_debug('Keep PWAD {0}'.format(key))
                    pwads_new[key] = pwad
                else:
                    log_debug('Dele PWAD {0}'.format(key))
                item_count += 1
                pDialog.update(item_count * 100 / num_items)
            pDialog.update(100)
            pDialog.close()

            # >> Regenerate PWAD index and save databases
            pwad_index_dic = fs_build_pwad_index_dic(PATHS, pwads_new)
            kodi_busydialog_ON()
            fs_write_JSON_file(PATHS.PWADS_FILE_PATH.getPath(), pwads_new)
            fs_write_JSON_file(PATHS.PWADS_IDX_FILE_PATH.getPath(), pwad_index_dic)
            kodi_busydialog_OFF()

    #
    # Choose DOOM executable for an IWAD
    #
    def _misc_get_doom_executable(self):
        doom_exe_FN_list = []
        doom_exe_name_list = []
        if PATHS.chocolate_doom_prog.isfile():
            doom_exe_FN_list.append(PATHS.chocolate_doom_prog)
            doom_exe_name_list.append(PATHS.chocolate_doom_prog.getBase_noext().capitalize())
        if PATHS.prboom_plus_prog.isfile():
            doom_exe_FN_list.append(PATHS.prboom_plus_prog)
            doom_exe_name_list.append(PATHS.prboom_plus_prog.getBase_noext().capitalize())
        if PATHS.zdoom_doom_prog.isfile():
            doom_exe_FN_list.append(PATHS.zdoom_doom_prog)
            doom_exe_name_list.append(PATHS.zdoom_doom_prog.getBase_noext().capitalize())

        # >> If not executables warn user and abort
        if len(doom_exe_name_list) < 1:
            return None
        # >> If only one exectuable there is nothing to choose
        elif len(doom_exe_name_list) == 1:
            log_info('_run_iwad() Only 1 DOOM executable configured.')
            doom_prog_FN = doom_exe_FN_list[0]
        else:
            dialog = xbmcgui.Dialog()
            menu_item = dialog.select('Choose DOOM executable', doom_exe_name_list)
            if menu_item < 0: return
            log_info('_run_iwad() User choos DOOM exe index {0}'.format(menu_item))
            doom_prog_FN = doom_exe_FN_list[menu_item]

        return doom_prog_FN

    #
    # Choose DOOM executable for an IWAD
    #
    def _misc_get_iwad_to_launch_pwad(self, iwads, pwad):
        # >> Pick first IWAD that matches game type
        for iwad in iwads:
            if iwad['iwad'] == pwad['iwad']:
                IWAD_FN = FileName(iwad['filename'])
                log_debug('_misc_get_iwad_to_launch_pwad() IWAD "{0}"'.format(IWAD_FN.getPath()))

                return IWAD_FN

        return None

    # ---------------------------------------------------------------------------------------------
    # Launch IWAD
    # ---------------------------------------------------------------------------------------------
    def _run_iwad(self, filename):
        log_info('_run_iwad() IWAD "{0}"'.format(filename))

        # >> Check if ROM exist
        IWAD_FN = FileName(filename)
        if not IWAD_FN.exists():
            kodi_dialog_OK('IWAD does not exist.')
            return

        # --- If user configured multiple DOOM executables show a list ---
        doom_prog_FN = self._misc_get_doom_executable()
        if doom_prog_FN == None:
            log_info('_run_iwad() No DOOM executables configured. Aboting.')
            kodi_dialog_OK('No DOOM exectuable configured. Aborting.')
            return

        # >> Launch machine using subprocess module
        (doom_dir, doom_exec) = os.path.split(doom_prog_FN.getPath())
        log_info('_run_iwad() doom_prog_FN "{0}"'.format(doom_prog_FN.getPath()))    
        log_info('_run_iwad() doom_dir     "{0}"'.format(doom_dir))
        log_info('_run_iwad() doom_exec    "{0}"'.format(doom_exec))
        log_info('_run_iwad() IWAD_FN      "{0}"'.format(IWAD_FN.getPath()))

        # >> Argument list
        arg_list = [doom_prog_FN.getPath(), '-iwad', IWAD_FN.getPath()]
        log_info('_run_iwad() arg_list {0}'.format(arg_list))

        self._run_process(arg_list, doom_dir)

    # ---------------------------------------------------------------------------------------------
    # Launch PWAD
    # ---------------------------------------------------------------------------------------------
    def _run_pwad(self, pwad_filename):
        log_info('_run_pwad() Launching PWAD "{0}"'.format(pwad_filename))

        # >> Check if ROM exist
        PWAD_FN = FileName(pwad_filename)
        if not PWAD_FN.exists():
            kodi_dialog_OK('PWAD does not exist.')
            return

        # --- Get PWAD database entry ---
        iwads = fs_load_JSON_file(PATHS.IWADS_FILE_PATH.getPath())
        pwads = fs_load_JSON_file(PATHS.PWADS_FILE_PATH.getPath())
        pwad_filename = pwad_filename.replace('\\', '/')
        pwad = pwads[pwad_filename]

        # --- Choose DOOM executable based on required engine or return None ---
        doom_prog_FN = self._misc_get_doom_executable()
        if doom_prog_FN == None:
            log_info('_run_pwad() No DOOM executables configured. Aboting.')
            kodi_dialog_OK('No DOOM exectuable configured. Aborting.')
            return

        # --- Choose DOOM IWAD based on game type or return None ---
        IWAD_FN = self._misc_get_iwad_to_launch_pwad(iwads, pwad)
        if IWAD_FN == None:
            log_info('_run_pwad() No DOOM IWAD found. Aborting.')
            kodi_dialog_OK('No suitable DOOM IWAD found to launch this PWAD '
                           '({0} IWAD).'.format(pwad['iwad']))
            return

        # >> Launch machine using subprocess module
        (doom_dir, doom_exec) = os.path.split(doom_prog_FN.getPath())
        log_info('_run_pwad() doom_prog_FN "{0}"'.format(doom_prog_FN.getPath()))    
        log_info('_run_pwad() doom_dir     "{0}"'.format(doom_dir))
        log_info('_run_pwad() doom_exec    "{0}"'.format(doom_exec))
        log_info('_run_pwad() PWAD_FN      "{0}"'.format(PWAD_FN.getPath()))

        # >> Argument list
        arg_list = [doom_prog_FN.getPath(), '-iwad', IWAD_FN.getPath(), '-file', PWAD_FN.getPath()]
        log_info('_run_pwad() arg_list {0}'.format(arg_list))

        self._run_process(arg_list, doom_dir)

    def _run_process(self, arg_list, exec_dir):
        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(arg_list[0]))

        # >> Prevent a console window to be shown in Windows. Not working yet!
        if sys.platform == 'win32':
            log_info('_run_process() Platform is win32. Creating _info structure')
            _info = subprocess.STARTUPINFO()
            _info.dwFlags = subprocess.STARTF_USESHOWWINDOW
            # See https://msdn.microsoft.com/en-us/library/ms633548(v=vs.85).aspx
            # See https://docs.python.org/2/library/subprocess.html#subprocess.STARTUPINFO
            # >> SW_HIDE = 0
            # >> Does not work: MAME console window is not shown, graphical window not shonw either,
            # >> process run in background.
            # _info.wShowWindow = subprocess.SW_HIDE
            # >> SW_SHOWMINIMIZED = 2
            # >> Both MAME console and graphical window minimized.
            # _info.wShowWindow = 2
            # >> SW_SHOWNORMAL = 1
            # >> MAME console window is shown, MAME graphical window on top, Kodi on bottom.
            _info.wShowWindow = 1
        else:
            log_info('_run_process() _info is None')
            _info = None

        # --- Launch DOOM process ---
        log_info('_run_process() Calling subprocess.Popen()...')
        with open(PATHS.DOOM_OUTPUT_FILE_PATH.getPath(), 'wb') as f:
            p = subprocess.Popen(arg_list, cwd = exec_dir, startupinfo = _info, stdout = f, stderr = subprocess.STDOUT)
        p.wait()
        log_info('_run_process() Exiting function')

    # ---------------------------------------------------------------------------------------------
    # Misc functions
    # ---------------------------------------------------------------------------------------------
    # List of sorting methods here http://mirrors.xbmc.org/docs/python-docs/16.x-jarvis/xbmcplugin.html#-setSetting
    def _set_Kodi_all_sorting_methods(self):
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

    def _set_Kodi_all_sorting_methods_and_size(self):
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_SIZE)
        xbmcplugin.addSortMethod(handle=self.addon_handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)

    # ---------------------------------------------------------------------------------------------
    # Misc URL building functions
    # ---------------------------------------------------------------------------------------------
    #
    # Used in xbmcplugin.addDirectoryItem()
    #
    def _misc_url_1_arg(self, arg_name, arg_value):
        arg_value_escaped = arg_value.replace('&', '%26')

        return '{0}?{1}={2}'.format(self.base_url, arg_name, arg_value_escaped)

    def _misc_url_2_arg(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2):
        # >> Escape '&' in URLs
        arg_value_1_escaped = arg_value_1.replace('&', '%26')
        arg_value_2_escaped = arg_value_2.replace('&', '%26')

        return '{0}?{1}={2}&{3}={4}'.format(self.base_url, 
                                            arg_name_1, arg_value_1_escaped,
                                            arg_name_2, arg_value_2_escaped)

    def _misc_url_3_arg(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                              arg_name_3, arg_value_3):
        arg_value_1_escaped = arg_value_1.replace('&', '%26')
        arg_value_2_escaped = arg_value_2.replace('&', '%26')
        arg_value_3_escaped = arg_value_3.replace('&', '%26')

        return '{0}?{1}={2}&{3}={4}&{5}={6}'.format(self.base_url,
                                                    arg_name_1, arg_value_1_escaped,
                                                    arg_name_2, arg_value_2_escaped,
                                                    arg_name_3, arg_value_3_escaped)

    def _misc_url_4_arg(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                              arg_name_3, arg_value_3, arg_name_4, arg_value_4):
        arg_value_1_escaped = arg_value_1.replace('&', '%26')
        arg_value_2_escaped = arg_value_2.replace('&', '%26')
        arg_value_3_escaped = arg_value_3.replace('&', '%26')
        arg_value_4_escaped = arg_value_4.replace('&', '%26')

        return '{0}?{1}={2}&{3}={4}&{5}={6}&{7}={8}'.format(self.base_url,
                                                            arg_name_1, arg_value_1_escaped,
                                                            arg_name_2, arg_value_2_escaped,
                                                            arg_name_3, arg_value_3_escaped,
                                                            arg_name_4, arg_value_4_escaped)

    #
    # Used in context menus
    #
    def _misc_url_1_arg_RunPlugin(self, arg_name_1, arg_value_1):
        return 'XBMC.RunPlugin({0}?{1}={2})'.format(self.base_url, 
                                                    arg_name_1, arg_value_1)

    def _misc_url_2_arg_RunPlugin(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2):
        return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4})'.format(self.base_url,
                                                            arg_name_1, arg_value_1,
                                                            arg_name_2, arg_value_2)

    def _misc_url_3_arg_RunPlugin(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                                  arg_name_3, arg_value_3):
        return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6})'.format(self.base_url,
                                                                    arg_name_1, arg_value_1,
                                                                    arg_name_2, arg_value_2,
                                                                    arg_name_3, arg_value_3)

    def _misc_url_4_arg_RunPlugin(self, arg_name_1, arg_value_1, arg_name_2, arg_value_2, 
                                  arg_name_3, arg_value_3, arg_name_4, arg_value_4):
        return 'XBMC.RunPlugin({0}?{1}={2}&{3}={4}&{5}={6}&{7}={8})'.format(self.base_url,
                                                                            arg_name_1, arg_value_1,
                                                                            arg_name_2, arg_value_2,
                                                                            arg_name_3, arg_value_3, 
                                                                            arg_name_4, arg_value_4)
