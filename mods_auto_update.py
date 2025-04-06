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
This module automates the process of checking for and updating Vintage Story mods. It compares local mod versions with the latest available versions, downloads updates, and manages backups.

Key functionalities include:
- Checking for mod updates by comparing local and latest available versions.
- Fetching changelogs for updated mods.
- Backing up mods before updating to prevent data loss.
- Downloading updated mods using multithreading for efficiency.
- Managing backup retention policies to avoid excessive disk usage.
- Providing detailed logging and user feedback on the update process.
- Handling excluded mods to skip them during the update process.
- Erasing old files before downloading the new ones.
- Resume the list of the mods updated with the changelog.

"""
__author__ = "Laerinok"
__version__ = "2.0.2"
__date__ = "2025-04-03"  # Last update


# mods_auto_update.py


import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich import print
from rich.console import Console
from rich.progress import Progress

import config
import global_cache
import lang
from http_client import HTTPClient
from utils import extract_filename_from_url, validate_workers

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()
console = Console()


def download_file(url, destination_path, progress_bar, task):
    """
    Download the file from the given URL and save it to the destination path with a progress bar using Rich.
    Implements error handling and additional security measures.
    """
    if not config.download_enabled:
        logging.info(f"Skipping download - for TEST")
        return  # Skip download if disabled

    response = client.get(url, stream=True, timeout=int(global_cache.config_cache["Options"]["timeout"]))
    response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx, 5xx)

    # Get the total size of the file (if available)
    total_size = int(response.headers.get('content-length', 0))

    if total_size == 0:
        print(f"[bold indian_red1]{lang.get_translation("auto_file_size_unknown")}[/bold indian_red1]")

    with open(destination_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            progress_bar.update(task, advance=len(data))  # Update progress bar in the same task

    logging.info(f"Download completed: {destination_path}")


def download_mods_to_update(mods_data):
    """
    Download all mods that require updates using multithreading with a progress bar for each download.
    """
    # Initialize the Rich Progress bar
    with Progress() as progress:
        # Create a single task for all downloads
        task = progress.add_task(f"[cyan]{lang.get_translation("auto_downloading_mods")}", total=len(mods_data))

        # Create a thread pool executor for parallel downloads
        max_workers = validate_workers()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for mod in mods_data:
                url = mod['url_download']
                # Extract the filename from the URL (using the name from the URL)
                filename = os.path.basename(url)
                filename = extract_filename_from_url(filename)

                # Set the destination folder path
                destination_folder = Path(global_cache.config_cache['ModsPath']['path']).resolve()
                destination_path = destination_folder / filename  # Combine folder path and filename

                # Submit download tasks to the thread pool with progress bar
                futures.append(executor.submit(download_file, url, destination_path, progress, task))

                # Erase old file
                file_to_erase = mod['Filename']
                filename_value = Path(global_cache.config_cache['ModsPath']['path']) / file_to_erase
                filename_value = filename_value.resolve()
                if not config.download_enabled:
                    logging.info(f"Skipping download - for TEST")
                    break  # Skip download (and erase) if disabled
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

                # Update the progress for each mod with mod name or file name
                mod_name = mod['Name']  # Get the mod name from the data
                progress.update(task, advance=1, description=f"[cyan]{lang.get_translation("auto_downloading_mod_name")} [green]{mod_name}")

            # Wait for all downloads to finish
            for future in futures:
                future.result()  # This will raise an exception if something went wrong


def resume_mods_updated():
    # app_log.txt
    print(f"\n{lang.get_translation("auto_mods_updated_resume")}")
    logging.info("Followings mods have been updated (More details in updated_mods_changelog.txt):")
    for mod in global_cache.mods_data.get('mods_to_update'):
        print(f"- [green]{mod['Name']} (v{mod['Old_version']} {lang.get_translation("to")} v{mod['New_version']}):[/green]")
        print(f"[bold][dark_goldenrod]CHANGELOG:\n{mod['Changelog']}[/dark_goldenrod][/bold]\n")
        logging.info(f"\t- {mod['Name']} (v{mod['Old_version']} to v{mod['New_version']})")

    # mod_updated_log.txt
    mod_updated_logger = config.configure_mod_updated_logging()

    for mod in global_cache.mods_data.get('mods_to_update', []):
        name_version = f"*** {mod['Name']} (v{mod['Old_version']} {lang.get_translation("to")} v{mod['New_version']}) ***"
        mod_updated_logger.info("================================")
        mod_updated_logger.info(name_version)
        if mod.get('Changelog'):
            # Formatage simple pour rendre le changelog lisible
            changelog = mod['Changelog']

            # Si tu veux organiser par section, tu peux ajouter des sauts de ligne ou autres
            changelog = changelog.replace("\n",
                                          "\n\t")  # Ajouter une tabulation pour chaque nouvelle ligne
            mod_updated_logger.info(f"Changelog:\n\t{changelog}")

        mod_updated_logger.info("\n\n")  # Ligne vide pour espacement


if __name__ == "__main__":
    pass
