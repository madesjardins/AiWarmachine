#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023 Marc-Antoine Desjardins.
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
"""Model detection object."""

import os
import traceback

# TEMP Commented !!
# import tensorflow as tf
import numpy as np
from PyQt6 import QtGui, QtCore

# TEMP Commented !!
# from matplotlib import pyplot as plt

# TEMP Commented !!
# from object_detection.utils import label_map_util
# from object_detection.utils import config_util
# from object_detection.utils import visualization_utils as viz_utils
# from object_detection.builders import model_builder


def load_qimage_into_numpy_array(image):
    """"""
    # incomingImage = incomingImage.convertToFormat(QtGui.QImage.Format.Format_RGB888)  #(4)
    width = image.width()
    height = image.height()

    ptr = image.constBits()
    ptr.setsize(height * width * 3)
    arr = np.array(ptr).reshape(height, width, 3)  # Copies the data
    return arr

    # incomingImage = incomingImage.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)

    # width = incomingImage.width()
    # height = incomingImage.height()

    # ptr = incomingImage.bits()
    # ptr.setsize(height * width * 4)
    # arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
    # return arr


def intersection(rect1, rect2):
    """
    Calculates square of intersection of two rectangles
    rect: list with coords of top-right and left-boom corners [x1,y1,x2,y2]
    return: square of intersection
    """
    x_overlap = max(0, min(rect1[2], rect2[2]) - max(rect1[0], rect2[0]))
    y_overlap = max(0, min(rect1[3], rect2[3]) - max(rect1[1], rect2[1]))
    overlapArea = x_overlap * y_overlap
    return overlapArea


def square(rect):
    """
    Calculates square of rectangle
    """
    return abs(rect[2] - rect[0]) * abs(rect[3] - rect[1])


def nms(rects, thd=0.5):
    """
    Filter rectangles
    rects is array of oblects ([x1,y1,x2,y2], confidence, class)
    thd - intersection threshold (intersection divides min square of rectange)
    """
    out = []

    remove = [False] * len(rects)

    for i in range(0, len(rects) - 1):
        if remove[i]:
            continue
        inter = [0.0] * len(rects)
        for j in range(i, len(rects)):
            if remove[j]:
                continue
            inter[j] = intersection(rects[i][0], rects[j][0]) / min(square(rects[i][0]), square(rects[j][0]))

        max_prob = 0.0
        max_idx = 0
        for k in range(i, len(rects)):
            if inter[k] >= thd:
                if rects[k][1] > max_prob:
                    max_prob = rects[k][1]
                    max_idx = k

        for k in range(i, len(rects)):
            if (inter[k] >= thd) & (k != max_idx):
                remove[k] = True

    for k in range(0, len(rects)):
        if not remove[k]:
            out.append(rects[k])

    boxes = [box[0] for box in out]
    scores = [score[1] for score in out]
    classes = [cls[2] for cls in out]
    return boxes, scores, classes


