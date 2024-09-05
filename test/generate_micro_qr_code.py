#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023-2024 Marc-Antoine Desjardins.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""Script to generate pages of 70 MicroQR codes to print.

You'll first need to download images from the shared google drive folder of AiWarmachine:
    - MicroQr_Int_Small_Base_Template_Page.png
    - MicroQr_Int_No_Base_Template_Page.png
    - Letter_300dpi.png

And put them in AiWarmachine/images/MicroQR folder on your machine.

Example usage:
python generate_micro_qr_code.py 0 --small_base
python generate_micro_qr_code.py 1000
"""

import os
import argparse

import pyboof as pb
from pyboof import pbg
from PyQt6 import QtGui

AIWARMACHINE_ROOT_DIR_PATH = os.path.dirname(os.path.dirname(__file__))

MICRO_QR_INT_FILE_PATH_TEMPLATE = AIWARMACHINE_ROOT_DIR_PATH + "/images/MicroQR/_tmp/MicroQr_Int_s{size:02d}_{value:04d}.png"
MICRO_QR_INT_PAGE_FILE_PATH_TEMPLATE = AIWARMACHINE_ROOT_DIR_PATH + "/images/MicroQR/MicroQr_Int_s{size:02d}_Page_{value_min:04d}_{value_max:04d}.png"
MICRO_QR_INT_SMALL_BASE_TEMPLATE_PAGE_FILE_PATH = AIWARMACHINE_ROOT_DIR_PATH + "/images/MicroQR/MicroQr_Int_Small_Base_Template_Page.png"
MICRO_QR_INT_NO_BASE_TEMPLATE_PAGE_FILE_PATH = AIWARMACHINE_ROOT_DIR_PATH + "/images/MicroQR/MicroQr_Int_No_Base_Template_Page.png"
LETTER_PAGE_300DPI_FILE_PATH = AIWARMACHINE_ROOT_DIR_PATH + "/images/MicroQR/Letter_300dpi.png"


def generate_micro_qr_int(size, value_min, value_max, file_path_template):
    """Generate MicroQR code in a range of values.

    :param size: The number of pixels_per_module.
    :type size: int

    :param value_min: The lowest MicroQR number to generate.
    :type value_min: int

    :param value_max: The highest MicroQR number to generate.
    :type value_max: int

    :param file_path_template: The file path template for the generated images.
    :type file_path_template: str

        **Example: "D:/Dev_Projects/AiWarmachine/images/MicroQR/_tmp/MicroQr_Int_s{size:02d}_{value:04d}.png" **

    :return: The list of image file paths.
    :rtype: list[str]
    """
    image_file_paths_list = []
    for value in range(value_min, value_max + 1):
        print(f"Generating: {value}")
        generator = pb.MicroQrCodeGenerator(pixels_per_module=size)
        generator.set_message(value)
        boof_gray_image = generator.generate()
        file_path = file_path_template.format(size=size, value=value)
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        elif os.path.exists(file_path):
            os.remove(file_path)
        pbg.gateway.jvm.boofcv.io.image.UtilImageIO.saveImage(boof_gray_image, file_path)
        image_file_paths_list.append(file_path)

    return image_file_paths_list


def composite_images(image_base, image_overlay, overlay_x=0, overlay_y=0):
    """Composite 2 images using over mode.

    :param image_base: The base image.
    :type image_base: :class:`QImage`

    :param image_overlay: The image to composite over the base image.
    :type image_overlay: :class:`QImage`

    :param overlay_x: Horizontal overlay offset in pixels. (0)
    :type overlay_x: int

    :param overlay_y: Vertical overlay offset in pixels. (0)
    :type overlay_y: int

    :return: Composite image.
    :rtype: :class:`QImage`
    """
    image_result = QtGui.QImage(image_base.size(), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    painter = QtGui.QPainter(image_result)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
    painter.drawImage(0, 0, image_base)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.drawImage(overlay_x, overlay_y, image_overlay)

    painter.end()

    return image_result


def compose_micro_qr_int_page(
    template_page_image_file_path,
    qr_image_file_paths_list,
    column_count,
    row_count,
    page_image_file_path,
    printable_page_image_file_path=None
):
    """Merge the MicroQR code images on top of a page template ready for print.

    :param template_page_image_file_path: The template page image file path.
    :type template_page_image_file_path: str

        **Example: "D:/Dev_Projects/AiWarmachine/images/MicroQR/MicroQr_Int_Small_Base_Template_Page.png" **

    :param qr_image_file_paths_list: The list of MicroQR image filepaths.
    :type qr_image_file_paths_list: list[str]

    :param column_count: The number of columns in the template page.
    :type column_count: int

    :param row_count: The number of rows in the template page.
    :type row_count: int

    :param page_image_file_path: The output image file path.
    :type page_image_file_path: str

        **Example: "D:/Dev_Projects/AiWarmachine/images/MicroQR/MicroQr_Int_s16_Page_0000_0069.png" **

    :param printable_page_image_file_path: If set, will composite the page result in the middle of this image. (None)
    :type printable_page_image_file_path: str

        **Example: "D:/Dev_Projects/AiWarmachine/images/MicroQR/Letter_300dpi.png" **

    :return: The output image file path.
    :rtype: str
    """
    template_image = QtGui.QImage(template_page_image_file_path)
    width = template_image.width()
    offset_step_f = width / column_count
    offset_base_f = offset_step_f / 2

    for row in range(row_count):
        for column in range(column_count):
            index = row * column_count + column
            qr_image = QtGui.QImage(qr_image_file_paths_list[index])
            template_image = composite_images(
                template_image,
                qr_image,
                overlay_x=int(offset_base_f + offset_step_f * column - qr_image.width() / 2 + 0.5),
                overlay_y=int(offset_base_f + offset_step_f * row - qr_image.height() / 2 + 0.5)
            )

    if printable_page_image_file_path is not None:
        printable_image = QtGui.QImage(printable_page_image_file_path)
        template_image = composite_images(
            printable_image,
            template_image,
            overlay_x=int((printable_image.width() - template_image.width()) / 2 + 0.5),
            overlay_y=int((printable_image.height() - template_image.height()) / 2 + 0.5)
        )

    print(f"Saving page result to '{page_image_file_path}'.")
    if not os.path.exists(os.path.dirname(page_image_file_path)):
        os.makedirs(os.path.dirname(page_image_file_path))
    elif os.path.exists(page_image_file_path):
        os.remove(page_image_file_path)
    template_image.save(page_image_file_path)

    return page_image_file_path


def generate_micro_qr_int_page(column_count, row_count, value_min, size, with_small_base_circle=False):
    """Generate a whole page of MicroQR code starting from a certain value.

    :param column_count: The number of columns in the template page.
    :type column_count: int

    :param row_count: The number of rows in the template page.
    :type row_count: int

    :param value_min: The lowest MicroQR number to generate.
    :type value_min: int

    :param size: The number of pixels_per_module.
    :type size: int

    :param with_small_base_circle: If set to True, will circle in light gray the MicroQR as hint for cut. (False)
    :type with_small_base_circle: bool

    :return: The output image file path.
    :rtype: str
    """
    value_max = value_min + column_count * row_count - 1
    micro_qr_image_file_paths_list = generate_micro_qr_int(
        size=size,
        value_min=value_min,
        value_max=value_max,
        file_path_template=MICRO_QR_INT_FILE_PATH_TEMPLATE
    )

    template_page_image_file_path = MICRO_QR_INT_SMALL_BASE_TEMPLATE_PAGE_FILE_PATH if with_small_base_circle else MICRO_QR_INT_NO_BASE_TEMPLATE_PAGE_FILE_PATH

    output_file_path = compose_micro_qr_int_page(
        template_page_image_file_path=template_page_image_file_path,
        qr_image_file_paths_list=micro_qr_image_file_paths_list,
        column_count=column_count,
        row_count=row_count,
        page_image_file_path=MICRO_QR_INT_PAGE_FILE_PATH_TEMPLATE.format(size=size, value_min=value_min, value_max=value_max),
        printable_page_image_file_path=LETTER_PAGE_300DPI_FILE_PATH
    )

    print("Deleting temporary files...")
    for qr_image_file_path in micro_qr_image_file_paths_list:
        os.remove(qr_image_file_path)

    return output_file_path


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("min_value", type=int, help="MicroQR minimum value")
    parser.add_argument("-sb", "--small_base", action="store_true", help="set to have small base circle around MicroQR")
    args = parser.parse_args()

    image_file_path = generate_micro_qr_int_page(
        column_count=7,
        row_count=10,
        value_min=args.min_value,
        size=16,
        with_small_base_circle=args.small_base
    )
