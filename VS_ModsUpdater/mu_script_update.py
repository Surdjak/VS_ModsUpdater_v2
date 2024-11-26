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
- Check for new script on ModDB
"""

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-22"  # Last update

# mu_script_update.py

import global_cache
import config
import utils
import logging
import requests
from requests.exceptions import RequestException
import re
from bs4 import BeautifulSoup
from urllib.error import URLError, HTTPError

# mu_script_update.py

config.load_config()
# config.configure_logging()  debug
logging.info(f'OS: {global_cache.SYSTEM} - Checking for ModsUpdater update')


def fetch_page():
    """Fetch and parse the page for the update script, handling errors."""
    system = global_cache.SYSTEM.lower()
    url_script = global_cache.URL_SCRIPT[system]

    try:
        response = requests.get(url_script)
        response.raise_for_status()
        page_content = response.content
        if 'not found' in response.text.lower():
            utils.log_error("Content indicates page not found.")
            return None, None

        # Parsing page content for latest version and download URL
        soup = BeautifulSoup(page_content, features="html.parser")
        changelog = soup.find("div", {"class": "changelogtext"})
        download_link = soup.find("a", {"class": "downloadbutton"})

        # Retrieve version number from changelog
        latest_version = re.search('<strong>v(.*)</strong>', str(changelog))
        new_version = utils.version_compare(__version__, latest_version[1])
        url_script = f'{global_cache.URL_MODS}{download_link["href"]}'
        logging.info("Check for script update done.")
        return new_version, url_script

    except (URLError, HTTPError, RequestException) as e:
        utils.log_error(f"Error accessing URL: {e}")


if __name__ == "__main__":  # For test
    fetch_page()
    # pass
