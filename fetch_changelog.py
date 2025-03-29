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
# Manage configuration using a global cache.
"""

# fetch_changelog.py


__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__date__ = "2025-03-26"  # Last update

import logging
import global_cache
import html2text
from bs4 import BeautifulSoup

import config
from http_client import HTTPClient

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient(timeout=timeout)


def convert_html_to_markdown(html_content):
    """
    Convert HTML content to Markdown.
    """
    converter = html2text.HTML2Text()
    converter.ignore_links = False  # Keep links
    converter.ignore_images = False  # Keep images
    converter.body_width = 0  # Prevent forced line breaks
    return converter.handle(html_content)


def get_raw_changelog(modname, mod_assetid, modversion):
    """
    Retrieve raw changelog from modDB for a specific mod version.
    Converts the changelog to Markdown.
    """
    logging.debug(f"Attempting to fetch changelog for mod '{modname}' (version {modversion}) from modDB.")
    mod_url_api = f'{config.URL_MOD_DB}{mod_assetid}'
    logging.debug(f"Retrieving changelog from: {mod_url_api}")

    response = client.get(mod_url_api, timeout=int(global_cache.config_cache["Options"]["timeout"]))
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all divs containing changelogs
    changelog_divs = soup.find_all("div", class_="changelogtext")

    # Clean modversion (remove spaces, lowercase, ensure it starts with 'v')
    clean_modversion = modversion.strip().lower()
    if not clean_modversion.startswith('v'):
        clean_modversion = 'v' + clean_modversion  # Ensure version starts with 'v'

    for div in changelog_divs:
        # Extract version (inside <strong>)
        version_tag = div.find("strong")
        version = version_tag.text.strip().lower() if version_tag else "unknown version"

        # Check if this version matches modversion
        if version == clean_modversion:
            # Remove the version tag from the changelog content
            version_tag.extract()

            # Extract the raw changelog text
            changelog_text = div.encode_contents().decode()  # Keep raw HTML
            changelog_markdown = convert_html_to_markdown(changelog_text)

            return changelog_markdown.strip()  # Return Markdown version

    logging.debug(f"{modname}: No changelog found for version {modversion}")
    return None


if __name__ == "__main__":
    pass
