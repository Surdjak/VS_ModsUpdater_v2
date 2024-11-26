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
Vintage Story mod management

TO do list:
- for new version installation:
    - check if a previous config.ini is present
    - retrieve previous config to set the new config
    - rename config.ini to config_01.back
"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-21"  # Last update

# main.py

import config
import lang
import global_cache
from rich import print
from rich.console import Console
from pathlib import Path
import os


console = Console()


def initialize_config():
    # Create config.ini if not present
    if not config.config_exists():
        print(f'\n\t[yellow]First run detected - Set up config.ini -[/yellow]')
        language = config.ask_language_choice()
        # Load translations
        path = Path(f'{global_cache.LANG_PATH}/{language[0]}.json')
        cache_lang = lang.load_translations(path)
        mods_dir = config.ask_mods_directory()
        game_version = config.ask_game_version()
        auto_update = config.ask_auto_update()
        print(f'\n{cache_lang['first_launch_language']}{language[1]}')
        print(f'{cache_lang['first_launch_mods_location']}{mods_dir}')
        print(f'{cache_lang['first_launch_game_version']}{game_version}')
        if auto_update.lower() == 'manual':
            choice_update = cache_lang['first_launch_manual_update']
        else:
            choice_update = cache_lang['first_launch_auto_update']
        print(f'{cache_lang['first_launch_set_update']}{choice_update}')
        # Create the config.ini file
        config.create_config(language, mods_dir, game_version, auto_update)
        print(f"\n{cache_lang['first_launch_config_created']}")
    global_cache.config_cache.update(config.load_config())
    # Configure the logging
    config.configure_logging()
    # Load the language translations from the config file
    lang_path = Path(f"{global_cache.LANG_PATH}/{global_cache.config_cache['Language']['language']}.json")
    global_cache.language_cache.update(lang.load_translations(lang_path))

    return global_cache.language_cache


def welcome_display():
    # Initialize config and load translations
    # look for script update
    new_version, urlscript = mu_script_update.fetch_page()
    if new_version:
        text_script_new_version = f'[red]- {cachelang["title_new_version"]} -[/red]\n{urlscript} -'
    else:
        text_script_new_version = f'[bold cyan]- {cachelang["title_no_new_version"]} - [/bold cyan]'
    # to center text
    try:
        column, row = os.get_terminal_size()
    except OSError:
        column, row = 300, 50  # Default values
    txt_title = f'\n\n[bold cyan]{cachelang["title_modsupdater_title"].format(mu_ver=__version__)}[/bold cyan]'

    lines = txt_title.splitlines() + text_script_new_version.splitlines()
    for line in lines:
        console.print(line.center(column), justify='center')


if __name__ == "__main__":
    # Initialize config before calling mods_common_update
    cachelang = initialize_config()
    import mu_script_update
    import mods_common_update

    welcome_display()
    # print(mods_common_update.check_mod_update())
    # print(mods_common_update.mod_dic_sorted)
    # print(mods_common_update.url_mod_to_dl('ExtraInfo-v1.8.0.zip'))
    mods_common_update.backup_mods()
