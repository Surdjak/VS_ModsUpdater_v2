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
#
# Manage language translations using a global cache.
#
"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__date__ = "2025-03-21"  # Last update

# lang.py

import json
from pathlib import Path

import global_cache


# config.load_config()


def get_language_setting():
    """Retrieve the language setting from the global cache."""
    if not global_cache.config_cache:
        raise RuntimeError("Configuration cache is empty. Ensure configuration is loaded.")
    return global_cache.config_cache["Language"]["language"]


def load_translations(path=None):
    """
    Load translations into the global cache based on the current language setting.
    """
    # If translations are already loaded, return them from the cache
    if global_cache.language_cache:
        return global_cache.language_cache

    lang_file_path = None

    # Determine the path of the language file
    if path:
        lang_file_path = Path(path)
    elif global_cache.config_cache:
        language = get_language_setting()
        lang_file_path = Path() / "lang" / f"{language}.json"

    # Handle the case where lang_file_path could not be determined
    if not lang_file_path or not lang_file_path.exists():
        raise FileNotFoundError(
            f"[Error] Language file not found: {lang_file_path}. Ensure the path is correct."
        )

    # Load translations from the language file
    try:
        with open(lang_file_path, 'r', encoding='utf-8') as file:
            translations = json.load(file)
            global_cache.language_cache.update(translations)
    except json.JSONDecodeError as e:
        raise ValueError(f"[Error] Failed to parse language file: {lang_file_path}. {e}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"[Error] Unable to locate the language file: {lang_file_path}. {e}")

    return global_cache.language_cache


if __name__ == "__main__":
    pass
