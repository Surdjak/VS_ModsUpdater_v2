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
__date__ = "2024-11-26"  # Last update

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

import requests
from packaging.version import Version
from tqdm import tqdm

import config
import global_cache
import utils

mod_dic = {}
mods_to_update = {}

config.load_config()
# Access translations through the cache
cache_lang = global_cache.global_cache.language_cache


# Creation of the mods list in a dictionary
def list_mods():
    path_mods = Path(global_cache.global_cache.config_cache['ModsPath']['path'])

    for mod_file in path_mods.iterdir():
        if zipfile.is_zipfile(mod_file):
            process_zip_mod(mod_file)
        elif mod_file.suffix.lower() == ".cs":
            process_cs_mod(mod_file)

    # Sort mod_dic by mod name
    return {key: value for key, value in
            sorted(mod_dic.items(), key=lambda item: item[1]["name"])}


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
        "version": mod_version,
        "modid": mod_modid,
        "description": mod_description
    }


mod_dic_sorted = list_mods()


# Get info stored in mod_dic_sorted
def get_mod_info(mod_file):
    try:
        mod_name = mod_dic_sorted[mod_file]['name']
        mod_version = mod_dic_sorted[mod_file]['version']
        mod_modid = mod_dic_sorted[mod_file]['modid']
        mod_description = mod_dic_sorted[mod_file]['description']
        return mod_name, mod_version, mod_modid, mod_description
    except:
        logging.warning(
            f"Mod file '{mod_file}' not found in sorted mod dictionary.")
        return None


mod_data_cache = {}


def get_mod_api_data(modid):
    # Check if the mod ID is already in the cache
    if modid in mod_data_cache:
        return mod_data_cache[modid]

    mod_url_api = f'{config.URL_API}/mod/{modid}'
    logging.debug(f"Retrieving mod info from: {mod_url_api}")

    try:
        response = requests.get(mod_url_api)
        response.raise_for_status()  # Checks that the request was successful (status code 200)
        mod_data = response.json()  # Retrieves JSON content
        name = mod_data['mod']['name']
        logging.debug(f"{name}: data from API retrieved successfully.")
        # Store the retrieved data in the cache
        mod_data_cache[modid] = mod_data
        return mod_data

    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logging.error(f'Other error occurred: {err}')


# get 'mainfile' for tag from json mod api
def get_mainfile_by_tag(mod_releases, target_tag):
    mainfiles = []
    for release in mod_releases:
        if target_tag in release['tags']:
            mainfiles.append(release['mainfile'])
    return mainfiles


# get 'modversion' for tag from json mod api
def get_modversion_by_tag(mod_releases, target_tag):
    modversion = []
    for release in mod_releases:
        if target_tag in release['tags']:
            modversion.append(release['modversion'])
    return modversion


def url_mod_to_dl(modfile):
    """ Construct url for DL according game version"""
    mod_info = get_mod_info(modfile)
    if not mod_info:
        logging.warning(f"No information found for mod file: {modfile}")
        return

    mod_name, mod_version, mod_modid, mod_description = mod_info
    game_version = global_cache.global_cache.config_cache['Game_Version']['version']
    if not game_version:
        logging.warning("Cannot retrieve the latest game version.")
        return

    mod_api_data = get_mod_api_data(mod_modid)
    if not mod_api_data:
        logging.warning(
            f"No data found for mod '{mod_name}' with ID '{mod_modid}'.")
        return
    mod_releases = mod_api_data['mod']['releases']

    tag_to_search = f'v{game_version}'
    modversion = []
    try:
        result = get_mainfile_by_tag(mod_releases, tag_to_search)
        modversion = get_modversion_by_tag(mod_releases, tag_to_search)
        url_mod_to_download = f'https://mods.vintagestory.at/{result[0]}'
        return mod_name, url_mod_to_download, modversion
    except IndexError:
        info = f'{mod_name}: no download corresponding to the desired game version v{modversion}.'
        logging.info(info)
        return mod_name, info, modversion


