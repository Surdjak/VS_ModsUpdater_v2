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
__date__ = "2024-12-03"  # Last update

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
import concurrent.futures
import config
import global_cache
import utils
import os


config.load_config()
mod_dic = global_cache.global_cache.mods

# Access translations through the cache
cache_lang = global_cache.global_cache.language_cache

config.configure_logging(global_cache.global_cache.config_cache["Logging"]['log_level'].upper())


# Creation of the mods list in a dictionary
def list_mods():
    path_mods = Path(global_cache.global_cache.config_cache['ModsPath']['path'])
    # List all mod files
    mod_files = [mod_file for mod_file in path_mods.iterdir() if zipfile.is_zipfile(mod_file) or mod_file.suffix.lower() == ".cs"]

    # Use ThreadPoolExecutor for I/O-bound tasks
    max_workers = config.MAX_WORKERS

    if max_workers is None:
        max_workers = os.cpu_count()
    # Apply a reasonable limit to avoid overload
    max_workers = min(max_workers, os.cpu_count() * 3)  # Limit to 3 times the number of logical cores

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Process all mod files in parallel
        futures = []
        for mod_file in mod_files:
            if zipfile.is_zipfile(mod_file):
                futures.append(executor.submit(process_zip_mod, mod_file))
            elif mod_file.suffix.lower() == ".cs":
                futures.append(executor.submit(process_cs_mod, mod_file))

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Will raise an exception if the function raised one

    # Sort mod_dic by mod name
    sorted_mods = {key: value for key, value in
                   sorted(mod_dic.items(), key=lambda item: item[1]["name"])}

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

    if modid in global_cache.global_cache.mods:
        logging.debug(f"Data for mod '{modid}' found in cache. Skipping API call.")
        return global_cache.global_cache.mods[modid]

    mod_url_api = f'{config.URL_API}/mod/{modid}'
    game_version = global_cache.global_cache.config_cache['Game_Version']['version']
    logging.debug(f"Retrieving mod info from: {mod_url_api}")

    try:
        response = requests.get(mod_url_api)
        response.raise_for_status()
        mod_json = response.json()
        name = mod_json['mod']['name']
        logging.debug(f"'{name}': Data from API retrieved successfully.")

        mod_releases = mod_json['mod']['releases']
        target_tag = f'v{game_version}'
        mod_data_by_tag = get_mod_data_by_tag(mod_releases, target_tag)
        modversion = mod_data_by_tag[0]
        mainfile = mod_data_by_tag[1]
        # print(f"\nmod_releases={mod_releases} - target_tag={target_tag}")  # debug
        logging.debug(f"mod_data_by_tag (before sorting): {mod_data_by_tag}")
        # print(f"\nmod_data_by_tag (before sorting): {mod_data_by_tag}")  # debug
        # print(f"\nname: {name}\nmodversion: {modversion}\nmainfile: {mainfile}")  # debug

        mod_info_api = {
            'name': mod_json['mod']['name'],
            'assetid': mod_json['mod']['assetid'],
            'game_version': game_version,
            'modversion': modversion,
            'mainfile': mainfile,
            # 'changelog': get_changelog(mod_json['mod']['assetid'])  # pose pb. a revoir !!!
            'changelog': ''
        }

        logging.debug(f"Final mod_info_api: {mod_info_api}")
        # print(f"\nFinal mod_info_api: {mod_info_api}")  # debug
        logging.info(f"'{name}': Data successfully retrieved from API.")
        return mod_info_api

    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logging.error(f'Error occurred: {err}')
    return None


def update_mod_cache_with_api_ata():
    # Retrieve mods list from mods folder
    list_mods()
    # Create the tqdm progress bar with the explicit total
    print(f"\n{global_cache.global_cache.language_cache['tqdm_looking_for_update']}")
    pbar = tqdm(global_cache.global_cache.mods.items(),
                unit="mod",
                total=len(global_cache.global_cache.mods),
                initial=1,
                bar_format="{l_bar} {bar} | {n}/{total} | {postfix}",
                ncols=100,
                position=0,
                leave=False)

    temporary_data = {}  # Temporary dictionary to store API data

    # Iterate over each mod in the cache
    for mod, mod_info in pbar:
        # Dynamically update the mod name in the progress bar (only display the name)
        pbar.set_postfix_str(mod_info['name'],
                             refresh=True)  # Display only the value of the name

        # Retrieve the data from the API without modifying the cache directly
        mod_info_api = get_mod_api_data(mod_info['modid'])
        if mod_info_api:
            logging.debug(
                f"API data collected for mod '{mod_info['name']}' (ID: {mod_info['modid']}).")
            temporary_data[
                mod_info['modid']] = mod_info_api  # Temporarily store the data
        """
        else:
            logging.error(
                f"Failed to collect API data for mod '{mod_info['name']}' (ID: {mod_info['modid']}).")
        """
    # Update the data in the global cache
    for mod, mod_info in global_cache.global_cache.mods.items():
        modid = mod_info.get('modid')  # Identify the `modid` of the current entry
        if modid and modid in temporary_data:
            # Merge the API data with the existing data
            global_cache.global_cache.mods[mod].update(temporary_data[modid])


