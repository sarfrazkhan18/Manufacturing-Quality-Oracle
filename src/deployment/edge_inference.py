"""
Edge Inference Script for Jetson and Intel NUC devices
Optimized for edge deployment with minimal dependencies
"""

import argparse
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from src.vision import DefectDetector, CameraInterface, ImageProcessor
from src.config import settings, LOG_DIR


class EdgeInference:
    """
    Edge inference engine optimized for edge devices
    """

    def __init__(self, device_type: str = "generic"):
        """
        Initialize edge inference

        Args:
            device_type: Device type ('jetson', 'intel_nuc', 'generic')
        """
        self.device_type = device_type

        # Setup logging
        log_file = LOG_DIR / f"edge_inference_{device_type}.log"
        logger.add(log_file, rotation="100 MB", retention="7 days")

        logger.info(f"Edge Inference Engine starting on {device_type}")

        # Initialize detector with device-specific settings
        if device_type == "jetson":
            # Use TensorRT optimization for Jetson
            self.detector = DefectDetector(device="cuda")
        elif device_type == "intel_nuc":
            # Use OpenVINO for Intel NUC
            self.detector = DefectDetector(device="cpu")
        else:
            # Generic
            self.detector = DefectDetector(device="auto")

        # Initialize camera
        self.camera = CameraInterface(camera_id=0)

        # Image processor
        self.processor = ImageProcessor()

        # Statistics
        self.total_inspections = 0
        self.total_defects = 0
        self.start_time = time.time()

    def run(self):
        """Run inference loop"""
        logger.info("Starting camera...")
        if not self.camera.start():
            logger.error("Failed to start camera")
            return

        logger.info("Inference loop started")

        try:
            while True:
                # Get frame
                frame = self.camera.get_latest_frame()

                if frame is None:
                    logger.warning("No frame available")
                    time.sleep(0.1)
                    continue

                # Preprocess
                processed_frame = self.processor.preprocess_for_detection(
                    frame,
                    normalize_lighting=True,
                    reduce_noise=True
                )

                # Detect defects
                detections = self.detector.detect(processed_frame)

                # Update statistics
                self.total_inspections += 1
                if detections:
                    self.total_defects += len(detections)

                    logger.info(
                        f"Inspection #{self.total_inspections}: "
                        f"Found {len(detections)} defects"
                    )

                    for detection in detections:
                        logger.warning(
                            f"  - {detection.defect_type}: "
                            f"{detection.confidence:.2f} "
                            f"({detection.severity})"
                        )

                # Log statistics periodically
                if self.total_inspections % 100 == 0:
                    self.print_statistics()

                # Small delay
                time.sleep(0.05)

        except KeyboardInterrupt:
            logger.info("Stopping inference...")
        finally:
            self.cleanup()

    def print_statistics(self):
        """Print inference statistics"""
        elapsed = time.time() - self.start_time
        fps = self.total_inspections / elapsed if elapsed > 0 else 0
        defect_rate = (self.total_defects / self.total_inspections * 100
                      if self.total_inspections > 0 else 0)

        logger.info("=" * 60)
        logger.info("STATISTICS:")
        logger.info(f"  Total Inspections: {self.total_inspections}")
        logger.info(f"  Total Defects: {self.total_defects}")
        logger.info(f"  Defect Rate: {defect_rate:.2f}%")
        logger.info(f"  FPS: {fps:.2f}")
        logger.info(f"  Avg Inference Time: {self.detector.get_average_inference_time()*1000:.2f}ms")
        logger.info("=" * 60)

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        self.camera.stop()
        self.print_statistics()
        logger.info("Shutdown complete")


def main():
    parser = argparse.ArgumentParser(description="Edge Inference Engine")
    parser.add_argument(
        "--device",
        type=str,
        default="generic",
        choices=["jetson", "intel_nuc", "generic"],
        help="Device type"
    )

    args = parser.parse_args()

    # Run inference
    engine = EdgeInference(device_type=args.device)
    engine.run()


if __name__ == "__main__":
    main()