class ModelDetector(QtCore.QThread):
    """Model detector class to detect models in image."""

    def __init__(
        self,
        trained_model_path,
        label_map_path,
    ):
        """Initializer."""
        super().__init__()
        self._trained_model_path = trained_model_path.replace("\\", "/")
        self._trained_model_config_path = self._trained_model_path + '/pipeline.config'

        configs = config_util.get_configs_from_pipeline_file(self._trained_model_config_path)  # importing config
        model_config = configs['model']  # recreating model config
        self._detection_model = model_builder.build(model_config=model_config, is_training=False)  # importing model

        ckpt = tf.compat.v2.train.Checkpoint(model=self._detection_model)
        ckpt.restore(os.path.join(self._trained_model_path, 'checkpoint', 'ckpt-0')).expect_partial()

        self._label_map_path = label_map_path.replace("\\", "/")
        self._category_index = label_map_util.create_category_index_from_labelmap(self._label_map_path, use_display_name=True)

        self._image_np = False
        self._running = False
        self._overlay_image = None
        self._image_offset_x = 0
        self._image_offset_y = 0
        self._image_width = 0
        self._image_height = 0

    def is_using_gpu(self):
        """Whether or not tensorflow will use the GPU.

        :return: Whether or not tensorflow will use the GPU.
        :rtype: bool
        """
        return tf.test.gpu_device_name()

    def detect(
        self,
        image_np,
        box_th=0.25,
        nms_th=0.5,
    ):
        """Function that performs inference and return filtered predictions.

        Args:
        box_th: (float) value that defines threshold for model prediction. Consider 0.25 as a value.
        nms_th: (float) value that defines threshold for non-maximum suppression. Consider 0.5 as a value.
        path2image + (x1abs, y1abs, x2abs, y2abs, score, conf) for box in boxes

        Returs:
        detections (dict): filtered predictions that model made
        """
        # convert qimage to numpy
        # image_np = load_qimage_into_numpy_array(image)
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        input_image, shapes = self._detection_model.preprocess(input_tensor)
        prediction_dict = self._detection_model.predict(input_image, shapes)
        detections = self._detection_model.postprocess(prediction_dict, shapes)
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy() for key, value in detections.items()}

        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        label_id_offset = 1

        # defining what we need from the resulting detection dict that we got from model output
        key_of_interest = ['detection_classes', 'detection_boxes', 'detection_scores']

        # filtering out detection dict in order to get only boxes, classes and scores
        detections = {key: value for key, value in detections.items() if key in key_of_interest}

        if box_th:  # filtering detection if a confidence threshold for boxes was given as a parameter
            for key in key_of_interest:
                scores = detections['detection_scores']
                current_array = detections[key]
                filtered_current_array = current_array[scores > box_th]
                detections[key] = filtered_current_array

        if nms_th:  # filtering rectangles if nms threshold was passed in as a parameter
            # creating a zip object that will contain model output info as
            output_info = list(
                zip(
                    detections['detection_boxes'],
                    detections['detection_scores'],
                    detections['detection_classes']
                )
            )
            boxes, scores, classes = nms(output_info)

            detections['detection_boxes'] = boxes  # format: [y1, x1, y2, x2]
            detections['detection_scores'] = scores
            detections['detection_classes'] = classes

        image_h, image_w, _ = image_np.shape

        # iterating over boxes
        model_boxes_list = []
        for b, s, c in zip(boxes, scores, classes):

            y1abs, x1abs = b[0] * image_h, b[1] * image_w
            y2abs, x2abs = b[2] * image_h, b[3] * image_w

            model_boxes_list.append([x1abs, y1abs, x2abs, y2abs, s, c])

        return model_boxes_list

    def set_image(self, image_np, min_x, min_y, max_x, max_y):
        """"""
        self._image_offset_x = min_x
        self._image_offset_y = min_y
        self._image_width = image_np.shape[1]
        self._image_height = image_np.shape[0]
        self._image_np = image_np[min_y:max_y, min_x:max_x]

    def _get_empty_overlay(self, width, height):
        """"""
        image_size = QtCore.QSize(width, height)
        image_overlay = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        # painter = QtGui.QPainter(image_overlay)
        # painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        # painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
        # painter.fillRect(image_overlay.rect(), QtCore.Qt.GlobalColor.transparent)
        # painter.end()
        return image_overlay

    def get_image_overlay(self):
        """"""
        return self._overlay_image

    def stop(self):
        """"""
        self._running = False

    def run(self):
        """"""
        self._running = True
        while self._running:
            if self._image_np is not None:
                overlay_offset_x = self._image_offset_x
                overlay_offset_y = self._image_offset_y
                overlay_width = self._image_width
                overlay_height = self._image_height
                overlay_image = self._get_empty_overlay(overlay_width, overlay_height)
                try:

                    detected_models_list = self.detect(np.copy(self._image_np))
                    if detected_models_list:
                        painter = QtGui.QPainter(overlay_image)
                        detect_brush = QtGui.QBrush()
                        painter.setBrush(detect_brush)
                        detect_pen = QtGui.QPen(QtCore.Qt.GlobalColor.red, 4, QtCore.Qt.PenStyle.SolidLine)
                        painter.setPen(detect_pen)
                        for x1abs, y1abs, x2abs, y2abs, _, _ in detected_models_list:
                            painter.drawRect(
                                overlay_offset_x + int(min(x1abs, x2abs)),
                                overlay_offset_y + int(min(y1abs, y2abs)),
                                int(abs(x2abs - x1abs)),
                                int(abs(y2abs - y1abs))
                            )
                        painter.end()
                except Exception:
                    traceback.print_exc()
                    self._running = False
                finally:
                    self._overlay_image = overlay_image
