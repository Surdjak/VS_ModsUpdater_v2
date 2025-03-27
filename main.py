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

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__license__ = "GNU GPL v3"
__description__ = "Mods Updater for Vintage Story"
__date__ = "2025-03-27"  # Last update


# main.py


import ctypes
import logging
import os
import sys
from pathlib import Path

from rich import print
from rich.console import Console
from rich.prompt import Prompt
import json_export

import config
import fetch_mod_info
import global_cache
import lang
import mods_auto_update
import utils
from utils import exit_program

console = Console()


ctypes.windll.kernel32.SetConsoleTitleW("VS Mods Updater")


def initialize_config():
    # Create config.ini if not present
    if not config.config_exists():
        # Config logging with log_level 'INFO' for the first execution.
        config.configure_logging('INFO')
        print(f'\n\t[yellow]First run detected - Set up config.ini -[/yellow]')
        language = config.ask_language_choice()
        # Load translations
        path = Path(f'{config.LANG_PATH}/{language[0]}.json').resolve()
        cache_lang = lang.load_translations(path)
        mods_dir = config.ask_mods_directory()
        user_game_version = config.ask_game_version()
        auto_update = 'True'
        print(f"\n{cache_lang['first_launch_language']}{language[1]}")
        print(f"{cache_lang['first_launch_mods_location']}{mods_dir}")
        print(f"{cache_lang['first_launch_game_version']}{user_game_version}")
        if auto_update.lower() == 'manual':
            choice_update = cache_lang['first_launch_manual_update']
        else:
            choice_update = cache_lang['first_launch_auto_update']
        print(f"{cache_lang['first_launch_set_update']}{choice_update}")

        # Create the config.ini file
        config.create_config(language, mods_dir, user_game_version, auto_update)
        print(f"\n{cache_lang['first_launch_config_created']}")

        # Ask for going on or exit to modify config.ini (e.g. add some mods to exception.)
        print(global_cache.language_cache["first_launch_confirms_update_info"])
        while True:
            user_confirms_update = Prompt.ask(
                global_cache.language_cache["first_launch_confirms_update"],
                choices=[global_cache.language_cache['yes'][0],
                         global_cache.language_cache['no'][0]], default=global_cache.language_cache['no'][0]
            )
            user_confirms_update = user_confirms_update.strip().lower()

            if user_confirms_update == global_cache.language_cache["yes"][0].lower():
                break
            elif user_confirms_update == global_cache.language_cache["no"][0].lower():
                print(global_cache.language_cache["exiting_program"])
                exit_program(extra_msg="User chose to exit the update process.")

            else:
                pass

    config.migrate_config_if_needed()

    # Load the configuration into the global cache
    config.load_config()

    # Configure the logging
    config.configure_logging(
        global_cache.config_cache["Logging"]['log_level'].upper())

    # Load the language translations from the config file into the global cache
    lang_path = Path(f"{config.LANG_PATH}/{global_cache.config_cache['Language']['language']}.json").resolve()
    global_cache.language_cache.update(lang.load_translations(lang_path))


def welcome_display():
    # look for script update
    new_version, urlscript, latest_version = mu_script_update.modsupdater_update()
    if new_version:
        text_script_new_version = f'[red]- {global_cache.language_cache["title_new_version"]} -[/red]\n{urlscript} -'
        logging.info(f"Latest version: {latest_version} | Download: {urlscript}")
    else:
        text_script_new_version = f'[bold cyan]- {global_cache.language_cache["title_no_new_version"]} - [/bold cyan]'
        logging.info(f"ModsUpdater - No new version")
    # to center text
    try:
        column, row = os.get_terminal_size()
    except OSError:
        column, row = 300, 50  # Default values
    txt_title = f'\n\n[bold cyan]{global_cache.language_cache["title_modsupdater_title"].format(mu_ver=__version__)}[/bold cyan]'

    lines = txt_title.splitlines() + text_script_new_version.splitlines()
    for line in lines:
        console.print(line.center(column), justify='center')


if __name__ == "__main__":
    # Initialize config
    initialize_config()

    import mu_script_update
    welcome_display()
    print("\n\n")

    mods_path = fetch_mod_info.get_mod_path()
    # Check if the 'Mods' folder is not empty and contains only archive files, not extracted archive folders.
    utils.check_mods_directory(mods_path)
    # Fetch mods info
    fetch_mod_info.scan_and_fetch_mod_info(mods_path)
    # print(f"installed_mods: {global_cache.mods_data['installed_mods']}")  # debug

    # Auto update mods
    mods_auto_update.get_mods_to_update(global_cache.mods_data)

    # Backup mods before Download
    if global_cache.mods_data.get('mods_to_update'):
        mods_to_backup = [mod['Filename'] for mod in global_cache.mods_data.get('mods_to_update', [])]
        mods_auto_update.backup_mods(mods_to_backup)

        # Download Mods
        mods_to_download = global_cache.mods_data.get('mods_to_update', [])
        mods_auto_update.download_mods_to_update(mods_to_download)

        # Display mods updated
        mods_auto_update.resume_mods_updated()
    else:
        print(f"No updates needed for mods.")
        logging.info("No updates needed for mods.")

    print(f"\nAll of your mods are up to date.\n")

    # Modlist creation
    json_export.format_mods_data(global_cache.mods_data['installed_mods'])
    print(f"A modlist has been exported in JSON format to the following location: {global_cache.config_cache['Backup_Mods']['modlist_folder']}")

    # End of programm
    exit_program(extra_msg="", do_exit=False)
    input("\nPress Enter to exit...")
    sys.exit()
