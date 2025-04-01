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
This module automates the creation of a PDF document containing a list of Vintage Story mods, including their icons, names, versions, and descriptions. It leverages multithreading to efficiently process mod information and generate a visually appealing PDF.

Key functionalities include:
- Extracting and resizing mod icons from ZIP archives.
- Generating a PDF with a table layout, displaying mod icons, names, versions, and descriptions.
- Using multithreading to accelerate the processing of mod data and icon extraction.
- Incorporating a banner and background image for enhanced visual appeal.
- Adding a footer with a link to the ModsUpdater project.
- Handling potential errors during image processing and PDF creation, with appropriate logging.
- Supporting Cyrillic and other Unicode characters by embedding a suitable font.
- Normalizing strings for case-insensitive sorting of mods by name.
- Retrieving local versions of excluded mods to ensure accurate version display.

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__date__ = "2025-04-01"  # Last update


# export_pdf.py


import concurrent.futures
import logging
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import unicodedata
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, \
    Spacer
from rich.progress import Progress

import config
import global_cache


# Suppress Pillow debug messages
logging.getLogger("PIL").setLevel(logging.WARNING)


def resize_image(image_data, max_width=100, max_height=100):
    """
    Resize the image to fit within the specified max width and height while maintaining the aspect ratio.
    """
    try:
        # Load the image into a Pillow object
        image = PILImage.open(BytesIO(image_data))

        # Calculate the new size preserving the aspect ratio
        image.thumbnail((max_width, max_height))

        # Save the resized image to a BytesIO object
        output_io = BytesIO()
        image.save(output_io, format='PNG')
        output_io.seek(0)  # Reset pointer to the beginning
        return output_io
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
    return None


def extract_icon(zip_path):
    """
    Extracts and resizes 'modicon.png' from the ZIP archive.
    If the file is not a ZIP file or doesn't contain 'modicon.png', returns a default icon ('assets/no_icon.png').
    If the file is a ZIP and contains 'modicon.png', resizes and returns the icon.
    """
    try:
        # Check if the file is a ZIP file
        if zip_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # If 'modicon.png' is not in the ZIP, treat it like a non-ZIP file and use default icon
                if 'modicon.png' not in zip_ref.namelist():
                    logging.debug(
                        f"'modicon.png' not found in {zip_path}, using default icon.")
                    return get_default_icon()

                # Read 'modicon.png' from the ZIP
                icon_data = zip_ref.read('modicon.png')
                logging.debug(f"Found 'modicon.png' in {zip_path}.")
                # Resize the image (adjust max width/height as needed)
                resized_icon = resize_image(icon_data, max_width=100, max_height=100)
                if resized_icon:
                    return resized_icon

        # If it's not a ZIP file or 'modicon.png' was not found, use the default icon
        return get_default_icon()

    except Exception as e:
        logging.error(f"Error extracting icon from {zip_path}: {e}")
        return get_default_icon()


def get_default_icon():
    """
    Loads and resizes the default icon ('assets/no_icon.png').
    """
    default_icon_path = Path(config.APPLICATION_PATH) / 'assets' / 'no_icon.png'
    if default_icon_path.exists():
        with open(default_icon_path, 'rb') as f:
            icon_data = f.read()
        logging.debug(f"Using default icon from {default_icon_path}.")
        # Resize the default icon
        resized_icon = resize_image(icon_data, max_width=100, max_height=100)
        if resized_icon:
            return resized_icon
    else:
        logging.debug(f"Default icon 'no_icon.png' not found at {default_icon_path}.")
        return None  # Return None if default icon is not found


