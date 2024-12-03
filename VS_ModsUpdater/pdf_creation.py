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
__date__ = "2024-12-03"  # Last update

# pdf_creation.py

import global_cache
import config
import zipfile
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO


mods_path = global_cache.MODS_PATHS[global_cache.SYSTEM]


def extract_icon(zip_path):
    """
    Extracts 'modicon.png' from the ZIP archive.
    If not found, returns None.
    If found, resizes and returns the icon as a ReportLab-compatible object.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if 'modicon.png' in zip_ref.namelist():
                # Read 'modicon.png'
                icon_data = zip_ref.read('modicon.png')
                # Save the image data to a BytesIO object
                img_io = BytesIO(icon_data)
                img_io.seek(0)  # Reset pointer
                return img_io
    except Exception as e:
        print(f"Error extracting icon from {zip_path}: {e}")
    return None


# Function to create the PDF with Platypus.Table
def create_pdf_with_table(modsdata, pdf_path):
    """
    Create a PDF listing all the mods with their icons, names, versions, and descriptions using Platypus.Table.
    """
    # Initialize the PDF document
    doc = SimpleDocTemplate(pdf_path,
                            pagesize=A4,
                            leftMargin=20,
                            topMargin=20,
                            rightMargin=20,
                            bottomMargin=20
                            )

    # Add a cyrillic font (for example, DejaVu Sans)
    cyrillic_font_path = Path(config.APPLICATION_PATH).parent / 'fonts' / 'FreeSans.ttf' # Specify the path to the TTF font file
    pdfmetrics.registerFont(TTFont('FreeSans', cyrillic_font_path))

    # Exemple de styles pour le texte
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontName = "FreeSans"
    style_normal.fontSize = 8
    style_title = styles["Title"]
    style_title.fontName = "FreeSans"
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
        print(f"Error loading banner image: {e}")
        elements.append(Paragraph("Banner missing", styles["Normal"]))

    # Add a space of 50 points below the image
    elements.append(Spacer(1, 50))

    # Draw background function
    def draw_background(canvas, doc):
        canvas.setFillColorRGB(200/255, 220/255, 160/255)  # Vert très pâle en RGB (moins flashy)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)  # Fill the entire page

    # Title
    elements.append(Paragraph(global_cache.global_cache.language_cache['pdf_title'], style_title))

    # Data for the table: rows
    # data = [["", "Mod (Version)", "Description"]]  # Table header
    data = []

    # Fill the table with mod data
    row_colors = [(204/255, 221/255, 168/255), (240/255, 245/255, 230/255)]  # Couleurs de lignes plus douces
    for idx, mod_info in enumerate(modsdata.values()):
        # Icon
        icon = mod_info.get("icon")
        if icon:
            icon_image = Image(icon)
            icon_image.drawWidth = 25
            icon_image.drawHeight = 25
        else:
            icon_image = ""

        # Name and version
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


# Main function to orchestrate the PDF generation
def generate_mod_pdf(mod_info_data, pdf_path):
    """
    Generate the PDF with a list of mods and their details.
    """
    mod_info_for_pdf = {}
    # Prepare the data: load icons for each mod
    for mod, mod_info in mod_info_data.items():
        mod_zip_path = str(global_cache.MODS_PATHS[global_cache.SYSTEM] / mod)  # Adjust path accordingly
        mod_info_for_pdf[mod] = {
            "name": mod_info["name"],
            "version": mod_info["local_version"],
            "description": mod_info["description"],
            "icon": extract_icon(mod_zip_path)
        }

    # Generate the PDF
    create_pdf_with_table(mod_info_for_pdf, pdf_path)
