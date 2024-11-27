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

import logging
import mods_common_update
from rich import print

print(f'\n\t[yellow]Auto Update[/yellow]')


def auto_update():
    mods_common_update.backup_mods()
    logging.info('Starting update check for mods.')
    mods_to_update = mods_common_update.check_mod_to_update()  # Identify the mods to update.
    for mod_name, (game_version, local_version, mod_last_version, mod_asset_id, mod_filename) in mods_to_update.items():
        mod_url = mods_common_update.url_mod_to_dl(mod_filename)[1]
        mod_version = mods_common_update.url_mod_to_dl(mod_filename)[2]
        print(f'{mod_name}: {local_version} -> {mod_version}')  # debug
        log = mods_common_update.get_changelog(mod_asset_id)
        if mod_url:
            print(log)
            print(f"Downloading {mod_name}... {mod_url}\n")  # debug
            # Code to download and install the mod
            logging.info(f'"{mod_name}" downloaded ({local_version} -> {mod_version}).')
    logging.info('Mods update done.')
    return


if __name__ == "__main__":
    mods_common_update.get_changelog(7214)
    auto_update()
