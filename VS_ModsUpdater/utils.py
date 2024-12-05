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

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-27"  # Last update


# utils.py

import global_cache
import argparse
import re
import logging
import requests
import sys
import time
from packaging.version import Version, InvalidVersion


def print_dict(dictionary):  # For test and debug
    """Print a dictionary in a structured format."""
    for key, value in dictionary.items():
        print(f"{key}: {value}")


def normalize_keys(d):
    """Normalize the keys of a dictionary to lowercase"""
    if isinstance(d, dict):
        return {k.lower(): normalize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [normalize_keys(i) for i in d]
    else:
        return d


def fix_json(json_data):
    # Correction 1 : Remove final commas
    json_data = re.sub(r",\s*([}\]])", r"\1", json_data)

    # Correction 2 : Add missing quotation marks around keys
    json_data = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_data)
    return json_data


def version_compare(local_version, online_version):
    # Compare local and online version
    if Version(local_version) < Version(online_version):
        new_version = True
        return new_version
    else:
        new_version = False
        return new_version


def setup_directories(path_dir):
    if not path_dir.exists():
        path_dir.mkdir(parents=True, exist_ok=True)


def log_error(message):
    print(message)
    logging.error(message)


def is_valid_version(version_string):
    """
    Validate if the version string matches the standard version format.
    Args:
        version_string (str): The version string to validate.
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        # Try to create a Version object.
        Version(version_string)
        return True
    except InvalidVersion:
        # If the version is not valid, an InvalidVersion exception will be raised.
        return False


def complete_version(version_string):
    """Ensure version has three components (major.minor.patch)."""
    parts = version_string.split(".")
    while len(parts) < 3:  # Add missing components
        parts.append("0")
    return ".".join(parts)


# Retrieve the last game version
def get_last_game_version(url_api='https://mods.vintagestory.at/api'):
    gameversions_api_url = f'{url_api}/gameversions'
    try:
        response = requests.get(gameversions_api_url)
        response.raise_for_status()  # Checks that the request was successful (status code 200)
        gameversion_data = response.json()  # Retrieves JSON content
        logging.info(f"Game version data retrieved.")
        # Retrieve the latest version
        return gameversion_data['gameversions'][0]['name'][1:]
    except:
        logging.warning(f"Cannot reach gameversion api.")
        return None


def parse_args():
    parser = argparse.ArgumentParser(description="ModsUpdater options")

    parser.add_argument('--modspath', type=str, help='Enter the mods directory (in quotes).')
    parser.add_argument('--language', type=str, default='en_US', help='Set the language file (default=en_US)')
    parser.add_argument('--nopause', type=lambda x: x.lower() == 'true', default=False, help='Disable the pause at the end (default=false)')
    parser.add_argument('--exclusion', nargs='*', type=str, help='Filenames of mods to exclude (in quotes)')
    parser.add_argument('--forceupdate', type=lambda x: x.lower() == 'true', default=False, help='Force update all mods (default=false)')
    parser.add_argument('--makepdf', type=lambda x: x.lower() == 'true', default=False, help='Create a PDF file (default=false)')
    parser.add_argument('--disable_mod_dev', type=lambda x: x.lower() == 'true', default=False, help='Enable/Disable mod dev updates (default=false)')

    return parser.parse_args()


def update_cache_from_args(args):
    if args.modspath:
        global_cache.global_cache.modspath = args.modspath
    if args.language:
        global_cache.global_cache.language = args.language
    if args.nopause:
        global_cache.global_cache.nopause = args.nopause == 'true'
    if args.exclusion:
        global_cache.global_cache.exclusion = args.exclusion
    if args.forceupdate:
        global_cache.global_cache.forceupdate = args.forceupdate == 'true'
    if args.makepdf:
        global_cache.global_cache.makepdf = args.makepdf == 'true'
    if args.disable_mod_dev:
        global_cache.global_cache.disable_mod_dev = args.disable_mod_dev == 'true'


def exit_program():
    time.sleep(2)  # 2-second delay to give the user time to read the message.
    sys.exit()
