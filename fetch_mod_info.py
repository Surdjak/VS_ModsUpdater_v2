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
Vintage Story mod management - Fetching mods information
- locally from zip file
- online with api
"""

__author__ = "Laerinok"
__version__ = "2.0.0-dev2"
__date__ = "2025-03-24"  # Last update

# fetch_mod_info.py

import json
import logging
import random
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from packaging.version import Version
from rich.progress import Progress

import config
import global_cache
from utils import fix_json, get_random_headers, is_zip_valid


def get_mod_path():
    # Check if ModsPath and path exist in the config.
    if "ModsPath" not in global_cache.config_cache or "path" not in global_cache.config_cache["ModsPath"]:
        print("Error: The ModsPath or 'path' key is missing in the configuration.")
        time.sleep(2)
        sys.exit(1)  # Stop the script with an error code

    mods_path = Path(global_cache.config_cache['ModsPath']['path'])
    if not mods_path.exists():
        print(f"Error: The mods path is not found.")
        time.sleep(2)
        sys.exit(1)  # Stop the script with an error code

    return mods_path


def get_modinfo_from_zip(zip_path):
    """Gets modid, name, version, and description from modinfo.json in a zip file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()

            # Check if modinfo.json is at the root of the zip file
            if 'modinfo.json' in file_list:
                modinfo_path = 'modinfo.json'
            else:
                # Search for modinfo.json in any subdirectory and stop at the first match
                modinfo_path = next(
                    (f for f in file_list if f.endswith('/modinfo.json')), None)

                if not modinfo_path:
                    return None, None, None, None

            # Open and read modinfo.json
            with zip_ref.open(modinfo_path) as modinfo_file:
                raw_json = modinfo_file.read().decode('utf-8-sig')
                fixed_json = fix_json(raw_json)  # Fix potential JSON formatting issues
                modinfo = json.loads(fixed_json)

                # Convert all keys to lowercase to avoid case sensitivity issues
                modinfo_lower = {k.lower(): v for k, v in modinfo.items()}
                return (
                    modinfo_lower.get('modid'),
                    modinfo_lower.get('name'),
                    modinfo_lower.get('version'),
                    modinfo_lower.get('description')
                )

    except zipfile.BadZipFile:
        logging.error(f"Error: {zip_path} is not a valid zip file.")
    except json.JSONDecodeError:
        logging.error(f"Error: Failed to parse modinfo.json in {zip_path}")
    except Exception as e:
        logging.error(f"Unexpected error processing {zip_path}: {e}")

    return None, None, None, None


def get_cs_info(cs_path):
    """Gets Version, Side, namespace information from a .cs file."""
    with open(cs_path, 'r', encoding='utf-8') as cs_file:
        content = cs_file.read()
        # Using regex to extract the values
        version_match = re.search(r'Version\s*=\s*"([^"]+)"', content)
        namespace_match = re.search(r'namespace\s+([A-Za-z0-9_]+)', content)
        description_match = re.search(r'Description\s*=\s*"([^"]+)"', content)
        # If the information is found, return it
        version = version_match.group(1) if version_match else None
        description = description_match.group(1) if description_match else None
        namespace = namespace_match.group(1) if namespace_match else None
        modid = namespace.lower().replace(" ", "") if namespace else None
        return version, namespace, modid, description


def get_api_info(modid):
    """Gets, via the API, the assetid and download link for the file corresponding to the mod version."""
    url_api_mod = f"{global_cache.config_cache['URL_BASE_MOD_API']}{modid}"
    try:
        response = requests.get(url_api_mod, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        data = response.json()
        mod_asset_id = data['mod']['assetid']
        releases = data['mod']['releases']
        side = data['mod']['side']
        return mod_asset_id, side, releases
    except requests.exceptions.Timeout:
        logging.error(f"Timeout when fetching API info for {modid}")
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error when fetching API info for {modid}: {err}")
    except requests.RequestException as err:
        logging.error(f"Error fetching API info for {modid}: {err}")
    except KeyError:
        logging.error(f"Unexpected API response format for {modid}")
        return None, None, None
    finally:
        # Wait for a random time between 1 and 5 seconds.
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)


def process_mod_file(file, mods_data, invalid_files):
    """Process a mod file (zip or cs), and add the results to mods_data or invalid_files."""
    if file.suffix == '.zip':
        if is_zip_valid(file):
            modid, modname, local_mod_version, description = get_modinfo_from_zip(file)
            if modid and modname and local_mod_version:
                mods_data["installed_mods"].append({
                    "Name": modname,
                    "Local_Version": local_mod_version,
                    "ModId": modid,
                    "Description": description,
                    "Filename": file.name
                })
            else:
                invalid_files.append(file.name)  # Add file name to invalid files list
        else:
            invalid_files.append(
                file.name)  # Add corrupted file name to invalid files list
    elif file.suffix == '.cs':
        local_mod_version, namespace, modid, description = get_cs_info(file)
        if local_mod_version and namespace and modid:
            mods_data["installed_mods"].append({
                "Name": namespace,
                "Local_Version": local_mod_version,
                "ModId": modid,
                "Description": description,
                "Filename": file.name
            })
        else:
            invalid_files.append(file.name)  # Add invalid .cs file name


