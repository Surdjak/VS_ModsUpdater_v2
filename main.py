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
This module serves as the main entry point for the Vintage Story Mods Updater application. It orchestrates the entire process of initializing the application, scanning for installed mods, checking for updates, backing up and downloading mods, and generating mod lists in JSON and PDF formats.

Key functionalities include:
- Initializing the application by loading configuration settings and language translations.
- Displaying a welcome message with version information and update status of the script itself.
- Scanning the specified mods directory to gather information about installed mods.
- Fetching mod information from local files and online API.
- Automatically checking for and downloading mod updates.
- Backing up mods before updating to prevent data loss.
- Generating mod lists in JSON and PDF formats for easy sharing and documentation.
- Providing user-friendly output and logging for debugging and information purposes.
- Handling potential errors and exceptions gracefully.
- Exiting the program with an informative message.

"""
__author__ = "Laerinok"
__version__ = "2.0.1-rc2"
__license__ = "GNU GPL v3"
__description__ = "Mods Updater for Vintage Story"
__date__ = "2025-04-02"  # Last update


# main.py


import ctypes
import logging
import os
import platform
import sys
from pathlib import Path

from rich import print
from rich.console import Console
from rich.prompt import Prompt

import config
import export_json
import export_pdf
import fetch_mod_info
import global_cache
import lang
import mods_auto_update
import mods_manual_update
import mods_update_checker
import utils
from utils import exit_program

console = Console()


def set_console_title(title):
    """Sets the console title if running on Windows"""
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleW(title)


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
        auto_update = config.ask_auto_update()
        print(f"\n{cache_lang['first_launch_language']}{language[1]}")
        print(f"{cache_lang['first_launch_mods_location']}{mods_dir}")
        print(f"{cache_lang['first_launch_game_version']}{user_game_version}")
        auto_update_choic = "Auto" if auto_update else "Manual"
        print(f"Mods update: {auto_update_choic}")

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
    set_console_title(f"ModsUpdater for Vintage Story {__version__} (by Laerinok)")

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

    # Mods update checker
    mods_update_checker.check_for_mod_updates()
    # print(f"mods_to_update: {global_cache.mods_data["mods_to_update"]}")  # Debug
    # print(global_cache.mods_data["excluded_mods"])  # Debug

    # Choice for auto/manual update
    auto_update_str = global_cache.config_cache['Options']['auto_update']
    auto_update_cfg = auto_update_str.lower() == 'true'

    # Download
    if auto_update_cfg:
        # Auto update mods
        if global_cache.mods_data.get('mods_to_update'):
            # Backup mods before update
            mods_to_backup = [mod['Filename'] for mod in global_cache.mods_data.get('mods_to_update', [])]
            utils.backup_mods(mods_to_backup)
            # Download Mods
            mods_to_download = global_cache.mods_data.get('mods_to_update', [])
            mods_auto_update.download_mods_to_update(mods_to_download)

            # Display mods updated
            mods_auto_update.resume_mods_updated()
        else:
            print(f"No updates needed for mods.")
            logging.info("No updates needed for mods.")
    else:
        # Manual update mods
        if global_cache.mods_data.get('mods_to_update'):
            # Backup mods before update
            mods_to_backup = [mod['Filename'] for mod in global_cache.mods_data.get('mods_to_update', [])]
            utils.backup_mods(mods_to_backup)
            # Download Mods
            mods_manual_update.perform_manual_updates(global_cache.mods_data['mods_to_update'])

    # Modlist creation
    export_json.format_mods_data(global_cache.mods_data['installed_mods'])

    # PDF creation
    export_pdf.generate_pdf(global_cache.mods_data['installed_mods'])

    # End of programm
    exit_program(extra_msg="", do_exit=False)
    input("\nPress Enter to exit...")
    sys.exit()
