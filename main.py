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
__version__ = "2.3.0"
__license__ = "GNU GPL v3"
__description__ = "Mods Updater for Vintage Story"
__date__ = "2025-08-26"  # Last update

# main.py


import ctypes
import logging
import platform
import sys
from pathlib import Path

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.text import Text

import cli
import config
import export_html
import export_json
import export_pdf
import fetch_mod_info
import global_cache
import lang
import mods_auto_update
import mods_install
import mods_manual_update
import mods_update_checker
from utils import exit_program

console = Console()


def set_console_title(title):
    """Sets the console title if running on Windows"""
    if platform.system() == 'Windows':
        # Ignore mypy type checking since SetConsoleTitleW is dynamic
        ctypes.windll.kernel32.SetConsoleTitleW(title)  # type: ignore


def initialize_config():
    # Create config.ini if not present
    if not config.config_exists():
        print(
            f'\n\t[dark_goldenrod]First run detected - Set up config.ini -[/dark_goldenrod]\n')
        # Configure logging with log_level 'DEBUG' for the first run.
        config.configure_logging('DEBUG')
        language = config.ask_language_choice()
        # Load translations for the chosen language
        lang_path = Path(f"{config.LANG_PATH}/{language[0]}.json").resolve()
        language_cache = lang.load_translations(lang_path)

        mods_dir = config.ask_mods_directory()
        user_game_version = config.ask_game_version()
        auto_update = config.ask_auto_update()

        print(
            f"\n- {language_cache['main_language_set_to']}[dodger_blue1]{language[1]}[/dodger_blue1]")
        print(
            f"- {language_cache['main_mods_folder_path']}[dodger_blue1]{mods_dir}[/dodger_blue1]")
        print(
            f"- {language_cache['main_game_version']}[dodger_blue1]{user_game_version}[/dodger_blue1]")
        auto_update_choice = lang.get_translation(
            "config_choose_update_mode_auto") if auto_update else lang.get_translation(
            "config_choose_update_mode_manual")
        print(
            f"- {language_cache['main_mods_update_choice']}[dodger_blue1]{auto_update_choice}[/dodger_blue1]")

        # Create config.ini file
        config.create_config(language, mods_dir, user_game_version, auto_update)
        print(f"\n{language_cache['main_config_file_created']}")

        # Ask if we continue or quit to modify config.ini (e.g., to add mods to the exception list.)
        print(f"{language_cache['main_update_or_modify_config']}")
        while True:
            user_confirms_update = Prompt.ask(
                f"{language_cache['main_continue_update_prompt']}",
                choices=[global_cache.language_cache["yes"][0],
                         global_cache.language_cache["no"][0]],
                default=global_cache.language_cache["no"][0])
            user_confirms_update = user_confirms_update.strip().lower()

            if user_confirms_update == global_cache.language_cache["yes"][0].lower():
                break
            elif user_confirms_update == global_cache.language_cache["no"][0].lower():
                print(f"{language_cache['main_exiting_program']}")
                utils.exit_program(
                    extra_msg=f"{lang.get_translation('main_user_exits')}")

            else:
                pass

    migration_performed = config.migrate_config_if_needed()

    # Load the configuration into the global cache
    config.load_config()

    # Configure the logging
    log_level = args.log_level or global_cache.config_cache["Logging"]["log_level"]
    config.configure_logging(log_level.upper())

    # Load the language translations from the config file into the global cache
    lang_path = Path(
        f"{config.LANG_PATH}/{global_cache.config_cache['Language']['language']}.json").resolve()
    global_cache.language_cache.update(lang.load_translations(lang_path))

    if migration_performed:
        print(
            f"[dark_goldenrod]{lang.get_translation('config_configuration_migrated').format(EXPECTED_VERSION=config.EXPECTED_VERSION)}[/dark_goldenrod]")


def welcome_display():
    """Displays the welcome message centered in the console."""

    # Checks for script updates
    new_version, urlscript, latest_version, changelog_text = mu_script_update.modsupdater_update()

    # Center the main title first
    title_text = f"\n\n[dodger_blue1]{lang.get_translation('main_title').format(ModsUpdater_version=__version__)}[/dodger_blue1]"
    console.print(title_text, justify="center")

    # Handles the update message and logs
    if new_version:
        # Log message with the full URL
        logging.info(f"Latest version: {latest_version} | Download: {urlscript}")

        # Display a simple message for the new version and a download link
        console.print(
            f'[indian_red1]- {lang.get_translation("main_new_version_available")} -[/indian_red1]',
            justify="center")
        console.print(
            f'[bold][link={urlscript}]Download v{latest_version}[/link][/bold]',
            justify="center")

        # Prompt the user to show the changelog
        show_changelog = Prompt.ask(
            f"\n{lang.get_translation('main_show_changelog_prompt')}",
            choices=["y", "n"],
            default="n"
        )

        if show_changelog.lower() == "y":
            changelog_panel = Panel(
                changelog_text,
                title=lang.get_translation("main_changelog_title"),
                border_style="dodger_blue1"
            )
            console.print(changelog_panel, justify="left")

    else:
        # Message for both log and display
        logging.info("ModsUpdater - No new version")

        text_script_new_version = f'[dodger_blue1]- {lang.get_translation("main_no_new_version_available")} - [/dodger_blue1]'
        console.print(text_script_new_version, justify="center")

    # main_max_game_version
    game_version_text = f'[dodger_blue1]{lang.get_translation("main_max_game_version")}{global_cache.config_cache["Game_Version"]["user_game_version"]}[/dodger_blue1]'
    console.print()  # Add a blank line
    console.print()  # Add another blank line
    console.print(game_version_text, justify="center")


