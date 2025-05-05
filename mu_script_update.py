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
This module is designed to check for updates to the ModsUpdater script itself by comparing the current version with the latest version available on ModDB. It fetches and parses the relevant webpage to extract version information and download URLs.

Key functionalities include:
- Determining the correct update URL based on the operating system.
- Fetching and parsing the ModDB page using BeautifulSoup to locate version information and download links.
- Extracting the latest version number and download URL from the HTML content.
- Comparing the current script version with the latest available version.
- Returning a boolean indicating whether an update is available, along with the download URL and latest version.
- Handling potential network errors and HTML parsing issues, with appropriate logging.

"""

__author__ = "Laerinok"
__version__ = "2.1.3"
__date__ = "2025-04-27"  # Last update

# mu_script_update.py

import logging
import re

from bs4 import BeautifulSoup

import config
import global_cache
import utils
from http_client import HTTPClient


logging.info(f'OS: {config.SYSTEM} - ModsUpdater v{__version__}')
logging.info(f"For Vintage Story v{global_cache.config_cache['Game_Version']['user_game_version']}")
logging.info(f'Checking for ModsUpdater script update')

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()


def modsupdater_update():
    """Fetch and parse the page for the update script, handling errors."""
    system = config.SYSTEM.lower()
    url_script = config.URL_SCRIPT[system]

    # Fetch the URL with a randomized User-Agent and timeout
    response = client.get(url_script, timeout=int(global_cache.config_cache["Options"]["timeout"]))
    response.raise_for_status()  # Check if the request was successful

    # Check if content indicates page not found
    if response.status_code == 404:
        logging.error("Page not found (404) for URL: %s", url_script)
        return None, None, None

    soup = BeautifulSoup(response.content, "html.parser")

    # Find the first table row
    first_row = soup.select_one("table.stdtable tbody tr")
    if not first_row:
        logging.error("Could not find the update table row on URL: %s", url_script)
        return None, None, None

    # Extract version and download URL
    version_text = first_row.select_one("td:nth-of-type(1)").text.strip()
    match = re.search(r'v\d+\.\d+\.\d+', version_text)

    latest_version = match.group(0) if match else None
    download_link = first_row.select_one("td:nth-of-type(6) a.downloadbutton")
    download_url = f"{config.URL_BASE_MODS}{download_link['href'][1:]}" if download_link else None

    # Ensure both version and download URL are found
    if not latest_version or not download_url:
        logging.error("Failed to extract version or download URL for URL: %s", url_script)
        return None, None, None

    # Compare with the current version
    new_version = utils.version_compare(__version__, latest_version)

    return new_version, download_url, latest_version


if __name__ == "__main__":  # For test
    pass
