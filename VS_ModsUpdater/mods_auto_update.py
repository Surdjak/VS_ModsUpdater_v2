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
-

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-26"  # Last update

# mods_auto_update.py

import global_cache
import mods_common_update
import utils
import os
import config
import logging
import requests
import wget
from rich import print
from pathlib import Path

config.load_config()
config.configure_logging()

print(f'\n\t[yellow]Auto Update for game version {global_cache.global_cache.config_cache['Game_Version']['version']}[/yellow]')


def auto_download():
    # On procède à la maj
    logging.info("Starting download process for mods.")
    print(f'[yellow]Téléchargement des mods:[yellow]\n')
    for mod, url in mods_to_update.items():
        dl_link = url
        modspaths = global_cache.global_cache.config_cache['ModsPath']['path']
        modname = global_cache.global_cache.mods[mod]['name']
        modversion = global_cache.global_cache.mods[mod]['modversion']
        current_mod = Path(modspaths) / mod
        resp = requests.get(str(dl_link), stream=True, timeout=2)
        file_size = int(resp.headers.get("Content-length"))
        file_size_mo = round(file_size / (1024 ** 2), 2)
        logging.info(
            f"Preparing to download {modname} (v{modversion}) - Size: {file_size_mo} MB.")
        try:
            # os.remove(current_mod)  # désactivé temporairment
            logging.info(f"Deleted old version of {modname} from {modspaths}.")
        except PermissionError as e:
            logging.error(f"Permission denied while deleting {current_mod}: {e}")
            print(f"[red]You don't have permission to delete this file.[/red]")
            utils.exit_program()
        except FileNotFoundError as e:
            logging.warning(f"{current_mod} not found during deletion: {e}")
            print(f'{current_mod} not found')
            utils.exit_program()
        print(f'[green] {modname} (v{modversion}) [/green] [white]Téléchargement en cours...({str(file_size_mo)}Mb)[/white]')
        try:
            # wget.download(dl_link, str(modspaths))  # désactivé temporairment
            print('\n')
            logging.info(f"Successfully downloaded {modname} to {modspaths}.")
        except Exception as e:
            logging.error(f"Error during download of {modname}: {e}")
            raise


mods_common_update.update_mod_cache_with_api_ata()

# Look for mods to update
mods_to_update = mods_common_update.check_mod_to_update()

# Backup mods before Download
mods_common_update.backup_mods(mods_to_update)

# Download Mods
auto_download()


if __name__ == "__main__":
    # test
    pass
    # print(global_cache.global_cache.mods)
    # auto_update()
