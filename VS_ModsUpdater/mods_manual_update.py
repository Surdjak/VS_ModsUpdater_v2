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

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-21"  # Last update

# mods_manual_update.py

import mods_common_update

print('Manual Update')


def manual_update():
    mods_to_update = mods_common_update.check_mod_to_update()  # Identifie les mods à mettre à jour
    for mod_name, (game_version, local_version, mod_last_version, mod_asset_id) in mods_to_update.items():
        print(f"Mod: {mod_name}")
        mod_data = mods_common_update.get_mod_api_data(mod_name)
        changelog = mod_data.get('mod', {}).get('changelog', 'No changelog available.')

        print(f"Changelog: {changelog}")
        user_choice = input(f"Do you want to update {mod_name}? (yes/no): ")
        if user_choice.lower() == 'yes':
            mod_url = mods_common_update.url_mod_to_dl(mod_name)
            if mod_url:
                print(f"Downloading {mod_name}...")
                # Code pour télécharger et installer le mod