# Function to create the PDF with Platypus.Table
def create_pdf_with_table(modsdata, pdf_path):
    """
    Create a PDF listing all the mods with their icons, names, versions, and descriptions using Platypus.Table.
    """
    num_mods = global_cache.total_mods
    # Initialize the PDF document
    doc = SimpleDocTemplate(pdf_path,
                            pagesize=A4,
                            leftMargin=20,
                            topMargin=20,
                            rightMargin=20,
                            bottomMargin=20
                            )

    # Add a cyrillic font (for example, DejaVu Sans)
    font_path = Path(config.APPLICATION_PATH) / 'fonts' / 'NotoSansCJKsc-Regular.ttf'
    pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Regular', font_path))

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontName = "NotoSansCJKsc-Regular"
    style_normal.fontSize = 8
    style_title = styles["Title"]
    style_title.textColor = colors.Color(47/255, 79/255, 79/255)  # Vert forêt en RGB normalisé
    style_title.fontSize = 14

    elements = []

    # Add the banner image
    try:
        path_img = Path(config.APPLICATION_PATH) / 'assets' / 'banner.png'
        banner = Image(str(path_img))  # Path to your image
        banner.drawWidth = A4[0] - 40  # Adjust width to fit the page minus margins
        banner.drawHeight = 120  # Adjust height as needed
        elements.append(banner)
    except Exception as e:
        logging.debug(f"Error loading banner image: {e}")
        # elements.append(Paragraph("Banner missing", styles["Normal"]))  # debug

    # Add a space of 50 points below the image
    elements.append(Spacer(1, 50))

    def draw_background(canvas):
        # Path to the background image
        background_path = Path(
            config.APPLICATION_PATH) / 'assets' / 'background.jpg'

        if background_path.exists():
            try:
                # Page Dimensions
                page_width, page_height = A4

                # Direct use of ReportLab to display the image
                canvas.drawImage(
                    str(background_path),
                    0,  # Position X
                    0,  # Position Y
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=True,
                    mask='auto'  # Transparence
                )
            except Exception as error:
                logging.error(f"Error displaying background image: {error}")
                # Fallback en cas d'échec
                canvas.setFillColorRGB(200 / 255, 220 / 255, 160 / 255)
                canvas.rect(0, 0, A4[0], A4[1], fill=1)
        else:
            # Fallback if the image does not exist
            canvas.setFillColorRGB(200 / 255, 220 / 255, 160 / 255)
            canvas.rect(0, 0, A4[0], A4[1], fill=1)

    # Add a link at the bottom-right corner (footer) of the page
    def draw_footer(canvas):
        # Creating the style for the link
        styles_local = getSampleStyleSheet()
        link_style_custom = styles_local["Normal"].clone("LinkStyle")
        link_style_custom.textColor = colors.black
        link_style_custom.fontSize = 8

        # The footer text
        footer_text = '<a href="https://mods.vintagestory.at/modsupdater">ModsUpdater by Laerinok</a>'
        link_paragraph = Paragraph(footer_text, link_style_custom)

        # Calculating the text size (width and height)
        footer_width, footer_height = link_paragraph.wrap(A4[0] - 475, 100)  # 120 x 100
        text_width = footer_width
        text_height = footer_height
        x_position = A4[0] - text_width - 20
        y_position = 10  # Marge du bas

        # Draw the colored background just behind the text (adjusted size)
        canvas.setFillColorRGB(240 / 255, 245 / 255, 220 / 255)
        canvas.roundRect(x_position, y_position, footer_width, footer_height, radius=10, fill=1)

        # Centered positioning of the text
        link_paragraph.drawOn(canvas,
                              x_position + (footer_width - text_width) / 2 + 15,
                              y_position + (footer_height - text_height) / 2)

    # Title
    elements.append(Paragraph(f"{num_mods} {global_cache.language_cache['pdf_title']}", style_title))

    # Add a space below the title
    elements.append(Spacer(1, 10))

    # Data for the table: rows
    data = []  # no header (empty table. the first entry is the header)

    # Fill the table with mod data
    for idx, mod_info in enumerate(modsdata.values()):
        # Icon (with direct insertion, not HTML)
        icon = mod_info.get("icon")
        icon_image = None
        if icon:
            try:
                icon_image = Image(icon)
                icon_image.drawWidth = 25
                icon_image.drawHeight = 25
            except Exception as e:
                logging.error(f"Failed to load icon for mod '{mod_info['name']}': {e}")
        else:
            icon_image = ""  # Placeholder if no icon is present

        # Modify the style for links
        link_style = styles["Normal"].clone("LinkStyle")
        link_style.textColor = colors.black  # Set your desired color here
        link_style.fontName = "NotoSansCJKsc-Regular"

        # Name and version with hyperlink
        url = mod_info.get("url_moddb", "")
        # print(mod_info)  # debug
        if url != 'Local mod':
            name_and_version = f'<b><a href="{url}">{mod_info["name"]} (v{mod_info["version"]})</a></b>'
            name_and_version_paragraph = Paragraph(name_and_version,
                                                   link_style)  # Use the custom style for links
        else:
            name_and_version = f"<b>{mod_info['name']}</b> (v{mod_info['version']})"
            name_and_version_paragraph = Paragraph(name_and_version, style_normal)

        # Description
        description = str(mod_info.get('description', ''))
        description_paragraph = Paragraph(description, style_normal)

        # Add the row
        data.append([icon_image, name_and_version_paragraph, description_paragraph])

    # Create the table
    table = Table(data, colWidths=[30, 180, 330])  # Adjust column widths
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),                       # Center horizontal align
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),                      # Middle vertical align
        ('GRID', (0, 0), (-1, -1), 1, colors.black),                 # Grid lines
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSansCJKsc-Regular'),                 # Normal font for rows
        ('FONTSIZE', (0, 0), (-1, -1), 8),                          # Font size
        ('BACKGROUND', (0, 0), (-1, -1), (240/255, 245/255, 220/255)),  # Alternating row background (light soft green)
    ]))

    # Add the table to the document
    elements.append(table)

    try:
        # Build the PDF
        def draw_background_and_footer(canvas):
            draw_background(canvas)
            draw_footer(canvas)
        doc.build(elements,
                  onFirstPage=lambda canvas, document: draw_background_and_footer(canvas),
                  onLaterPages=lambda canvas, document: draw_background_and_footer(canvas))
        print(f"A modlist has been exported in PDF format to the following location: {global_cache.config_cache['Backup_Mods']['modlist_folder']}")
        logging.info(f"PDF successfully created: {pdf_path}")
    except PermissionError as e:
        print(f"PermissionError: Unable to access the file '{pdf_path}'. The file may be open or in use by another process.\nPlease close any applications that may be using the file and try again.")
        logging.error(f"{e} - PermissionError: Unable to access the file '{pdf_path}'. ")
        sys.exit()


