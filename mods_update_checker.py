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
__version__ = "2.1.3"
__date__ = "2025-08-24"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import global_cache
from utils import version_compare, check_excluded_mods, convert_html_to_markdown


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
    check_excluded_mods()  # Update excluded mods list
    excluded_filenames = [mod['Filename'] for mod in
                          global_cache.mods_data.get("excluded_mods", [])]
    mods_to_update = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for mod in global_cache.mods_data.get("installed_mods", []):
            futures.append(executor.submit(process_mod, mod, excluded_filenames))

        # We collect the results from the threads
        for future in as_completed(futures):
            mod_data = future.result()
            if mod_data:
                mods_to_update.append(mod_data)

    global_cache.mods_data['mods_to_update'] = sorted(mods_to_update,
                                                      key=lambda mod: mod[
                                                          "Name"].lower())


def process_mod(mod, excluded_filenames):
    """
    Processes a single mod to check for updates and fetch changelog.
    Returns the mod data if an update is found, otherwise None.
    """
    if mod['Filename'] in excluded_filenames:
        logging.info(f"Skipping excluded mod: {mod['Name']}")
        return None  # We return None if the mod is excluded

    # We check if an online version is available and if it is more recent
    if mod.get("mod_latest_version_for_game_version") and version_compare(
            mod["Local_Version"], mod["mod_latest_version_for_game_version"]):
        try:
            # Update the download URL in the global cache to match the new version
            mod['installed_download_url'] = mod['latest_version_dl_url']

            # Gets the changelog. If the key is missing, returns None.
            raw_changelog_html = mod.get("Changelog")

            # Checks if the changelog is None before trying to convert it
            changelog_markdown = ""
            if raw_changelog_html is not None:
                # Converts the HTML changelog to Markdown
                changelog_markdown = convert_html_to_markdown(raw_changelog_html)
            else:
                logging.info(f"Changelog for {mod['Name']} not available.")

            return {
                "Name": mod['Name'],
                "Old_version": mod['Local_Version'],
                "New_version": mod['mod_latest_version_for_game_version'],
                "Changelog": changelog_markdown,
                "Filename": mod['Filename'],
                "download_url": mod['latest_version_dl_url']
            }
        except Exception as e:
            logging.error(f"Failed to process changelog for {mod['Name']}: {e}")
            return None
    return None  # We return None if no update is found