if __name__ == "__main__":
    args = cli.parse_args()

    import utils

    # Initialize config
    initialize_config()
    set_console_title(
        lang.get_translation("main_title").format(ModsUpdater_version=__version__))

    import mu_script_update

    welcome_display()
    print("\n\n")

    mods_path = fetch_mod_info.get_mod_path()

    # Install from modlist.json
    if args.install_modlist:
        mods_install.main()
        exit_program()

    # Check if the 'Mods' folder is not empty and contains only archive files, not extracted archive folders.
    utils.check_mods_directory(mods_path)

    # Fetch mods info
    # fetch_mod_info.scan_and_fetch_mod_info(mods_path)
    mod_data = fetch_mod_info.scan_and_fetch_mod_info(mods_path)
    excluded_mods = mod_data['excluded_mods']

    # Check for updates and pass the --force-update flag
    mods_update_checker.check_for_mod_updates(args.force_update)

    # Choice for auto/manual update
    auto_update_str = global_cache.config_cache['Options']['auto_update']
    auto_update_cfg = auto_update_str.lower() == 'true'

    # Download
    if global_cache.mods_data.get('incompatible_mods'):
        # Handle incompatible mods
        print(f"[yellow]{global_cache.language_cache['main_incompatible_mods_found_without_update']}[/yellow]")
        for mod in global_cache.mods_data.get('incompatible_mods'):
            print(f"[yellow] - {mod['Name']} ({mod['Old_version'] + (' for game version ' + mod['Old_version_game_Version'] if mod['Old_version_game_Version'] else '')})[/yellow]")
        incompatibility_behavior = global_cache.config_cache.get("Incompatibility_behavior", 0)
        if incompatibility_behavior == 0:
            # Use Prompt.ask to get the user's input
            user_confirms_abort = Prompt.ask(
                f"{global_cache.language_cache['main_continue_anyway_prompt']}",
                choices=[global_cache.language_cache["yes"][0],
                         global_cache.language_cache["no"][0]],
                default=global_cache.language_cache["no"][0])
            user_confirms_abort = user_confirms_abort.strip().lower()
            if user_confirms_abort == global_cache.language_cache["no"][0].lower():
                exit_program()
        elif incompatibility_behavior == 1:
            print(f"[red]{global_cache.language_cache['main_aborting_due_to_incompatibility']}[/red]")
            if not args.no_pause:
                input(f"\n{global_cache.language_cache['main_press_enter_to_exit']}")
            sys.exit()
    if auto_update_cfg:
        # Auto update mods
        if global_cache.mods_data.get('mods_to_update'):
            # Backup mods before update
            mods_to_backup = [mod['Filename'] for mod in
                              global_cache.mods_data.get('mods_to_update', [])]
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
            mods_to_backup = [mod['Filename'] for mod in
                              global_cache.mods_data.get('mods_to_update', [])]
            utils.backup_mods(mods_to_backup)
            # Download Mods
            mods_manual_update.perform_manual_updates(
                global_cache.mods_data['mods_to_update'])

        else:
            print(lang.get_translation("main_mods_no_update"))
            logging.info("No updates needed for mods.")

    # Modlist creation
    # Generate JSON output of the installed mods data.
    # The export_json module will internally check for the --no-json argument when saving the file,
    # allowing it to manage its own logic for skipping the export if needed.
    export_json.format_mods_data(global_cache.mods_data['installed_mods'], args)

    # Generate a PDF report of the installed mods.
    # The export_pdf module will internally check for the --no-pdf argument when saving the file,
    # allowing it to manage its own logic for skipping the export if needed.
    export_pdf.generate_pdf(global_cache.mods_data['installed_mods'], args)

    # Generate an HTML report of the installed mods.
    if not args.no_html:
        export_html.export_mods_to_html()

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
        input(f"\n{lang.get_translation('main_press_enter_to_exit')}")
    sys.exit()
