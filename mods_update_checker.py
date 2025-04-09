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
__version__ = "2.1.1"
__date__ = "2025-04-01"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import fetch_changelog
import global_cache
from utils import version_compare, check_excluded_mods


def check_for_mod_updates():
    """
    This module automates the process of checking for updates to installed mods.
    It compares local mod versions with the latest available versions and retrieves changelogs for mods that require updates.

    Key functionalities include:
    - Checking for mod updates by comparing local and latest available versions.
    - Handling excluded mods to skip them during the update check.
    - Fetching changelogs for updated mods using the fetch_changelog module.
    - Populating the global_cache['mods_to_update'] list with relevant mod information.
    - Utilizing multithreading to efficiently process multiple mods.
    - Providing detailed logging for debugging and monitoring.
    """
    check_excluded_mods()  # Update excluded mods list#
    excluded_filenames = [mod['Filename'] for mod in global_cache.mods_data.get("excluded_mods", [])]
    mods_to_update = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for mod in global_cache.mods_data.get("installed_mods", []):
            futures.append(executor.submit(process_mod, mod, excluded_filenames, mods_to_update))
        for future in as_completed(futures):
            future.result()

    global_cache.mods_data['mods_to_update'] = sorted(mods_to_update, key=lambda mod: mod["Name"].lower())


def process_mod(mod, excluded_filenames, mods_to_update):
    """
    Processes a single mod to check for updates and fetch changelog.
    """
    if mod['Filename'] in excluded_filenames:
        logging.info(f"Skipping excluded mod: {mod['Name']}")
        return

    if mod.get("mod_latest_version_for_game_version") and version_compare(mod["Local_Version"], mod["mod_latest_version_for_game_version"]):
        try:
            changelog = fetch_changelog.get_raw_changelog(mod['Name'], mod['AssetId'], mod['mod_latest_version_for_game_version'])
            mods_to_update.append({
                "Name": mod['Name'],
                "Old_version": mod['Local_Version'],
                "New_version": mod['mod_latest_version_for_game_version'],
                "Changelog": changelog,
                "Filename": mod['Filename'],
                "url_download": mod['latest_version_dl_url']
            })
        except Exception as e:
            logging.error(f"Failed to process changelog for {mod['Name']}: {e}")
