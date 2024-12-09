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

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
import logging
import requests
from rich import print
from rich.progress import Progress, BarColumn, FileSizeColumn

import config
import global_cache
import mods_common_update

config.load_config()
config.configure_logging(
    global_cache.global_cache.config_cache["Logging"]['log_level'].upper())

VS_version = global_cache.global_cache.config_cache['Game_Version']['version']
print(
    f'\n\t[yellow]{global_cache.global_cache.language_cache["auto_update_title"].format(VS_version=VS_version)}\n[/yellow]'
)


def download_mod(mod, url, modspaths):
    """
    Download a mod from a given URL and save it to the specified path.
    """
    modname = global_cache.global_cache.mods[mod]['name']
    modversion = global_cache.global_cache.mods[mod]['modversion']
    parsed_url = urlparse(url)
    file_name = Path(parsed_url.path).name
    save_path = Path(modspaths) / file_name

    # Delete obsolete files
    for file in Path(modspaths).glob(f"{mod}*"):
        if file != save_path:
            try:
                file.unlink()
                logging.info(f"Deleted obsolete file: {file}")
            except Exception as e:
                logging.error(f"Failed to delete obsolete file {file}: {e}")

    try:
        resp = requests.get(url, stream=True, timeout=10)
        resp.raise_for_status()
        file_size = int(resp.headers.get("Content-length", 0)) / (1024 ** 2)
        logging.info(f"Downloading {modname} (v{modversion}) - Size: {file_size:.2f} MB.")

        if save_path.exists():
            save_path.unlink()
            logging.info(f"Deleted old version of {modname} from {save_path}.")

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        logging.info(f"Successfully downloaded {modname} to {save_path}.")
    except Exception as e:
        logging.error(f"Error during download of {modname}: {e}")
        raise


def auto_download_parallel():
    """
    Download mods in parallel, showing progress bars.
    """
    max_workers = int(global_cache.global_cache.config_cache['Options']['max_workers'])
    modspaths = Path(global_cache.global_cache.config_cache['ModsPath']['path'])

    logging.info("Starting parallel download process for mods.")

    # Setup progress bar
    with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3}%",
            FileSizeColumn(),
            transient=False,
    ) as progress:
        download_task = progress.add_task(f"[cyan]{global_cache.global_cache.language_cache['auto_update_download_in_progress']}", total=len(mods_to_update), mod_name="")

        # ThreadPool for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(download_mod, mod, url, modspaths): mod
                for mod, url in mods_to_update.items()
            }

            for future in futures:
                mod = futures[future]
                try:
                    future.result()  # Wait for completion
                    progress.update(download_task, advance=1, mod_name=mod)
                except Exception as e:
                    mod = futures[future]
                    logging.error(f"Failed to download mod {mod} : {e}\n")


# Update mod_cache info
mods_common_update.update_mod_cache_with_api_ata()

# Load mods exclusion
excluded_mods = mods_common_update.load_mods_exclusion()
# Look for mods to update
mods_to_update = mods_common_update.check_mod_to_update()
# Filter mods to update
mods_to_update = {mod: url for mod, url in mods_to_update.items() if mod not in excluded_mods}


# Download Mods in Parallel
if len(mods_to_update) > 0:
    print(f"\n{global_cache.global_cache.language_cache['auto_update_following_mods']}")
    for key in mods_to_update:
        print(
            f"\t- {global_cache.global_cache.mods[key]['name']} ({global_cache.global_cache.mods[key]['local_version']} -> {global_cache.global_cache.mods[key]['modversion']})")
    print("\n")
    # Backup mods before Download
    mods_common_update.backup_mods(mods_to_update)
    auto_download_parallel()
else:
    print(f"{global_cache.global_cache.language_cache['auto_update_no_download']}\n")

if __name__ == "__main__":
    pass
