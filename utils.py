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
__version__ = "2.0.0-dev2"
__date__ = "2025-03-25"  # Last update


# utils.py

import argparse
import json
import logging
import os
import random
import re
import sys
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from packaging.version import Version, InvalidVersion
from rich import print

import global_cache


# #### For test and debug ####
def print_dict(dictionary):
    """Print a dictionary in a structured format."""
    for key, value in dictionary.items():
        print(f"{key}: {value}")


def print_config_cache():
    """ Print the global_cache"""
    print(global_cache.config_cache)


def print_language_cache():
    """ Print the global_cache"""
    print(global_cache.language_cache)


def print_mods_data():
    """ Print the global_cache"""
    print(global_cache.mods_data)

# #### END ####


def setup_directories(path_dir):
    if not path_dir.exists():
        path_dir.mkdir(parents=True, exist_ok=True)


def check_mods_directory(mods_dir):
    mods_dir_path = Path(mods_dir)

    # Check if the directory is empty
    if not any(mods_dir_path.iterdir()):
        print("[red]Warning: The Mods directory is empty![/red] Please add your mod files.")
        logging.error("Warning: The Mods directory is empty!")
        exit_program(extra_msg="Empty folder")

    found_valid_file = False

    # Loop through all files in the 'Mods' directory
    for item in mods_dir_path.iterdir():
        if item.is_dir():
            print(f"[red]Warning: Directory found in Mods folder: {item.name}.[/red] Please ensure you have .zip files, not folders.")
            logging.error(f"Warning: Directory found in Mods folder: {item.name}. Please ensure you have .zip files, not folders.")
        elif item.suffix.lower() in ['.zip', '.cs']:
            found_valid_file = True  # We found at least one valid file

    # If no valid files were found, exit the program
    if not found_valid_file:
        exit_program(extra_msg="No valid mod files found in the Mods folder.")


def calculate_max_workers():
    """
    Calculate the maximum number of workers based on CPU cores and the user's max_workers value.
    Allows a factor of 2.5 times the number of CPU cores.
    :return: The validated max_workers value
    """
    user_max_workers = int(global_cache.config_cache["Options"]["max_workers"])
    cpu_cores = os.cpu_count()

    # Define the maximum workers allowed as 2.5 times the number of cores
    max_workers = cpu_cores * 2.5

    # If the user has set max_workers, validate it
    if user_max_workers:
        # Never exceed the max_workers limit
        return min(user_max_workers, max_workers)
    else:
        # If the user hasn't set max_workers, use the calculated max_workers
        return int(max_workers)  # We return an integer value for consistency


def get_random_headers():
    """Returns a random User-Agent from the predefined list."""
    return {"User-Agent": random.choice(global_cache.config_cache['USER_AGENTS'])}


def is_zip_valid(zip_path):
    """Checks if a zip file is valid and not corrupted."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.testzip()  # Tests the integrity of the zip file
        return True
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        return False


def normalize_keys(d):
    """Normalize the keys of a dictionary to lowercase"""
    if isinstance(d, dict):
        return {k.lower(): normalize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [normalize_keys(i) for i in d]
    else:
        return d


def sanitize_json_data(data):
    """Recursively replace None values with empty strings."""
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif data is None:
        return ""
    return data


def fix_json(json_data):
    """Fix the JSON string by removing comments, trailing commas, and ignoring the 'website' key."""

    # Remove single-line comments (lines starting with //)
    json_data = re.sub(r'^\s*//[^\n]*$', '', json_data, flags=re.MULTILINE)

    # Remove trailing commas before closing braces/brackets
    json_data = re.sub(r',\s*([}\]])', r'\1', json_data)

    # Try to load the JSON string into a Python dictionary
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON: {e}")
        return "Error: Invalid JSON data"

    # Sanitize the data: replace None with empty strings
    data = sanitize_json_data(data)

    # Remove the 'website' key if it exists
    if "website" in data:
        del data["website"]

    # Convert the dictionary back into a formatted JSON string
    json_data_fixed = json.dumps(data, indent=2)
    return json_data_fixed


def version_compare(local_version, online_version):
    # Compare local and online version
    if Version(local_version) < Version(online_version):
        new_version = True
        return new_version
    else:
        new_version = False
        return new_version


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
def get_latest_game_version(url_api='https://mods.vintagestory.at/api'):
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


def extract_filename_from_url(url):
    # Parse the URL and get the query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    # Extract the filename from the 'dl' parameter
    filename = query_params.get('dl', [None])[0]
    return filename


def check_excluded_mods():
    """
    Retrieve excluded mods from the config file and ensure they exist in the mods folder.
    """
    # Correct usage of the get method
    excluded_mods = global_cache.config_cache.get("Mod_Exclusion", {}).get("mods", "").split(", ")

    # Ensure we don't have empty strings in the list
    excluded_mods = [mod.strip() for mod in excluded_mods if mod.strip()]

    # Retrieve the absolute path of the mods folder
    mods_folder_path = global_cache.config_cache["MODS_PATHS"][global_cache.config_cache["SYSTEM"]].resolve()

    # Clear the previous excluded mods in global_cache
    # global_cache.mods_data["excluded_mods"] = []

    for mod in excluded_mods:
        # Check if the file exists in the mods folder
        mod_file_path = mods_folder_path / mod  # Build the path to the mod file
        if mod_file_path.exists():
            global_cache.mods_data["excluded_mods"].append({"Filename": mod})
            logging.info(f"Excluded mod added: {mod}")


def parse_args():
    parser = argparse.ArgumentParser(description="ModsUpdater options")

    parser.add_argument('--modspath', type=str, help='Enter the mods directory (in quotes).')
    parser.add_argument('--language', type=str, default='en_US', help='Set the language file (default=en_US)')
    parser.add_argument('--nopause', type=lambda x: x.lower() == 'true', default=False, help='Disable the pause at the end (default=false)')
    parser.add_argument('--exclusion', nargs='*', type=str, help='Filenames of mods to exclude (in quotes)')
    parser.add_argument('--forceupdate', type=lambda x: x.lower() == 'true', default=False, help='Force update all mods (default=false)')
    parser.add_argument('--makepdf', type=lambda x: x.lower() == 'true', default=False, help='Create a PDF file (default=false)')
    parser.add_argument('--exclude_prerelease_mods', type=lambda x: x.lower() == 'true', default=False, help='Enable/Disable prerelease mod updates (default=false)')

    return parser.parse_args()


def exit_program(msg="Program terminated", extra_msg=None):
    full_msg = msg if not extra_msg else f"{msg}: {extra_msg}"
    print(f"\n*** {full_msg} ***")
    logging.info(f"*** {full_msg} ***")
    time.sleep(2)  # 2-second delay to give the user time to read the message.
    sys.exit()
