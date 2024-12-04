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
__date__ = "2024-11-27"  # Last update

import platform
from pathlib import Path
import os

# global_cache.py

# Constant for os
SYSTEM = platform.system()
HOME_PATH = Path.home()
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

MODS_PATHS = {
    "Windows": Path(HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
    "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
}


class GlobalCache:
    def __init__(self):
        self.config_cache = {}  # Configuration cache
        self.language_cache = {}  # Translation cache
        self.mods = {}  # Mod cache
        self.logs = {}  # For any internal log if needed
        self.total_mods = 0


global_cache = GlobalCache()
