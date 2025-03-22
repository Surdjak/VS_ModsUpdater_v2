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
Global Cache Management for Vintage Story Mod Updater

This module handles caching for various global data used throughout the script. It manages:
- Configuration data loaded from config.ini
- System information like paths and environment variables
- Language translations loaded from JSON files
- Mod-related data (mod info, updates, etc.)
- Logging data
"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2025-03-21"  # Last update


# global_cache.py


config_cache = {}  # Configuration cache
language_cache = {}  # Translation cache
mods_data = {"Local_Mods": [],
             "Distant_Mods": []}  # Mod cache
total_mods = 0
