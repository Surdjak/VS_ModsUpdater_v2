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
This module handles manual updates for Vintage Story mods.
It retrieves changelogs for mods that need updates and prompts the user to download them.
"""

__author__ = "Laerinok"
__version__ = "2.0.2"
__date__ = "2025-04-03"  # Last update

# mods_manual_update.py

import logging
import os
from pathlib import Path

from rich import print
from rich.progress import Progress
from rich.prompt import Prompt

import global_cache
import lang
from http_client import HTTPClient
from utils import extract_filename_from_url

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()

"""
parcourir global_cache['mods_to_update'], afficher changelog, proposer de mettre à jour, et si oui, telecharger la maj
"""


def perform_manual_updates(mods_to_update):
    """
    Processes the mods to update, displays changelogs, and prompts the user to download.

    Args:
        mods_to_update (list): List of mods to update.
    """
    for mod in mods_to_update:
        print(f"\n[green]{mod['Name']} (v{mod['Old_version']} {lang.get_translation("to")} v{mod['New_version']})[/green]")
        print(f"[bold][yellow]CHANGELOG:\n{mod['Changelog']}[/yellow][/bold]\n")

        download_choice = Prompt.ask(lang.get_translation("manual_download_mod_prompt"), choices=["y", "n"], default="y").lower()

        if download_choice == "y":
            download_mod(mod)
            logging.info(
                f"\t- {mod['Name']} (v{mod['Old_version']} {lang.get_translation("to")} v{mod['New_version']})")
        else:
            print(f"{lang.get_translation("manual_skipping_download")} {mod['Name']}.")
            logging.info(f"Skipping download for {mod['Name']}.")


def download_mod(mod):
    """
    Downloads the specified mod.
    """
    url = mod['url_download']
    filename = extract_filename_from_url(os.path.basename(url))
    destination_folder = Path(global_cache.config_cache['ModsPath']['path']).resolve()
    destination_path = destination_folder / filename

    print(f"{lang.get_translation("manual_downloading_mod")} {mod['Name']}...")
    logging.info(f"Downloading {mod['Name']} from {url} to {destination_path}")

    try:
        response = client.get(url, stream=True, timeout=int(global_cache.config_cache["Options"]["timeout"]))
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with Progress() as progress:
            task = progress.add_task("[cyan]Downloading...", total=total_size)
            with open(destination_path, 'wb') as file:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    progress.update(task, advance=len(data))

        print(f"{lang.get_translation("manual_download_completed")} {mod['Name']}.")
        logging.info(f"Download completed for {mod['Name']}.")

        # Erase old file
        file_to_erase = mod['Filename']
        filename_value = Path(global_cache.config_cache['ModsPath']['path']) / file_to_erase
        filename_value = filename_value.resolve()
        try:
            os.remove(filename_value)
            logging.info(f"Old file {file_to_erase} has been deleted successfully.")
        except PermissionError:
            logging.error(
                f"PermissionError: Unable to delete {file_to_erase}. You don't have the required permissions.")
        except FileNotFoundError:
            logging.error(
                f"FileNotFoundError: The file {file_to_erase} does not exist.")
        except Exception as e:
            logging.error(
                f"An unexpected error occurred while trying to delete {file_to_erase}: {e}")

        # Update global_cache.mods_data['installed_mods']
        for installed_mod in global_cache.mods_data['installed_mods']:
            if installed_mod.get('Filename') == mod.get('Filename'):
                installed_mod['Local_Version'] = mod['New_version']
                break  # Stop searching once found

    except Exception as e:
        print(f"{lang.get_translation("manual_download_error")} {mod['Name']}: {e}")
        logging.error(f"Error downloading {mod['Name']}: {e}")


if __name__ == "__main__":
    pass
