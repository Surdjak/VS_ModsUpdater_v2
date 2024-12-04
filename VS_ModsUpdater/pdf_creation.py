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
__date__ = "2024-12-04"  # Last update


# pdf_creation.py


import logging
import global_cache
import config
import zipfile
from datetime import datetime
from pathlib import Path
from rich.progress import Progress
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PIL import Image as PILImage
from io import BytesIO


config.configure_logging(global_cache.global_cache.config_cache["Logging"]['log_level'].upper())
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
    If not found, returns None.
    If found, resizes and returns the icon as a ReportLab-compatible object.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if 'modicon.png' in zip_ref.namelist():
                # Read 'modicon.png'
                icon_data = zip_ref.read('modicon.png')
                logging.debug(f"Found 'modicon.png' in {zip_path}.")
                # Resize the image (adjust max width/height as needed)
                resized_icon = resize_image(icon_data, max_width=100, max_height=100)
                if resized_icon:
                    return resized_icon
            else:
                logging.debug(f"'modicon.png' not found in {zip_path}.")
    except Exception as e:
        logging.error(f"Error extracting icon from {zip_path}: {e}")
    return None


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
    freesans_path = Path(config.APPLICATION_PATH).parent / 'fonts' / 'FreeSans.ttf'
    pdfmetrics.registerFont(TTFont('FreeSans', freesans_path))
    bold_freesans_path = Path(config.APPLICATION_PATH).parent / 'fonts' / 'FreeSansBold.ttf'
    pdfmetrics.registerFont(TTFont('FreeSansBold', bold_freesans_path))

    # Exemple de styles pour le texte
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
        path_img = Path(config.APPLICATION_PATH).parent / 'assets' / 'banner.png'
        banner = Image(str(path_img))  # Path to your image
        banner.drawWidth = A4[0] - 40  # Adjust width to fit the page minus margins
        banner.drawHeight = 120  # Adjust height as needed
        elements.append(banner)
    except Exception as e:
        logging.debug(f"Error loading banner image: {e}")
        # elements.append(Paragraph("Banner missing", styles["Normal"]))  # debug

    # Add a space of 50 points below the image
    elements.append(Spacer(1, 50))

    # Draw background function
    def draw_background(canvas, doc):
        canvas.setFillColorRGB(200/255, 220/255, 160/255)  # Vert très pâle en RGB (moins flashy)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)  # Fill the entire page

    # Title
    elements.append(Paragraph(f"{global_cache.global_cache.language_cache['pdf_title']} ({num_mods} mods)", style_title))

    # Add a space below the title
    elements.append(Spacer(1, 10))

    # Data for the table: rows
    # data = [["", "Mod (Version)", "Description"]]  # Table header
    data = []  # no header (empty table. the first entry is the header)

    # Fill the table with mod data
    row_colors = [(204/255, 221/255, 168/255), (240/255, 245/255, 230/255)]  # Couleurs de lignes plus douces
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
    table = Table(data, colWidths=[50, 150, 300])  # Adjust column widths
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

    # Build the PDF
    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
    logging.info(f"PDF successfully created: {pdf_path}")


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
    output_pdf_path = str(Path(config.APPLICATION_PATH).parent / pdf_name)
    logging.debug(f"Output PDF will be saved at: {output_pdf_path}")

    mod_info_for_pdf = {}
    total_mods = len(mod_info_data)
    logging.info(f"Preparing data for {total_mods} mods.")

    # Utilisation de Rich Progress
    with Progress() as progress:
        task = progress.add_task("PDF creation...", total=total_mods)

        for mod, mod_info in mod_info_data.items():
            logging.debug(f"Processing mod: {mod} - {mod_info['name']}")
            mod_zip_path = str(f"{global_cache.global_cache.config_cache['ModsPath']['path']}/{mod}")

            try:
                mod_info_for_pdf[mod] = {
                    "name": mod_info["name"],
                    "version": mod_info["local_version"],
                    "description": mod_info["description"],
                    "url_moddb": mod_info["url_moddb"],
                    "icon": extract_icon(mod_zip_path),
                }
            except Exception as e:
                logging.error(f"Error processing mod: {mod} - {e}")

            # Avancer la barre de progression
            progress.update(task, advance=1)

    global_cache.global_cache.total_mods = total_mods
    logging.info(f"Total mods processed: {total_mods}")

    logging.info("Generating PDF document.")
    create_pdf_with_table(mod_info_for_pdf, output_pdf_path)
    logging.info(f"PDF generation complete: {output_pdf_path}")
