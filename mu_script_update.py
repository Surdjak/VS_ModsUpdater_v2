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
- Check for update of ModsUpdater on ModDB
"""

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2025-03-21"  # Last update

# mu_script_update.py

import logging
import re

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

import config
import utils
from global_cache import config_cache

# mu_script_update.py


logging.info(f'OS: {config.SYSTEM} - ModsUpdater v{__version__}')
logging.info(f"For Vintage Story v{config_cache['Game_Version']['version']}")
logging.info(f'Checking for ModsUpdater script update')


def modsupdater_update():
    """Fetch and parse the page for the update script, handling errors."""
    system = config.SYSTEM.lower()
    url_script = config.URL_SCRIPT[system]

    """Fetches the URL with a randomized User-Agent."""
    headers = utils.get_random_headers()

    try:
        response = requests.get(url_script, headers=headers, timeout=5)
        response.raise_for_status()
        page_content = response.content

        if 'not found' in response.text.lower():
            utils.log_error("Content indicates page not found.")
            return None, None

        soup = BeautifulSoup(page_content, "html.parser")

        # Récupérer la première ligne du tableau
        first_row = soup.select_one("table.stdtable tbody tr")
        if not first_row:
            utils.log_error("Could not find the update table row.")
            return None, None

        # Récupérer la version depuis la 1ʳᵉ colonne
        version_text = first_row.select_one("td:nth-of-type(1)").text.strip()
        # Récupérer la version avec une expression régulière
        match = re.search(r'v\d+\.\d+\.\d+', version_text)
        latest_version = match.group(0) if match else None

        # Récupérer le lien de téléchargement depuis la 6ᵉ colonne
        download_link = first_row.select_one("td:nth-of-type(6) a.downloadbutton")
        download_url = f"{config.URL_BASE_MODS}{download_link['href']}" if download_link else None

        if not latest_version or not download_url:
            utils.log_error("Failed to extract version or download URL.")
            return None, None

        # Comparer avec la version actuelle
        new_version = utils.version_compare(__version__, latest_version)

        # logging.info(f"Latest version: {latest_version} | Download: {download_url}")
        return new_version, download_url, latest_version

    except (RequestException, ValueError) as e:
        utils.log_error(f"Error accessing or parsing URL: {e}")
        return None, None


if __name__ == "__main__":  # For test
    pass
