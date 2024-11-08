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
__date__ = "2024-11-07"  # Last update

# lang.py

import config  # Import the config module
import json
from pathlib import Path

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


load_translations()
