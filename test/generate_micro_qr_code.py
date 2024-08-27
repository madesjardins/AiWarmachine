import os
import pyboof as pb
import cv2
import numpy as np
from pyboof import pbg
from PyQt6 import QtGui

MICRO_QR_INT_FILE_PATH_TEMPLATE = "D:/Dev_Projects/AiWarmachine/images/MicroQR/_tmp/MicroQr_Int_s{size:02d}_{value:04d}.png"
MICRO_QR_INT_PAGE_FILE_PATH_TEMPLATE = "D:/Dev_Projects/AiWarmachine/images/MicroQR/MicroQr_Int_s{size:02d}_Page_{value_min:04d}_{value_max:04d}.png"
MICRO_QR_INT_SMALL_BASE_TEMPLATE_PAGE_FILE_PATH = "D:/Dev_Projects/AiWarmachine/images/MicroQR/MicroQr_Int_Small_Base_Template_Page.png"
LETTER_PAGE_300DPI_FILE_PATH = "D:/Dev_Projects/AiWarmachine/images/MicroQR/Letter_300dpi.png"

# def generate_all_resolution():
#     for size in range(1, 20):
#         message = f"AiWM{size:04d}"
#         print(f"Generating: {message}")
#         generator = pb.MicroQrCodeGenerator(pixels_per_module=size)
#         generator.set_message(message)
#         boof_gray_image = generator.generate()
#         pbg.gateway.jvm.boofcv.io.image.UtilImageIO.savePGM(boof_gray_image, f"C:/tmp/{message}.pgm")


# def generate_all_resolution_int():
#     for exponent in range(0, 14):
#         number = pow(2, exponent)
#         print(f"Generating: {number}")
#         generator = pb.MicroQrCodeGenerator(pixels_per_module=16)
#         generator.set_message(number)
#         boof_gray_image = generator.generate()
#         file_path = f"D:/Dev_Projects/AiWarmachine/images/MicroQR/MicroQrInt_s16_{number:05d}.png"
#         pbg.gateway.jvm.boofcv.io.image.UtilImageIO.saveImage(boof_gray_image, file_path)


def generate_micro_qr_int(size, value_min, value_max, file_path_template):
    """"""
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
    column_count, row_count,
    page_image_file_path,
    printable_page_image_file_path=None
):
    """"""
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

# img = pb.image.mmap_boof_to_numpy_U8(boof_gray_image)

# print(f"{boof_gray_image.width}x{boof_gray_image.height}")
# print(boof_gray_image.stride)

# cv2.imwrite("C:/tmp/boof_microqr2.png", img=img)
# pb.swing.show(boof_gray_image, "Toto")

# img = pb.boof_to_ndarray(boof_gray_image)
# print(img)
# input("Press any key to exit")
# pb.convert_boof_image(boof_gray_image, )
# binary = pb.create_single_band(,original.getHeight(),np.uint8)


def detect(dir_path):
    for file_name in sorted(os.listdir(dir_path)):
        file_path = os.path.join(dir_path, file_name)
        detector = pb.FactoryFiducial(np.uint8).microqr()
        image = pb.load_single_band(file_path, np.uint8)
        detector.detect(image)
        print(f"{file_name} has detected {len(detector.detections)} Micro QR Codes:")
        print("    {}\n".format(", ".join(sorted([qr.message for qr in detector.detections]))))

        # for qr in detector.detections:
        #     print("  Message: " + qr.message)
        #     print("     at: " + str(qr.bounds))


def generate_micro_qr_int_page(column_count, row_count, value_min, size):
    """"""
    value_max = value_min + column_count * row_count - 1
    micro_qr_image_file_paths_list = generate_micro_qr_int(
        size=size,
        value_min=value_min,
        value_max=value_max,
        file_path_template=MICRO_QR_INT_FILE_PATH_TEMPLATE
    )
    return compose_micro_qr_int_page(
        template_page_image_file_path=MICRO_QR_INT_SMALL_BASE_TEMPLATE_PAGE_FILE_PATH,
        qr_image_file_paths_list=micro_qr_image_file_paths_list,
        column_count=column_count,
        row_count=row_count,
        page_image_file_path=MICRO_QR_INT_PAGE_FILE_PATH_TEMPLATE.format(size=size, value_min=value_min, value_max=value_max),
        printable_page_image_file_path=LETTER_PAGE_300DPI_FILE_PATH
    )


if __name__ == "__main__":
    # generate_micro_qr_int_page(
    #     column_count=7,
    #     row_count=10,
    #     value_min=0,
    #     size=16
    # )

    detect(dir_path=r"D:\Dev_Projects\AiWarmachine\saved\snapshot\MicroQR_PhotoUHD")
