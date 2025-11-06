"""
Computer Vision Agent for Defect Detection using YOLOv8/v9
"""

import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import cv2
from ultralytics import YOLO
from loguru import logger

from ..config import settings


class DefectType:
    """Defect type classifications"""
    SCRATCH = "scratch"
    DENT = "dent"
    COLOR_DEFECT = "color_defect"
    DIMENSIONAL = "dimensional"
    ASSEMBLY_ERROR = "assembly_error"
    CONTAMINATION = "contamination"
    SURFACE_DEFECT = "surface_defect"
    UNKNOWN = "unknown"


class DetectionResult:
    """Detection result container"""

    def __init__(
        self,
        defect_type: str,
        confidence: float,
        bbox: Tuple[int, int, int, int],
        severity: str = "medium",
        image_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.defect_type = defect_type
        self.confidence = confidence
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.severity = severity
        self.image_path = image_path
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.detection_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique detection ID"""
        return f"DET-{int(self.timestamp * 1000)}"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "detection_id": self.detection_id,
            "defect_type": self.defect_type,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "severity": self.severity,
            "image_path": self.image_path,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class DefectDetector:
    """
    YOLOv8/v9-based defect detection agent with self-correction capabilities
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: str = "auto"
    ):
        """
        Initialize the defect detector

        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on ('cpu', 'cuda', 'auto')
        """
        self.model_path = model_path or settings.model.yolo_model_path
        self.confidence_threshold = confidence_threshold or settings.model.confidence_threshold
        self.iou_threshold = iou_threshold or settings.model.iou_threshold
        self.device = self._determine_device(device)

        # Load YOLO model
        logger.info(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(str(self.model_path))

        # Performance metrics
        self.inference_times = []
        self.detection_count = 0
        self.false_positive_count = 0

        logger.info(f"DefectDetector initialized on device: {self.device}")

    def _determine_device(self, device: str) -> str:
        """Determine the best device for inference"""
        if device == "auto":
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def detect(
        self,
        image: np.ndarray,
        visualize: bool = False,
        save_path: Optional[Path] = None
    ) -> List[DetectionResult]:
        """
        Detect defects in an image

        Args:
            image: Input image as numpy array (BGR format)
            visualize: Whether to draw bounding boxes
            save_path: Optional path to save visualized image

        Returns:
            List of DetectionResult objects
        """
        start_time = time.time()

        # Run YOLO inference
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )

        # Parse results
        detections = []

        for result in results:
            boxes = result.boxes

            for box in boxes:
                # Extract box information
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                # Map class ID to defect type
                defect_type = self._map_class_to_defect(class_id, result.names)

                # Determine severity based on confidence and size
                severity = self._determine_severity(confidence, (x2 - x1) * (y2 - y1), image.shape)

                detection = DetectionResult(
                    defect_type=defect_type,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    severity=severity,
                    metadata={
                        "class_id": class_id,
                        "class_name": result.names.get(class_id, "unknown")
                    }
                )

                detections.append(detection)
                self.detection_count += 1

        # Record inference time
        inference_time = time.time() - start_time
        self.inference_times.append(inference_time)

        logger.info(
            f"Detected {len(detections)} defects in {inference_time*1000:.2f}ms "
            f"(avg: {self.get_average_inference_time()*1000:.2f}ms)"
        )

        # Visualize if requested
        if visualize and len(detections) > 0:
            visualized_image = self.visualize_detections(image, detections)

            if save_path:
                cv2.imwrite(str(save_path), visualized_image)
                logger.info(f"Saved visualized image to {save_path}")

        return detections

    def detect_batch(
        self,
        images: List[np.ndarray],
        batch_size: int = 8
    ) -> List[List[DetectionResult]]:
        """
        Detect defects in a batch of images

        Args:
            images: List of images as numpy arrays
            batch_size: Batch size for inference

        Returns:
            List of lists of DetectionResult objects
        """
        all_detections = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]

            # Run batch inference
            results = self.model.predict(
                batch,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False
            )

            # Parse results for each image in batch
            for result in results:
                detections = []
                boxes = result.boxes

                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])

                    defect_type = self._map_class_to_defect(class_id, result.names)

                    detection = DetectionResult(
                        defect_type=defect_type,
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                        metadata={"class_id": class_id}
                    )

                    detections.append(detection)

                all_detections.append(detections)

        logger.info(f"Processed batch of {len(images)} images")
        return all_detections

    def _map_class_to_defect(self, class_id: int, names: Dict) -> str:
        """Map YOLO class ID to defect type"""
        class_name = names.get(class_id, "unknown").lower()

        # Map common defect names
        defect_mapping = {
            "scratch": DefectType.SCRATCH,
            "dent": DefectType.DENT,
            "color": DefectType.COLOR_DEFECT,
            "dimensional": DefectType.DIMENSIONAL,
            "assembly": DefectType.ASSEMBLY_ERROR,
            "contamination": DefectType.CONTAMINATION,
            "surface": DefectType.SURFACE_DEFECT
        }

        for key, value in defect_mapping.items():
            if key in class_name:
                return value

        return DefectType.UNKNOWN

    def _determine_severity(
        self,
        confidence: float,
        defect_area: int,
        image_shape: Tuple
    ) -> str:
        """
        Determine defect severity based on confidence and size

        Args:
            confidence: Detection confidence
            defect_area: Area of defect bounding box
            image_shape: Shape of input image

        Returns:
            Severity level: 'critical', 'high', 'medium', 'low'
        """
        image_area = image_shape[0] * image_shape[1]
        area_ratio = defect_area / image_area

        # Critical: High confidence and large area
        if confidence > 0.9 and area_ratio > 0.05:
            return "critical"

        # High: High confidence or large area
        if confidence > 0.8 or area_ratio > 0.03:
            return "high"

        # Medium: Moderate confidence and area
        if confidence > 0.6 and area_ratio > 0.01:
            return "medium"

        # Low: Lower confidence or small area
        return "low"

    def visualize_detections(
        self,
        image: np.ndarray,
        detections: List[DetectionResult]
    ) -> np.ndarray:
        """
        Visualize detections on image

        Args:
            image: Input image
            detections: List of detections

        Returns:
            Image with bounding boxes and labels
        """
        vis_image = image.copy()

        # Color map for severity levels
        severity_colors = {
            "critical": (0, 0, 255),    # Red
            "high": (0, 165, 255),      # Orange
            "medium": (0, 255, 255),    # Yellow
            "low": (0, 255, 0)          # Green
        }

        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            color = severity_colors.get(detection.severity, (255, 255, 255))

            # Draw bounding box
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = f"{detection.defect_type}: {detection.confidence:.2f} ({detection.severity})"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)

            # Background for text
            cv2.rectangle(
                vis_image,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )

            # Text
            cv2.putText(
                vis_image,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

        return vis_image

    def get_average_inference_time(self) -> float:
        """Get average inference time"""
        if not self.inference_times:
            return 0.0
        return sum(self.inference_times) / len(self.inference_times)

    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            "total_detections": self.detection_count,
            "average_inference_time_ms": self.get_average_inference_time() * 1000,
            "false_positives": self.false_positive_count,
            "model_path": str(self.model_path),
            "confidence_threshold": self.confidence_threshold,
            "device": self.device
        }

    def update_thresholds(
        self,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ):
        """Update detection thresholds"""
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
            logger.info(f"Updated confidence threshold to {confidence_threshold}")

        if iou_threshold is not None:
            self.iou_threshold = iou_threshold
            logger.info(f"Updated IoU threshold to {iou_threshold}")

    def reset_metrics(self):
        """Reset performance metrics"""
        self.inference_times = []
        self.detection_count = 0
        self.false_positive_count = 0
        logger.info("Reset performance metrics")
