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
Vintage Story mod management:

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-28"  # Last update

# mods_common_update.py

import datetime
import json
import logging
import re
import zipfile
from pathlib import Path
import urllib.error
import urllib.request
from bs4 import BeautifulSoup
from rich import print
import requests
from packaging.version import Version
from tqdm import tqdm

import config
import global_cache
import utils


config.load_config()
mod_dic = global_cache.global_cache.mods

# Access translations through the cache
cache_lang = global_cache.global_cache.language_cache

config.configure_logging()


# Creation of the mods list in a dictionary
def list_mods():
    path_mods = Path(global_cache.global_cache.config_cache['ModsPath']['path'])

    for mod_file in path_mods.iterdir():
        if zipfile.is_zipfile(mod_file):
            process_zip_mod(mod_file)
        elif mod_file.suffix.lower() == ".cs":
            process_cs_mod(mod_file)

    # Sort mod_dic by mod name
    sorted_mods = {key: value for key, value in sorted(mod_dic.items(), key=lambda item: item[1]["name"])}
    # Store in the cache
    global_cache.global_cache.mods = sorted_mods


def process_zip_mod(zip_mod):
    with zipfile.ZipFile(zip_mod, "r") as zip_modfile:
        with zip_modfile.open("modinfo.json", "r") as modinfo_json:
            modinfo_content = modinfo_json.read().decode("utf-8-sig")
            try:
                python_obj = json.loads(modinfo_content)
            except json.JSONDecodeError:
                python_obj = json.loads(utils.fix_json(modinfo_content))
            python_obj_normalized = utils.normalize_keys(python_obj)

            mod_name = python_obj_normalized.get("name", "").capitalize()
            mod_version = python_obj_normalized.get("version", "")
            mod_modid = python_obj_normalized.get("modid", "")
            mod_description = python_obj_normalized.get("description", "")
            add_mod_info(mod_name, mod_version, mod_modid, mod_description,
                         zip_mod.name)


def process_cs_mod(cs_mod):
    with open(cs_mod, "r", encoding="utf-8-sig") as cs_modfile:
        cs_file = cs_modfile.read()
        mod_name = re.search(r"(namespace )(\w*)", cs_file, flags=re.IGNORECASE)[
            2].capitalize()
        mod_version = \
            re.search(r"(Version\s=\s\")([\d.]*)\"", cs_file, flags=re.IGNORECASE)[2]
        mod_description = \
            re.search(r'Description = "(.*)",', cs_file, flags=re.IGNORECASE)[1]
        add_mod_info(mod_name, mod_version, mod_name, mod_description, cs_mod.name)


def add_mod_info(mod_name: str, mod_version: str, mod_modid: str, mod_description: str,
                 mod_file: str) -> None:
    mod_dic[mod_file] = {
        "name": mod_name,
        "local_version": mod_version,
        "modid": mod_modid,
        "description": mod_description
    }


def get_mod_api_data(modid):
    """
    Retrieve mod infos from API or cache.
    """
    logging.debug(f"Attempting to fetch data for mod '{modid}' from API.")

    # Check if the mod is already in the cache
    if modid in global_cache.global_cache.mods:
        logging.debug(f"Data for mod '{modid}' found in cache. Skipping API call.")
        return global_cache.global_cache.mods[modid]  # Return the cached data

    # If the mod is not in the cache, fetch the information via the API
    mod_url_api = f'{config.URL_API}/mod/{modid}'
    # print(f'\nmod_url_api: {mod_url_api}')  # debug
    # print(f'game_version: {global_cache.global_cache.config_cache['Game_Version']['version']}')  # debug
    game_version = global_cache.global_cache.config_cache['Game_Version']['version']
    logging.debug(f"Retrieving mod info from: {mod_url_api}")
    name = None
    try:
        response = requests.get(mod_url_api)
        response.raise_for_status()  # Check that the request is successful (status code 200)
        mod_json = response.json()  # Retrieve the JSON data
        name = mod_json['mod']['name']
        logging.debug(f"{name}: data from API retrieved successfully.")
        mainfile = get_mainfile_by_tag(mod_json['mod']['releases'], f'v{game_version}')
        modversion = get_modversion_by_tag(mod_json['mod']['releases'], f'v{game_version}')
        mod_info_api = {
            'name':  mod_json['mod']['name'],
            'assetid': mod_json['mod']['assetid'],
            'game_version': game_version,
            'modversion': modversion[0],
            'mainfile': mainfile[0],
            'changelog': get_changelog(mod_json['mod']['assetid'])
        }
        logging.info(f"Data successfully retrieved from API for mod '{name}'.")
        return mod_info_api

    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except Exception:
        # logging.error(f'Other error occurred: {err}')  # debug
        logging.error(f'{name}: No file available for the desired game version.')
    return None  # If an error occurs, return None


