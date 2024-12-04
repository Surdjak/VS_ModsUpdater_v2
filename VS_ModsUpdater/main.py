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
    -> arguments pour ligne de commande
    -> test linux
    -> manual update
"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-12-04"  # Last update


# main.py

import config
import lang
import global_cache
from utils import exit_program
from rich import print
from rich.console import Console
from rich.prompt import Prompt
from pathlib import Path
import os


console = Console()


def initialize_config():
    # Create config.ini if not present
    if not config.config_exists():
        # Config logging with log_level 'INFO' for the first execution.
        config.configure_logging('INFO')
        print(f'\n\t[yellow]First run detected - Set up config.ini -[/yellow]')
        language = config.ask_language_choice()
        # Load translations
        path = Path(f'{config.LANG_PATH}/{language[0]}.json')
        cache_lang = lang.load_translations(path)

        mods_dir = config.ask_mods_directory()
        game_version = config.ask_game_version()
        auto_update = config.ask_auto_update()
        print(f"\n{cache_lang['first_launch_language']}{language[1]}")
        print(f"{cache_lang['first_launch_mods_location']}{mods_dir}")
        print(f"{cache_lang['first_launch_game_version']}{game_version}")
        if auto_update.lower() == 'manual':
            choice_update = cache_lang['first_launch_manual_update']
        else:
            choice_update = cache_lang['first_launch_auto_update']
        print(f"{cache_lang['first_launch_set_update']}{choice_update}")

        # Create the config.ini file
        config.create_config(language, mods_dir, game_version, auto_update)
        print(f"\n{cache_lang['first_launch_config_created']}")

        # Ask for going on or exit to modify config.ini (e.g. add some mods to exception.)
        print(global_cache.global_cache.language_cache["first_launch_confirms_update_info"])
        while True:
            user_confirms_update = Prompt.ask(
                global_cache.global_cache.language_cache["first_launch_confirms_update"],
                default=global_cache.global_cache.language_cache["yes"]
            )
            user_confirms_update = user_confirms_update.strip().lower()

            if user_confirms_update == global_cache.global_cache.language_cache["yes"].lower():
                return
            elif user_confirms_update == global_cache.global_cache.language_cache["no"].lower():
                print(global_cache.global_cache.language_cache["exiting_program"])
                exit_program()

            else:
                pass

    config.migrate_config_if_needed()

    # Update the global cache with the config settings
    global_cache.global_cache.config_cache.update(config.load_config())

    # Configure the logging
    config.configure_logging(global_cache.global_cache.config_cache["Logging"]['log_level'].upper())

    # Load the language translations from the config file into the global cache
    lang_path = Path(f"{config.LANG_PATH}/{global_cache.global_cache.config_cache['Language']['language']}.json")
    global_cache.global_cache.language_cache.update(lang.load_translations(lang_path))

    return global_cache.global_cache.language_cache


def welcome_display():
    # look for script update
    new_version, urlscript = mu_script_update.fetch_page()
    if new_version:
        text_script_new_version = f'[red]- {global_cache.global_cache.language_cache["title_new_version"]} -[/red]\n{urlscript} -'
    else:
        text_script_new_version = f'[bold cyan]- {global_cache.global_cache.language_cache["title_no_new_version"]} - [/bold cyan]'
    # to center text
    try:
        column, row = os.get_terminal_size()
    except OSError:
        column, row = 300, 50  # Default values
    txt_title = f'\n\n[bold cyan]{global_cache.global_cache.language_cache["title_modsupdater_title"].format(mu_ver=__version__)}[/bold cyan]'

    lines = txt_title.splitlines() + text_script_new_version.splitlines()
    for line in lines:
        console.print(line.center(column), justify='center')


if __name__ == "__main__":
    # Initialize config before calling mods update
    initialize_config()
    import mu_script_update
    welcome_display()

    if global_cache.global_cache.config_cache['Options']['auto_update']:
        import mods_auto_update  # noqa: F401 - Used for its side effects

    else:
        import mods_manual_update  # noqa: F401 - Used for its side effects

    # Ask for pdf creation
    import pdf_creation  # noqa: F401 - Used for its side effects
    mods_data = global_cache.global_cache.mods
    pdf_creation.generate_mod_pdf(mods_data)

    # tests