# Dictionnaire pour stocker les résultats de cache
mod_update_cache = {}


def check_mod_to_update():
    game_version = global_cache.global_cache.config_cache['Game_Version']['version']

    # Vérifie si les résultats sont déjà en cache pour la version du jeu
    if game_version in mod_update_cache:
        logging.info(f"Using cached update data for game version {game_version}.")
        return mod_update_cache[game_version]
    mods_to_update.clear()  # Réinitialise les résultats de mise à jour
    for mod_filename, mod_desc in tqdm(mod_dic_sorted.items(),
                                       desc=cache_lang.get('tqdm_looking_for_update'),
                                       unit="mod", ncols=100,
                                       bar_format="{l_bar} {bar} | {n}/{total} "):
        local_version = mod_desc['version']
        mod_data = get_mod_api_data(mod_desc['modid'])

        mod_last_version = mod_data['mod']['releases'][0]['modversion']
        mod_asset_id = mod_data['mod']['assetid']

        if Version(mod_last_version) > Version(local_version):
            mods_to_update[mod_desc['name']] = (
                game_version, local_version, mod_last_version, mod_asset_id,
                mod_filename)
    print('\n')
    logging.info('Update search completed.')

    # Mémorise le résultat dans le cache
    mod_update_cache[game_version] = mods_to_update.copy()

    return mods_to_update


def backup_mods():
    """
    Create a backup of the ZIP mods before download and manage a retention policy.
    """
    # Modifier par valeur config.ini
    max_backups = int(global_cache.global_cache.config_cache['Backup_Mods']['max_backups'])

    # Dictionnaire des mods à sauvegarder
    mods_to_backup = {}  # À remplacer par la liste effective des mods à sauvegarder
    mods_to_backup_import = check_mod_to_update()

    for mod_name, versions in mods_to_backup_import.items():
        for zip_filename, details in mod_dic_sorted.items():
            # Check if the mod name in mods_to_backup_import matches the 'name' in mod_dic_sorted
            if mod_name == details["name"]:
                zipfile_path = Path(
                    global_cache.MODS_PATHS[global_cache.SYSTEM]) / zip_filename
                if zipfile_path.is_file():
                    mods_to_backup[mod_name] = zipfile_path
                    break

    # Modifier par valeur de config .ini
    backup_folder_name = global_cache.global_cache.config_cache['Backup_Mods']['backup_folder']
    backup_folder = Path(config.APPLICATION_PATH).parent / backup_folder_name

    # Ensure the backup directory exists
    utils.setup_directories(backup_folder)

    # Create a unique backup name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_folder / f"backup_{timestamp}.zip"

    # Create the ZIP archive
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for mod_name, file_path in mods_to_backup.items():
            if file_path.is_file():
                backup_zip.write(file_path, arcname=file_path.name)

    logging.info(f"Backup of mods completed: {backup_path}")

    # Cleanup old backups if the maximum limit is exceeded
    backups = sorted(backup_folder.glob("backup_*.zip"),
                     key=lambda p: p.stat().st_mtime,
                     reverse=True)
    if len(backups) > max_backups:
        for old_backup in backups[max_backups:]:
            old_backup.unlink()
            logging.info(f"Deleted old backup: {old_backup}")


def get_changelog(mod_asset_id):
    # print(f'cache: {mod_data_cache}')  # debug
    url_changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
    # Scrap pour recuperer le changelog
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
        # log content
        raw_log[log_version] = soup_raw_changelog.text
        log[log_version] = raw_log[log_version].replace('\n', '\n\t\t').lstrip('\n')
    except requests.exceptions.ReadTimeout:
        logging.warning('ReadTimeout error: Server did not respond within the specified timeout.')
    except urllib.error.URLError as err_url:
        # Affiche de l'erreur si le lien n'est pas valide
        print(f'[red]Lien non valide[/red]')
        msg_error = f'{err_url.reason} : {url_changelog}'
        logging.warning(msg_error)
    return log


if __name__ == "__main__":
    pass
