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

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-08"  # Last update

# display.py

import translations  # Import the lang module
import mu_script_update
import os
# from rich import print
from rich.console import Console


# from utils import print_dict  # for test

console = Console()


def welcome_display():
    # look for script update
    new_version, urlscript = mu_script_update.fetch_page()
    # new_version, urlscript = [True, config.URL_SCRIPT[config.SYSTEM.lower()]]  # test
    if new_version:
        text_script_new_version = f'[red]- {translations.translations_cache.get("title_new_version")} -[/red]\n{urlscript} -'
    else:
        text_script_new_version = f'[bold cyan]- {translations.translations_cache.get("title_no_new_version")} - [/bold cyan]'
    # *** Welcome text ***
    try:
        column, row = os.get_terminal_size()
    except OSError:
        column, row = 300, 50  # Default values
    txt_title = f'\n\n[bold cyan]{translations.translations_cache.get("title_modsupdater_title").format(mu_ver=__version__)}[/bold cyan]'

    lines = txt_title.splitlines() + text_script_new_version.splitlines()
    for line in lines:
        console.print(line.center(column), justify='center')


if __name__ == "__main__":  # For test
    welcome_display()
