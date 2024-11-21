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
__date__ = "2024-11-21"  # Last update

# lang.py

import json
import config
from pathlib import Path
# from utils import print_dict  # for test

_language_cache = {}  # Cache for loaded languages


def get_language_setting():
    """Retrieve the language setting from the configuration."""
    config_obj = config.load_config()
    return config_obj["language"]


def load_translations(path):
    if config.config_exists():
        """Load the translation file based on the language setting."""
        language = get_language_setting()
        # Construct the path to the language file
        lang_file_path = Path(f'{config.LANG_PATH}', f'{language}.json')
    else:
        lang_file_path = Path(path)

    # Load the translations if not already cached
    if not _language_cache:
        try:
            with open(lang_file_path, 'r', encoding='utf-8') as file:
                _language_cache.update(json.load(file))
        except FileNotFoundError:
            print(f"Error: The translation file {lang_file_path} was not found.")

    return _language_cache
