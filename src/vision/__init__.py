"""
Computer Vision module for defect detection
"""

from .defect_detector import DefectDetector
from .camera_interface import CameraInterface
from .image_processor import ImageProcessor

__all__ = ["DefectDetector", "CameraInterface", "ImageProcessor"]
