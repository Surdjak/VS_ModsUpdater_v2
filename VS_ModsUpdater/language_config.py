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


"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-08"  # Last update

# language_config.py

import json
import config
from pathlib import Path
from rich import print
from rich.prompt import Prompt

translations_cache = {}


def get_language_setting():
    """Retrieve the language setting from the configuration."""
    config_obj = config.load_or_create_config()
    language = config_obj["Language"]["language"]
    return language


def load_translations():
    """Load the translation file based on the language setting."""
    language = get_language_setting()

    # Construct the path to the language file
    lang_file_path = Path(f'{config.LANG_PATH}', f'{language}.json')

    # Load the translations if not already cached
    if not translations_cache:
        try:
            with open(lang_file_path, 'r', encoding='utf-8') as file:
                translations_cache.update(json.load(file))
        except FileNotFoundError:
            print(f"Error: The translation file {lang_file_path} was not found.")

    return translations_cache


def ask_language_choice():
    """Ask the user to select a language at the first script launch."""
    print("[bold cyan]Please select your preferred language:[/bold cyan]")

    # Display a message to prompt the user for language selection
    language_options = list(config.SUPPORTED_LANGUAGES.keys())
    for index, region in enumerate(language_options, start=1):
        language_name = config.SUPPORTED_LANGUAGES[region][1]
        print(f"    [bold]{index}.[/bold] {language_name} ({region})")

    # Use Prompt.ask to get the user's input
    choice_index = Prompt.ask(
        "Enter the number of your language choice",
        choices=[str(i) for i in range(1, len(language_options) + 1)],
        show_choices=False
    )

    # Convert the user's choice to the corresponding language key
    chosen_region = language_options[int(choice_index) - 1]
    language_code = config.SUPPORTED_LANGUAGES.get(chosen_region)[0]
    chosen_language = f'{language_code}_{chosen_region}'
    return chosen_language