def get_compatible_releases(mod_json, user_game_version):
    """
    Retrieve all compatible releases for the mod based on the user_game_version.

    A release is considered compatible if at least one of its tag versions has the same major and minor version
    as user_game_version and is less than or equal to user_game_version.
    The releases are then sorted in descending order (by modversion and creation date).
    """
    releases = mod_json.get("mod", {}).get("releases", [])
    user_ver = Version(user_game_version.lstrip("v"))
    compatible_releases = []
    for release in releases:
        for tag in release.get("tags", []):
            if not tag:
                continue
            try:
                tag_ver = Version(tag.lstrip("v"))
                # Only include the release if the tag is exactly equal to the user's game version.
                if tag_ver == user_ver:
                    compatible_releases.append(release)
                    break  # Stop checking other tags for this release.
            except Exception:
                continue  # Ignore invalid version tags.

    if not compatible_releases:
        logging.info(
            f"{mod_json['mod']['name']}: No compatible release found for game version {user_game_version}.")
        return []

    # Sort compatible releases by modversion (including patch) and creation date in descending order.
    sorted_releases = sorted(
        compatible_releases,
        key=lambda r: (Version(r.get("modversion") or "0.0.0"), r.get("created") or ""),
        reverse=True
    )
    return sorted_releases


def get_mod_api_data(mod):
    """
    Retrieve mod infos from API
    """
    modid = mod['ModId']
    logging.debug(f"Attempting to fetch data for mod '{modid}' from API.")
    mod_url_api = f'{config.URL_BASE_MOD_API}{modid}'
    logging.debug(f"Retrieving mod info from: {mod_url_api}")
    try:
        response = requests.get(mod_url_api, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        mod_json = response.json()
        mod_assetid = mod_json["mod"]["assetid"]
        mod_url = f"{global_cache.config_cache['URL_MOD_DB']}{mod_assetid}"

        sorted_releases = get_compatible_releases(mod_json, global_cache.config_cache['Game_Version']['user_game_version'])
        mainfile_url = sorted_releases[0]['mainfile']

        mod_latest_version_for_game_version = sorted_releases[0]['modversion']
        return mod_assetid, mod_url, mainfile_url, mod_latest_version_for_game_version
    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logging.error(f'Error occurred: {err}')
    finally:
        # Wait for a random time between 0.5 and 1.5 seconds.
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
    return None, None, None, None


def scan_and_fetch_mod_info(mods_folder):
    invalid_files = []  # List of invalid or corrupted files.

    mod_files = list(mods_folder.iterdir())
    total_files = len(mod_files)
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning mods...", total=total_files)
        with ThreadPoolExecutor() as executor:
            futures = []
            for file in mods_folder.iterdir():
                futures.append(
                    executor.submit(process_mod_file, file, global_cache.mods_data,
                                    invalid_files))

            for idx, future in enumerate(as_completed(futures)):
                future.result()  # Wait for completion and handle exceptions
                progress.update(task, advance=1)  # Update the progress bar after each file.

    # Sort the mods by "Name."
    global_cache.mods_data["installed_mods"].sort(
        key=lambda mod: mod["Name"].lower() if mod["ModId"] else "")

    # Prepare the API calls with multithreading and the progress bar.
    mod_ids = [mod['ModId'] for mod in global_cache.mods_data["installed_mods"]]
    mods = global_cache.mods_data["installed_mods"]  # Complete list of mods to associate the results.

    with Progress() as progress:
        api_task = progress.add_task("[green]Fetching mod info from API...",
                                     total=len(mod_ids))
        with ThreadPoolExecutor() as executor:
            api_futures = []
            # Use a dictionary to associate the mod with the future.
            future_to_mod = {}
            for mod in mods:
                future = executor.submit(get_mod_api_data, mod)  # Pass the entire mod.
                api_futures.append(future)
                future_to_mod[future] = mod  # Associate each future with its mod.
            for future in as_completed(api_futures):
                mod = future_to_mod[future]  # Retrieve the mod linked to the future.
                mod_assetid, mod_url, mainfile_url, mod_latest_version_for_game_version = future.result()  # Retrieve the result of each API call.
                if mod_assetid and mod_url:
                    mod["AssetId"] = mod_assetid
                    mod["Mod_url"] = mod_url
                    mod["mod_latest_version_for_game_version"] = mod_latest_version_for_game_version
                    mod["Latest_version_mod_url"] = mainfile_url
                    logging.debug(f"Received assetid: {mod_assetid} and mod_url: {mod_url} for mod: {mod['Name']}")
                else:
                    logging.warning(f"Failed to retrieve assetid and mod_url for mod: {mod['Name']}")

                # Update the progress bar with the mod name.
                progress.update(api_task, advance=1, description=f"[cyan]Fetching: {mod['Name']}")


if __name__ == "__main__":
    # pense-bete only
    pass