def get_mod_data_by_tag(mod_releases, target_tag):
    """
    Retrieves modversion and mainfile for a given target tag.

    Args:
        mod_releases (list): List of mod release dictionaries.
        target_tag (str): The tag to search for.

    Returns:
        list: A list of tuples containing (modversion, mainfile) for matching releases.
    """
    results = []
    for release in mod_releases:
        tags = release.get('tags', [])  # Récupération des tags de la release

        # Si la liste des tags contient une seule valeur, on fait une comparaison stricte
        if len(tags) == 1:
            if target_tag.strip().lower() == tags[0].strip().lower():  # Comparaison avec une seule valeur
                modversion = release.get('modversion')
                mainfile = release.get('mainfile')
                results.append((modversion, mainfile))
        # Sinon, on fait la comparaison habituelle pour plusieurs tags
        elif any(target_tag.strip().lower() in tag.strip().lower() for tag in tags):
            modversion = release.get('modversion')
            mainfile = release.get('mainfile')
            results.append((modversion, mainfile))
    # print(f"\nFiltered results: {results[0]}")  # debug
    return results[0]


def get_changelog(mod_asset_id):
    url_changelog = f'https://mods.vintagestory.at/show/mod/{mod_asset_id}#tab-files'
    # url_changelog = f'https://mods.vintagestory.at/show/mod/7214#tab-files'  # for test
    # Scrap to retrieve changelog
    req_url = urllib.request.Request(url_changelog)
    log = {}
    cleaned_text = None
    try:
        urllib.request.urlopen(req_url)
        req_page_url = requests.get(url_changelog, timeout=2)
        page = req_page_url.content
        soup = BeautifulSoup(page, features="html.parser")
        changelog_div = soup.find("div", {"class": "changelogtext"})
        # log version
        log_version = changelog_div.find('strong').text
        # print(f"\n\nchangelog_div: {log_version}\n\n{changelog_div}\n")  # debug

        # Nettoyer le contenu
        if changelog_div:
            # 1. Supprimer la balise <strong> qui contient la version et d'autres éléments non nécessaires
            for strong_tag in changelog_div.find_all('strong'):
                strong_tag.decompose()

            # 2. Remplacer les liens <a> par leur URL texte
            for a_tag in changelog_div.find_all('a'):
                a_tag.insert_after(
                    f" [Link: {a_tag.get('href')}]")  # Remplacer le lien par son URL

            # 3. Remplacer les balises <br> par des sauts de ligne
            for br_tag in changelog_div.find_all('br'):
                br_tag.insert_before("\n")
                br_tag.decompose()  # Supprimer la balise <br> après l'insertion du saut de ligne

            # 4. Convertir en texte brut
            cleaned_text = changelog_div.get_text(separator="\n", strip=True)
            # print(f"\n\n{cleaned_text}\n")  # debug
        # print(f"\n\n{changelog_div}\n")  # debug

    except requests.exceptions.ReadTimeout:
        logging.warning('ReadTimeout error: Server did not respond within the specified timeout.')
    except urllib.error.URLError as err_url:
        # Affiche de l'erreur si le lien n'est pas valide
        print(f'[red]Lien non valide[/red]')
        msg_error = f'{err_url.reason} : {url_changelog}'
        logging.warning(msg_error)
    return cleaned_text


mod_to_update = {}


def check_mod_to_update():
    # print(global_cache.global_cache.mods)  # debug
    for mod_filename, mod_details in global_cache.global_cache.mods.items():
        local_version = mod_details['local_version']
        modversion = mod_details.get('modversion')
        # print(f"mod_filename: {mod_filename}")  # debug
        # print(f"local_version: {local_version}\tmodversion: {modversion}")  # debug
        if modversion and Version(modversion) > Version(local_version):
            mod_to_update[mod_filename] = f'{config.URL_MODS}/{mod_details['mainfile']}'
            # print(f'[green]{mod_details['name']} peut être mis à jour.[/green]')  # debug
    return mod_to_update


def backup_mods(mods_to_backup):
    """
    Create a backup of the ZIP mods before download and manage a retention policy.
    """
    max_backups = int(global_cache.global_cache.config_cache['Backup_Mods']['max_backups'])
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

    pass
