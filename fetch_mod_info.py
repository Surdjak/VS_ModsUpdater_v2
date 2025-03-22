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
__version__ = "2.0.0-dev1"
__date__ = "2025-03-22"  # Last update

# fetch_mod_info.py

import config
import global_cache
import utils
from pathlib import Path
import logging
import sys
import time
import zipfile
import json
import re
import requests
import random
from rich.progress import Progress
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    """Gets modid, name, and version information from modinfo.json in a zip file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Opens modinfo.json inside the zip file
            if 'modinfo.json' not in zip_ref.namelist():
                print(f"Warning: No modinfo.json found in {zip_path}")
                return None, None, None
            with zip_ref.open('modinfo.json') as modinfo_file:
                raw_json = modinfo_file.read().decode('utf-8-sig')
                fixed_json = utils.fix_json(raw_json)
                modinfo = json.loads(fixed_json)
                # Convert all keys to lowercase to ignore case
                modinfo_lower = {k.lower(): v for k, v in modinfo.items()}
                return modinfo_lower.get('modid'), modinfo_lower.get('name'), modinfo_lower.get('version'), modinfo_lower.get('description')
    except zipfile.BadZipFile:
        print(f"Error: {zip_path} is not a valid zip file.")
    except json.JSONDecodeError:
        print(f"Error: Failed to parse modinfo.json in {zip_path}")
    except Exception as e:
        print(f"Unexpected error processing {zip_path}: {e}")
    return None, None, None


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


def get_mainfile_for_version(mod_version, api_response):
    """
    Retrieves the 'mainfile' link for the given version in modinfo and compares it with the versions in the API file.

    mod_version: the mod version extracted from modinfo.json or a .cs file.
    api_response: the API response containing the version information and 'mainfile'.

    Returns the link for the corresponding 'mainfile'.
    """

    for release in api_response:
        modversion = release.get('modversion', [])
        # Check if the modinfo version is in the tags
        if mod_version == modversion:
            return release.get('mainfile')

    # If no match is found
    print(f"No link found for version {mod_version}.")
    return None


def get_api_info(modid):
    """Gets, via the API, the assetid and download link for the file corresponding to the mod version."""
    url_api_mod = f"{global_cache.config_cache['URL_BASE_MOD_API']}{modid}"
    try:
        response = requests.get(url_api_mod, headers=utils.get_random_headers(), timeout=5)
        response.raise_for_status()
        data = response.json()
        mod_asset_id = data['mod']['assetid']
        releases = data['mod']['releases']
        side = data['mod']['side']
        return mod_asset_id, side, releases
    except requests.exceptions.Timeout:
        print(f"Timeout when fetching API info for {modid}")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error when fetching API info for {modid}: {err}")
    except requests.RequestException as err:
        print(f"Error fetching API info for {modid}: {err}")
    except KeyError:
        print(f"Unexpected API response format for {modid}")
        return None, None, None
    finally:
        # Wait for a random time between 1 and 5 seconds.
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)


def process_mod_file(file, mods_data, invalid_files):
    """Traite un fichier de mod (zip ou cs), ajoute les résultats dans mods_data ou invalid_files"""
    if file.suffix == '.zip':
        if utils.is_zip_valid(file):
            modid, modname, local_mod_version, description = get_modinfo_from_zip(file)
            if modid and modname and local_mod_version:
                mods_data["Local_Mods"].append({
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
            mods_data["Local_Mods"].append({
                "Name": namespace,
                "Local_Version": local_mod_version,
                "ModId": modid,
                "Description": description,
                "Filename": file.name
            })
        else:
            invalid_files.append(file.name)  # Add invalid .cs file name


def get_mod_api_data():
    """
    Retrieve mod infos from API
    """
    # utils.print_config_cache()  # debug
    for mod in global_cache.mods_data['Local_Mods']:
        modid = mod['ModId']
        logging.debug(f"Attempting to fetch data for mod '{modid}' from API.")
        mod_url_api = f'{config.URL_BASE_MOD_API}{modid}'
        logging.debug(f"Retrieving mod info from: {mod_url_api}")
        try:
            response = requests.get(mod_url_api, headers=utils.get_random_headers(), timeout=5)
            response.raise_for_status()
            mod_json = response.json()
            mod_assetid = mod_json["mod"]["assetid"]
            return mod_assetid
        except requests.exceptions.HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logging.error(f'Error occurred: {err}')
        finally:
            # Wait for a random time between 1 and 5 seconds.
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
        return None


def list_mods(mods_folder):
    invalid_files = []  # Liste des fichiers invalides ou corrompus

    mod_files = list(mods_folder.iterdir())
    total_files = len(mod_files)
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning mods...", total=total_files)
        with ThreadPoolExecutor() as executor:
            futures = []
            for file in mods_folder.iterdir():
                futures.append(
                    executor.submit(process_mod_file, file, global_cache.mods_data, invalid_files))

            for idx, future in enumerate(as_completed(futures)):
                future.result()  # Wait for completion and handle exceptions
                progress.update(task, advance=1)  # Mettre à jour la barre de progression après chaque fichier

    # Sort the mods by "Name."
    global_cache.mods_data["Local_Mods"].sort(key=lambda mod: mod["Name"].lower() if mod["ModId"] else "")
    # Get Info from API
    get_mod_api_data()


if __name__ == "__main__":
    # pense-bete only
    pass
