#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024  Laerinok
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""


"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-22"  # Last update

import platform
from pathlib import Path
import os

# global_cache.py

# Constants for paths
APPLICATION_PATH = os.getcwd()
HOME_PATH = Path.home()
CONFIG_FILE_PATH = Path(APPLICATION_PATH).parent / Path('config.ini')
TEMP_PATH = Path(APPLICATION_PATH).parent / Path('temp')
LOGS_PATH = Path(APPLICATION_PATH).parent / Path('logs')
LANG_PATH = Path(APPLICATION_PATH).parent / Path('lang')
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

# Constant for os
SYSTEM = platform.system()

# Constants for url
URL_MODS = 'https://mods.vintagestory.at'
URL_API = 'https://mods.vintagestory.at/api'
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
    "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
}

MODS_PATHS = {
    "Windows": Path(HOME_PATH, r'AppData\Roaming\VintagestoryData\Mods'),
    "Linux": Path(XDG_CONFIG_HOME_PATH, 'VintagestoryData')
}

# Cache for translations
language_cache = {}

# Cache for the configuration (config.ini)
config_cache = {}