def get_local_versions_of_excluded_mods(mods_data):
    """
    Retrieves the 'Local_Version' of excluded mods.
    """
    local_versions = {}  # Dictionary to store ModId: Local_Version pairs
    excluded_filenames = {mod['Filename'] for mod in mods_data['excluded_mods']}  # Set of excluded filenames for fast lookup

    for installed_mod in mods_data['installed_mods']:
        if installed_mod['Filename'] in excluded_filenames:
            local_versions[installed_mod['ModId']] = installed_mod['Local_Version']  # Store Local_Version if filename matches

    return local_versions  # Return the dictionary of Local_Versions


def process_mod(mod_info):
    """
    Process to extract mod information.
    """
    mod_name = mod_info["Name"]
    if mod_info["Mod_url"] != "Local mod":
        if mod_info['Latest_version_mod_url'] is not None:
            filename = mod_info['Latest_version_mod_url'].split("dl=")[-1]
            version = mod_info['mod_latest_version_for_game_version']
        else:
            filename = mod_info['Filename']
            version = mod_info["Local_Version"]
    else:
        filename = mod_info['Filename']
        version = mod_info["Local_Version"]

    excluded_local_versions = get_local_versions_of_excluded_mods(global_cache.mods_data)
    if mod_info['ModId'] in excluded_local_versions:
        version = excluded_local_versions[mod_info['ModId']]

    return {
        mod_info["ModId"]: {
            "name": mod_name,
            "version": version,
            "description": mod_info["Description"] if mod_info["Description"] is not None else "",
            "url_moddb": mod_info["Mod_url"],
            "icon": extract_icon(
                Path(global_cache.config_cache['ModsPath']['path']) / filename)
        }
    }


def normalize_string_case_insensitive(s):
    """Normalize a string for case-insensitive sorting."""
    s = s.lstrip()
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


# Main function to orchestrate the PDF generation
def generate_pdf(mod_info_data):
    """
    Generates the PDF with a list of mods and their details using multithreading.
    """
    pdf_name = f"modlist.pdf"
    output_pdf_path = str(Path(config.APPLICATION_PATH) / global_cache.config_cache['Backup_Mods']['modlist_folder'] / pdf_name)

    global_cache.total_mods = len(mod_info_data)
    mod_info_for_pdf = {}

    with Progress() as progress:
        task = progress.add_task("[cyan]Generating PDF...", total=global_cache.total_mods)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_mod, mod_info) for mod_info in global_cache.mods_data['installed_mods']]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                mod_info_for_pdf.update(result)
                progress.update(task, advance=1)

    sorted_mod_info = dict(sorted(mod_info_for_pdf.items(), key=lambda item: normalize_string_case_insensitive(item[1]['name'])))
    create_pdf_with_table(sorted_mod_info, output_pdf_path)
