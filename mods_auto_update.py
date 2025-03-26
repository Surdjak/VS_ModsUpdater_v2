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
__version__ = "2.0.0-dev2"
__date__ = "2025-03-26"  # Last update


# mods_auto_update.py


import datetime
import logging
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.progress import Progress

import global_cache
from http_client import HTTPClient
from utils import version_compare, check_excluded_mods, \
    setup_directories, extract_filename_from_url, calculate_max_workers

client = HTTPClient


def get_mods_to_update(mods_data):
    """
    Check for mods that need updates.

    - If Local_Version < mod_latest_version_for_game_version, the mod needs an update.
    - If the Filename is in excluded_mods, skip the mod.
    - Returns a list of mods that require updates.
    """
    # Extract filenames from excluded_mods to compare correctly
    excluded_filenames = [mod['Filename'] for mod in mods_data.get("excluded_mods", [])]
    logging.info(f"Excluded filenames: {excluded_filenames}")
    for mod in mods_data.get("installed_mods", []):
        try:
            # Log mod Filename to verify
            logging.info(f"Processing mod: {mod['Name']} - Filename: {mod['Filename']}")

            # Skip the mod if its Filename is in excluded_filenames
            check_excluded_mods()
            if mod['Filename'] in excluded_filenames:
                logging.info(f"Skipping excluded mod: {mod['Name']} - Filename: {mod['Filename']}")
                continue  # Skip this mod if it's in the excluded list
            # Proceed with the version comparison
            if mod.get("mod_latest_version_for_game_version"):
                mod_update = version_compare(mod["Local_Version"],
                                             mod["mod_latest_version_for_game_version"])
            else:
                mod_update = False
            if mod_update:
                mods_data["mods_to_update"].append({
                    "Name": mod['Name'],
                    "New_version": mod['mod_latest_version_for_game_version'],
                    "Filename": mod['Filename'],
                    "url_download": mod['Latest_version_mod_url']})

        except ValueError:
            # Skip mods with invalid version formats
            logging.warning(f"Invalid version format for mod: {mod['Name']}")
            continue


def backup_mods(mods_to_backup):
    """
    Create a backup of the ZIP mods before download and manage a retention policy.
    """
    max_backups = int(global_cache.config_cache['Backup_Mods']['max_backups'])
    backup_folder_name = global_cache.config_cache['Backup_Mods']['backup_folder']
    backup_folder = (Path(global_cache.config_cache['APPLICATION_PATH']) / backup_folder_name).resolve()

    # Ensure the backup directory exists
    setup_directories(backup_folder)

    # Create a unique backup name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_folder / f"backup_{timestamp}.zip"

    modspaths = global_cache.config_cache['ModsPath']['path']

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


def download_file(url, destination_path, progress_bar, task):
    """
    Download the file from the given URL and save it to the destination path with a progress bar using Rich.
    Implements error handling and additional security measures.
    """
    response = client.get(url, stream=True, timeout=10)  # Increased timeout to 10 seconds
    response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx, 5xx)

    # Get the total size of the file (if available)
    total_size = int(response.headers.get('content-length', 0))

    if total_size == 0:
        print("[bold red]Warning: The file size is unknown or zero. Download may not complete properly.[/bold red]")

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
        task = progress.add_task("[cyan]Downloading mods...", total=len(mods_data))

        # Create a thread pool executor for parallel downloads
        max_workers = calculate_max_workers()
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

                # Update the progress for each mod with mod name or file name
                mod_name = mod['Name']  # Get the mod name from the data
                progress.update(task, advance=1, description=f"[cyan]Downloading {mod_name}")

            # Wait for all downloads to finish
            for future in futures:
                future.result()  # This will raise an exception if something went wrong


def resume_mods_updated():
    print(f"\nFollowings mods have been updated:")
    logging.info("Followings mods have been updated:")
    for mod in global_cache.mods_data.get('mods_to_update'):
        print(f"\t- {mod['Name']} to v{mod['New_version']}")
        logging.info(f"\t{mod['Name']} to v{mod['New_version']}")


if __name__ == "__main__":
    pass