def update_mod_cache_with_api_ata():
    # Retrieve mods list from mods folder
    list_mods()
    # Créez la barre de progression tqdm avec le total explicite
    print(f"\n{global_cache.global_cache.language_cache['tqdm_looking_for_update']}")
    pbar = tqdm(global_cache.global_cache.mods.items(),
                unit="mod",
                total=len(global_cache.global_cache.mods),
                initial=1,
                bar_format="{l_bar} {bar} | {n}/{total} | {postfix}",
                ncols=100,
                position=0,
                leave=False)

    temporary_data = {}  # Dictionnaire temporaire pour stocker les données API

    # Itérer sur chaque mod dans le cache
    for mod, mod_info in pbar:
        # Mise à jour dynamique du nom du mod dans la barre de progression (affiche seulement le nom)
        pbar.set_postfix_str(mod_info['name'],
                             refresh=True)  # Affiche uniquement la valeur du nom

        # Récupérer les données de l'API sans modifier le cache directement
        mod_info_api = get_mod_api_data(mod_info['modid'])
        if mod_info_api:
            logging.info(
                f"API data collected for mod '{mod_info['name']}' (ID: {mod_info['modid']}).")
            temporary_data[
                mod_info['modid']] = mod_info_api  # Stocker temporairement les données
        """
        else:
            logging.error(
                f"Failed to collect API data for mod '{mod_info['name']}' (ID: {mod_info['modid']}).")
        """
    # Mise à jour des données dans le cache global
    for mod, mod_info in global_cache.global_cache.mods.items():
        modid = mod_info.get('modid')  # Identifier le `modid` de l'entrée actuelle
        if modid and modid in temporary_data:
            # Fusionner les données API avec les données existantes
            global_cache.global_cache.mods[mod].update(temporary_data[modid])


# get 'modversion' for tag from json mod api
def get_modversion_by_tag(mod_releases, target_tag):
    modversion = []
    for release in mod_releases:
        if target_tag in release['tags']:
            modversion.append(release['modversion'])
    return modversion


# get 'mainfile' for tag from json mod api
def get_mainfile_by_tag(mod_releases, target_tag):
    mainfiles = []
    for release in mod_releases:
        if target_tag in release['tags']:
            mainfiles.append(release['mainfile'])
    return mainfiles


def get_changelog(mod_asset_id):
    url_changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
    # url_changelog = f'https://mods.vintagestory.at/show/mod/4405#tab-files'  # for test
    # Scrap to retrieve changelog
    req_url = urllib.request.Request(url_changelog)
    log = {}
    raw_log = {}
    try:
        urllib.request.urlopen(req_url)
        req_page_url = requests.get(url_changelog, timeout=2)
        page = req_page_url.content
        soup = BeautifulSoup(page, features="html.parser")
        soup_raw_changelog = soup.find("div", {"class": "changelogtext"})

        # log version
        log_version = soup_raw_changelog.find('strong').text
        # raw_log[log_version] = soup_raw_changelog.text
        # print(f"\n{soup_raw_changelog}")  # debug

    except requests.exceptions.ReadTimeout:
        logging.warning('ReadTimeout error: Server did not respond within the specified timeout.')
    except urllib.error.URLError as err_url:
        # Affiche de l'erreur si le lien n'est pas valide
        print(f'[red]Lien non valide[/red]')
        msg_error = f'{err_url.reason} : {url_changelog}'
        logging.warning(msg_error)
    return log


mod_to_update = {}


def check_mod_to_update():
    for mod_filename, mod_details in global_cache.global_cache.mods.items():
        local_version = mod_details['local_version']
        modversion = mod_details.get('modversion')
        if modversion and Version(modversion) > Version(local_version):
            mod_to_update[mod_filename] = f'{config.URL_MODS}/{mod_details['mainfile']}'
        # print(f'[green]{mod_details['name']} peut être mis à jour.[/green]')
    return mod_to_update


def backup_mods(mods_to_backup):
    """
    Create a backup of the ZIP mods before download and manage a retention policy.
    """
    # Modifier par valeur config.ini
    max_backups = int(global_cache.global_cache.config_cache['Backup_Mods']['max_backups'])

    # Modifier par valeur de config .ini
    backup_folder_name = global_cache.global_cache.config_cache['Backup_Mods']['backup_folder']
    backup_folder = Path(config.APPLICATION_PATH).parent / backup_folder_name

    # Ensure the backup directory exists
    utils.setup_directories(backup_folder)

    # Create a unique backup name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_folder / f"backup_{timestamp}.zip"

    modspaths = global_cache.global_cache.config_cache['ModsPath']['path']

    # Create the ZIP archive
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for mod_key in mods_to_backup:
            zip_filename = Path(modspaths) / mod_key
            if zip_filename.is_file():
                backup_zip.write(zip_filename, arcname=zip_filename.name)

    logging.info(f"Backup of mods completed: {backup_path}")

    # Cleanup old backups if the maximum limit is exceeded
    backups = sorted(backup_folder.glob("backup_*.zip"),
                     key=lambda p: p.stat().st_mtime,
                     reverse=True)
    if len(backups) > max_backups:
        for old_backup in backups[max_backups:]:
            old_backup.unlink()
            logging.info(f"Deleted old backup: {old_backup}")


def load_mods_exclusion():
    # Check if the section and the key exist in the config cache
    mods_section = global_cache.global_cache.config_cache.get("Mod_Exclusion", {})
    raw_mods = mods_section.get("mods", "")

    # Split and clean the mod names, ensuring no empty strings
    excluded_mods = [mod.strip() for mod in raw_mods.split(",") if mod.strip()]

    return excluded_mods


if __name__ == "__main__":
    print(load_mods_exclusion())
    pass
