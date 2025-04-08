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
__version__ = "2.0.2"
__license__ = "GNU GPL v3"
__description__ = "Mods Updater for Vintage Story"
__date__ = "2025-04-06"  # Last update


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
from rich.style import Style
from rich.text import Text

import cli
import config
import export_json
import export_pdf
import fetch_mod_info
import global_cache
import lang
import mods_auto_update
import mods_manual_update
import mods_update_checker

console = Console()


def set_console_title(title):
    """Sets the console title if running on Windows"""
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleW(title)


def initialize_config():
    # Create config.ini if not present
    if not config.config_exists():
        print(f'\n\t[dark_goldenrod]First run detected - Set up config.ini -[/dark_goldenrod]\n')
        # Configure logging with log_level 'DEBUG' for the first run.
        config.configure_logging('DEBUG')
        language = config.ask_language_choice()
        # Load translations for the chosen language
        lang_path = Path(f"{config.LANG_PATH}/{language[0]}.json").resolve()
        language_cache = lang.load_translations(lang_path)

        mods_dir = config.ask_mods_directory()
        user_game_version = config.ask_game_version()
        auto_update = config.ask_auto_update()

        print(f"\n- {language_cache["main_language_set_to"]}[dodger_blue1]{language[1]}[/dodger_blue1]")
        print(f"- {language_cache["main_mods_folder_path"]}[dodger_blue1]{mods_dir}[/dodger_blue1]")
        print(f"- {language_cache["main_game_version"]}[dodger_blue1]{user_game_version}[/dodger_blue1]")
        auto_update_choice = lang.get_translation("config_choose_update_mode_auto") if auto_update else lang.get_translation("config_choose_update_mode_manual")
        print(f"- {language_cache["main_mods_update_choice"]}[dodger_blue1]{auto_update_choice}[/dodger_blue1]")

        # Create config.ini file
        config.create_config(language, mods_dir, user_game_version, auto_update)
        print(f"\n{language_cache["main_config_file_created"]}")

        # Ask if we continue or quit to modify config.ini (e.g., to add mods to the exception list.)
        print(f"{language_cache["main_update_or_modify_config"]}")
        while True:
            user_confirms_update = Prompt.ask(
                f"{language_cache["main_continue_update_prompt"]}",
                choices=[global_cache.language_cache["yes"][0], global_cache.language_cache["no"][0]], default=global_cache.language_cache["no"][0])
            user_confirms_update = user_confirms_update.strip().lower()

            if user_confirms_update == global_cache.language_cache["yes"][0].lower():
                break
            elif user_confirms_update == global_cache.language_cache["no"][0].lower():
                print(f"{language_cache["main_exiting_program"]}")
                utils.exit_program(extra_msg=f"{lang.get_translation("main_user_exits")}")

            else:
                pass

    migration_performed = config.migrate_config_if_needed()

    # Load the configuration into the global cache
    config.load_config()

    # Configure the logging
    log_level = args.log_level or global_cache.config_cache["Logging"]["log_level"]
    config.configure_logging(log_level.upper())

    # Load the language translations from the config file into the global cache
    lang_path = Path(f"{config.LANG_PATH}/{global_cache.config_cache['Language']['language']}.json").resolve()
    global_cache.language_cache.update(lang.load_translations(lang_path))

    if migration_performed:
        print(f"[dark_goldenrod]{lang.get_translation("config_configuration_migrated").format(EXPECTED_VERSION=config.EXPECTED_VERSION)}[/dark_goldenrod]")


def welcome_display():
    """Displays the welcome message centered in the console."""

    # Checks for script updates
    new_version, urlscript, latest_version = mu_script_update.modsupdater_update()
    if new_version:
        text_script_new_version = f'[indian_red1]- {lang.get_translation("main_new_version_available")} -[/indian_red1]\n{urlscript} -'
        logging.info(f"Latest version: {latest_version} | Download: {urlscript}")
    else:
        text_script_new_version = f'[dodger_blue1]- {lang.get_translation("main_no_new_version_available")} - [/dodger_blue1]'
        logging.info("ModsUpdater - No new version")

        # Gets the console width
        try:
            column, _ = os.get_terminal_size()
        except OSError:
            column = 80  # Default value if console size cannot be determined

        # Creates and centers the title
        txt_title = f'\n\n[dodger_blue1]{lang.get_translation("main_title").format(ModsUpdater_version=__version__)}[/dodger_blue1]'
        lines = txt_title.splitlines() + text_script_new_version.splitlines()

        # Displays the centered lines
        for line in lines:
            console.print(line.center(column))

        # main_max_game_version
        print(f'\n\n\t\t\t[dodger_blue1]{lang.get_translation("main_max_game_version")}{global_cache.config_cache['Game_Version']['user_game_version']}[/dodger_blue1]')


if __name__ == "__main__":
    args = cli.parse_args()

    import utils

    # Initialize config
    initialize_config()
    set_console_title(lang.get_translation("main_title").format(ModsUpdater_version=__version__))

    import mu_script_update
    welcome_display()
    print("\n\n")

    mods_path = fetch_mod_info.get_mod_path()

    if args.modspath:  # use the argument modspath if present.
        mods_path = args.modspath

    # Check if the 'Mods' folder is not empty and contains only archive files, not extracted archive folders.

    utils.check_mods_directory(mods_path)
    # Fetch mods info
    fetch_mod_info.scan_and_fetch_mod_info(mods_path)

    # Mods update checker
    mods_update_checker.check_for_mod_updates()

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
            print(lang.get_translation("main_mods_no_update"))
            logging.info("No updates needed for mods.")
    else:
        # Manual update mods
        if global_cache.mods_data.get('mods_to_update'):
            # Backup mods before update
            mods_to_backup = [mod['Filename'] for mod in global_cache.mods_data.get('mods_to_update', [])]
            utils.backup_mods(mods_to_backup)
            # Download Mods
            mods_manual_update.perform_manual_updates(global_cache.mods_data['mods_to_update'])

        else:
            print(lang.get_translation("main_mods_no_update"))
            logging.info("No updates needed for mods.")

    # Modlist creation
    # args.no-json handled in export_json
    export_json.format_mods_data(global_cache.mods_data['installed_mods'])

    # PDF creation
    if not args.no_pdf:
        export_pdf.generate_pdf(global_cache.mods_data['installed_mods'])

    # HTML modlist export
    # export_html.format_mods_html_data(global_cache.mods_data['installed_mods'])

    excluded_mods = global_cache.mods_data.get('excluded_mods', [])

    if excluded_mods:
        excluded_title_style = Style(color="dark_goldenrod", bold=True)
        excluded_mod_style = Style(color="indian_red1")

        print(Text(f"\n{lang.get_translation('main_excluded_mods_title')}",
                   style=excluded_title_style))
        for mod in excluded_mods:
            mod_name = mod.get('Name', mod.get('Filename', 'Unknown name'))
            print(Text(f"- {mod_name}", style=excluded_mod_style))
        print()
    else:
        logging.info("No mods were found in the exclusion list.")

    # display logs path
    log_file_path = global_cache.config_cache.get('LOGS_PATH')
    if log_file_path:
        print(
            f"[dodger_blue1]{lang.get_translation('main_logs_location')}[/dodger_blue1]\n[green]{log_file_path}[/green]\n")
    else:
        logging.warning("Could not retrieve logs path from global cache.")
        print(f"\n{lang.get_translation('main_logs_location_error')}\n")

    # End of programm
    utils.exit_program(extra_msg="", do_exit=False)
    if not args.no_pause:
        input(f"\n{lang.get_translation("main_press_enter_to_exit")}")
    sys.exit()
