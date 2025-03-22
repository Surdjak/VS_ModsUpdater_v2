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
Vintage Story mod management:
** PDF Creation **

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-12-09"  # Last update


# pdf_creation.py


import logging
import sys

import global_cache
import config
import zipfile
from datetime import datetime
from pathlib import Path
from rich.progress import Progress, BarColumn, TextColumn
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image as PILImage
from io import BytesIO


config.configure_logging(
    global_cache.global_cache.config_cache["Logging"]['log_level'].upper())
# Suppress Pillow debug messages
logging.getLogger("PIL").setLevel(logging.WARNING)

mods_path = global_cache.MODS_PATHS[global_cache.SYSTEM]


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
        logging.debug(f"Image resized to fit within {max_width}x{max_height}.")
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
    logging.info(f"Starting PDF creation: {pdf_path}")
    num_mods = global_cache.global_cache.total_mods
    # Initialize the PDF document
    doc = SimpleDocTemplate(pdf_path,
                            pagesize=A4,
                            leftMargin=20,
                            topMargin=20,
                            rightMargin=20,
                            bottomMargin=20
                            )

    # Add a cyrillic font (for example, DejaVu Sans)
    freesans_path = Path(config.APPLICATION_PATH) / 'fonts' / 'FreeSans.ttf'
    pdfmetrics.registerFont(TTFont('FreeSans', freesans_path))
    bold_freesans_path = Path(
        config.APPLICATION_PATH) / 'fonts' / 'FreeSansBold.ttf'
    pdfmetrics.registerFont(TTFont('FreeSansBold', bold_freesans_path))

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontName = "FreeSans"
    style_normal.fontSize = 8
    style_title = styles["Title"]
    style_title.fontName = "FreeSansBold"
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

    def draw_background(canvas, doc):
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
    def draw_footer(canvas, doc):
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
    elements.append(Paragraph(f"{num_mods} {global_cache.global_cache.language_cache['pdf_title']}", style_title))

    # Add a space below the title
    elements.append(Spacer(1, 10))

    # Data for the table: rows
    # data = [["", "Mod (Version)", "Description"]]  # Table header
    data = []  # no header (empty table. the first entry is the header)

    # Fill the table with mod data
    row_colors = [(204/255, 221/255, 168/255), (240/255, 245/255, 230/255)]
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
        link_style.fontName = "FreeSans"

        # Name and version with hyperlink
        url = mod_info.get("url_moddb", "")
        if url:
            name_and_version = f'<b><a href="{url}">{mod_info["name"]}</a></b> (v{mod_info["version"]})'
            name_and_version_paragraph = Paragraph(name_and_version,
                                                   link_style)  # Use the custom style for links
        else:
            name_and_version = f"<b>{mod_info['name']}</b> (v{mod_info['version']})"
            name_and_version_paragraph = Paragraph(name_and_version, style_normal)

        # Description
        description = mod_info['description']
        description_paragraph = Paragraph(description, style_normal)

        # Add the row
        data.append([icon_image, name_and_version_paragraph, description_paragraph])

    # Create the table
    table = Table(data, colWidths=[30, 180, 330])  # Adjust column widths
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),                       # Center horizontal align
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),                      # Middle vertical align
        ('GRID', (0, 0), (-1, -1), 1, colors.black),                 # Grid lines
        ('FONTNAME', (0, 0), (-1, -1), 'FreeSans'),                 # Normal font for rows
        ('FONTSIZE', (0, 0), (-1, -1), 8),                          # Font size
        ('BACKGROUND', (0, 0), (-1, -1), (240/255, 245/255, 220/255)),  # Alternating row background (light soft green)
    ]))

    # Add the table to the document
    elements.append(table)

    try:
        # Build the PDF
        doc.build(elements,
                  onFirstPage=draw_background,
                  onLaterPages=lambda canvas, doc: [draw_background(canvas, doc), draw_footer(canvas, doc)])
        logging.info(f"PDF successfully created: {pdf_path}")
    except PermissionError as e:
        print(f"PermissionError: Unable to access the file '{pdf_path}'. The file may be open or in use by another process.\nPlease close any applications that may be using the file and try again.")
        logging.error(f"{e} - PermissionError: Unable to access the file '{pdf_path}'. ")
        sys.exit()


# Main function to orchestrate the PDF generation
def generate_mod_pdf(mod_info_data):
    """
    Generate the PDF with a list of mods and their details.
    """
    logging.info("Starting PDF generation process.")
    logging.info(f"Total mods to process: {len(mod_info_data)}")

    # file path
    current_datetime = datetime.now()
    year = current_datetime.strftime("%Y")
    month = current_datetime.strftime("%m")
    day = current_datetime.strftime("%d")
    pdf_name = f"VS_Mods_{year}_{month}_{day}.pdf"
    output_pdf_path = str(Path(config.APPLICATION_PATH) / pdf_name)
    logging.debug(f"Output PDF will be saved at: {output_pdf_path}")

    mod_info_for_pdf = {}
    total_mods = len(mod_info_data)
    logging.info(f"Preparing data for {total_mods} mods.")

    # Use of Rich Progress
    with Progress(
            "[progress.description]" + f"[green]{global_cache.global_cache.language_cache['pdf_creation']}[/green]",
            BarColumn(bar_width=30, finished_style="green",
                      complete_style="bold green"),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TextColumn("{task.fields[mod_name]}"),
            "{task.completed}/{task.total}",
            transient=False,
    ) as progress:
        task = progress.add_task(
            f"{global_cache.global_cache.language_cache['pdf_creation']}", total=total_mods,
            mod_name="")

        for mod, mod_info in mod_info_data.items():
            mod_name = mod_info['name']
            progress.update(task, advance=1, mod_name=mod_name)  # Update mod_name

            logging.debug(f"Processing mod: {mod} - {mod_name}")
            mod_zip_path = Path(
                global_cache.global_cache.config_cache['ModsPath']['path']) / mod

            try:
                mod_info_for_pdf[mod] = {
                    "name": mod_name,
                    "version": mod_info["local_version"],
                    "description": mod_info["description"],
                    "url_moddb": mod_info["url_moddb"],
                    "icon": extract_icon(mod_zip_path),
                }
            except Exception as e:
                logging.error(f"Error processing mod: {mod} - {e}")

    global_cache.global_cache.total_mods = total_mods
    logging.info(f"Total mods processed: {total_mods}")

    logging.info("Generating PDF document.")

    create_pdf_with_table(mod_info_for_pdf, output_pdf_path)
    logging.info(f"PDF generation complete: {output_pdf_path}")
